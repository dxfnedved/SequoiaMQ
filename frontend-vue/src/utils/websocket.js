/**
 * WebSocket连接管理
 * 用于处理与后端的WebSocket通信
 */
import { getWebSocketUrl } from '../api/system'

class WebSocketManager {
  constructor() {
    this.socket = null
    this.isConnected = false
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectInterval = 3000
    this.listeners = {
      message: [],
      open: [],
      close: [],
      error: [],
      reconnect: []
    }
    this.topicSubscriptions = {}
  }

  /**
   * 连接WebSocket
   * @returns {Promise} 连接成功或失败的Promise
   */
  connect() {
    return new Promise((resolve, reject) => {
      if (this.isConnected) {
        resolve()
        return
      }

      try {
        const wsUrl = getWebSocketUrl()
        this.socket = new WebSocket(wsUrl)

        this.socket.onopen = (event) => {
          console.log('WebSocket连接已建立')
          this.isConnected = true
          this.reconnectAttempts = 0
          this._notifyListeners('open', event)
          
          // 重新订阅之前的主题
          Object.keys(this.topicSubscriptions).forEach(topic => {
            this.subscribe(topic)
          })
          
          resolve(event)
        }

        this.socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            
            // 如果消息包含主题，通知该主题的订阅者
            if (data.topic && this.topicSubscriptions[data.topic]) {
              this.topicSubscriptions[data.topic].forEach(callback => {
                callback(data.data)
              })
            }
            
            this._notifyListeners('message', data)
          } catch (error) {
            console.error('解析WebSocket消息失败:', error)
          }
        }

        this.socket.onclose = (event) => {
          this.isConnected = false
          console.log('WebSocket连接已关闭', event.code, event.reason)
          this._notifyListeners('close', event)
          
          if (!event.wasClean) {
            this._attemptReconnect()
          }
        }

        this.socket.onerror = (error) => {
          console.error('WebSocket错误:', error)
          this._notifyListeners('error', error)
          reject(error)
        }
      } catch (error) {
        console.error('创建WebSocket连接失败:', error)
        reject(error)
      }
    })
  }

  /**
   * 尝试重新连接
   * @private
   */
  _attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('达到最大重连次数，停止重连')
      return
    }

    this.reconnectAttempts++
    console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
    
    setTimeout(() => {
      this._notifyListeners('reconnect', this.reconnectAttempts)
      this.connect()
        .then(() => {
          console.log('重连成功')
        })
        .catch(error => {
          console.error('重连失败:', error)
        })
    }, this.reconnectInterval)
  }

  /**
   * 关闭WebSocket连接
   */
  disconnect() {
    if (this.socket && this.isConnected) {
      this.socket.close(1000, '客户端主动关闭')
      this.isConnected = false
    }
  }

  /**
   * 发送消息到服务器
   * @param {Object|String} data - 要发送的数据
   * @returns {Boolean} 是否发送成功
   */
  send(data) {
    if (!this.isConnected) {
      console.error('WebSocket未连接，无法发送消息')
      return false
    }

    try {
      const message = typeof data === 'string' ? data : JSON.stringify(data)
      this.socket.send(message)
      return true
    } catch (error) {
      console.error('发送WebSocket消息失败:', error)
      return false
    }
  }

  /**
   * 订阅主题
   * @param {String} topic - 主题名称
   * @param {Function} callback - 接收消息的回调函数
   */
  subscribe(topic, callback) {
    // 初始化主题的订阅者数组
    if (!this.topicSubscriptions[topic]) {
      this.topicSubscriptions[topic] = []
      
      // 如果已连接，发送订阅消息到服务器
      if (this.isConnected) {
        this.send({
          action: 'subscribe',
          topic: topic
        })
      }
    }
    
    // 如果提供了回调函数，添加到订阅者列表
    if (callback) {
      this.topicSubscriptions[topic].push(callback)
    }
  }

  /**
   * 取消订阅主题
   * @param {String} topic - 主题名称
   * @param {Function} callback - 要移除的回调函数，如果不提供则移除所有回调
   */
  unsubscribe(topic, callback) {
    if (!this.topicSubscriptions[topic]) {
      return
    }
    
    if (callback) {
      // 移除特定回调
      const index = this.topicSubscriptions[topic].indexOf(callback)
      if (index !== -1) {
        this.topicSubscriptions[topic].splice(index, 1)
      }
    } else {
      // 移除所有回调
      delete this.topicSubscriptions[topic]
    }
    
    // 如果没有回调了，发送取消订阅消息到服务器
    if (!this.topicSubscriptions[topic] || this.topicSubscriptions[topic].length === 0) {
      if (this.isConnected) {
        this.send({
          action: 'unsubscribe',
          topic: topic
        })
      }
      
      delete this.topicSubscriptions[topic]
    }
  }

  /**
   * 添加事件监听器
   * @param {String} event - 事件类型 (message, open, close, error, reconnect)
   * @param {Function} callback - 回调函数
   */
  addEventListener(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event].push(callback)
    }
  }

  /**
   * 移除事件监听器
   * @param {String} event - 事件类型
   * @param {Function} callback - 要移除的回调函数
   */
  removeEventListener(event, callback) {
    if (this.listeners[event]) {
      const index = this.listeners[event].indexOf(callback)
      if (index !== -1) {
        this.listeners[event].splice(index, 1)
      }
    }
  }

  /**
   * 通知所有监听器
   * @param {String} event - 事件类型
   * @param {*} data - 事件数据
   * @private
   */
  _notifyListeners(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => {
        try {
          callback(data)
        } catch (error) {
          console.error(`执行${event}事件监听器时出错:`, error)
        }
      })
    }
  }
}

// 创建单例实例
const wsManager = new WebSocketManager()

export default wsManager 