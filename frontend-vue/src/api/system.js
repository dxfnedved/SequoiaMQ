/**
 * 系统API
 * 封装系统设置相关的API请求
 */
import { request } from '../utils/request'

/**
 * 获取系统信息
 * @returns {Promise}
 */
export function getSystemInfo() {
  return request({
    url: '/system/info',
    method: 'get'
  })
}

/**
 * 获取系统日志
 * @param {Object} params - 查询参数
 * @param {String} params.level - 日志级别（可选）
 * @param {Number} params.lines - 返回行数（可选）
 * @returns {Promise}
 */
export function getSystemLogs(params = {}) {
  return request({
    url: '/system/logs',
    method: 'get',
    params
  })
}

/**
 * 清除缓存
 * @param {String} type - 缓存类型（stock/analysis/all）
 * @returns {Promise}
 */
export function clearCache(type = 'all') {
  return request({
    url: `/system/cache?type=${type}`,
    method: 'delete'
  })
}

/**
 * 获取系统设置
 * @returns {Promise}
 */
export function getSettings() {
  return request({
    url: '/system/settings',
    method: 'get'
  })
}

/**
 * 更新系统设置
 * @param {Object} settings - 设置对象
 * @returns {Promise}
 */
export function updateSettings(settings) {
  return request({
    url: '/system/settings',
    method: 'post',
    data: settings
  })
}

/**
 * 检查系统状态
 * @returns {Promise}
 */
export function checkSystemStatus() {
  return request({
    url: '/system/status',
    method: 'get'
  })
}

/**
 * 获取WebSocket连接URL
 * @returns {String} WebSocket连接URL
 */
export function getWebSocketUrl() {
  // 根据当前环境获取WebSocket URL
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = import.meta.env.VITE_API_BASE_URL || window.location.host
  return `${protocol}//${host}/ws`
}

/**
 * 系统设置和状态相关的API
 */
export const systemApi = {
  /**
   * 获取系统状态
   * @returns {Promise<Object>} 系统状态信息
   */
  getSystemStatus() {
    return request({
      url: '/api/system/status',
      method: 'get'
    })
  },

  /**
   * 获取系统设置
   * @returns {Promise<Object>} 系统设置信息
   */
  getSettings() {
    return request({
      url: '/api/system/settings',
      method: 'get'
    })
  },

  /**
   * 更新系统设置
   * @param {Object} settings 系统设置
   * @returns {Promise<Object>} 更新结果
   */
  updateSettings(settings) {
    return request({
      url: '/api/system/settings',
      method: 'post',
      data: settings
    })
  },

  /**
   * 获取服务器日志
   * @param {Object} params 查询参数
   * @returns {Promise<Object>} 日志信息
   */
  getLogs(params) {
    return request({
      url: '/api/system/logs',
      method: 'get',
      params
    })
  },

  /**
   * 获取系统性能指标
   * @returns {Promise<Object>} 性能指标
   */
  getPerformanceMetrics() {
    return request({
      url: '/api/system/performance',
      method: 'get'
    })
  },

  /**
   * 检查系统更新
   * @returns {Promise<Object>} 更新信息
   */
  checkForUpdates() {
    return request({
      url: '/api/system/check-updates',
      method: 'get'
    })
  },

  /**
   * 重启服务器
   * @returns {Promise<Object>} 重启结果
   */
  restartServer() {
    return request({
      url: '/api/system/restart',
      method: 'post'
    })
  }
} 