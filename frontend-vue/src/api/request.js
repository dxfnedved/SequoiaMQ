/**
 * 封装Axios请求
 * 
 * 主要功能：
 * 1. HTTP请求配置
 * 2. 请求/响应拦截器
 * 3. 错误处理
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

// 错误消息映射
const ERROR_MESSAGES = {
  400: '请求参数错误',
  401: '未授权，请重新登录',
  403: '拒绝访问',
  404: '请求地址不存在',
  408: '请求超时',
  500: '服务器内部错误',
  501: '服务未实现',
  502: '网关错误',
  503: '服务不可用',
  504: '网关超时',
  505: 'HTTP版本不受支持'
}

// 记录正在进行的请求数量
let pendingRequests = 0

// 创建axios实例
const service = axios.create({
  baseURL: process.env.VUE_APP_BASE_API || '',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    // 记录请求开始时间，用于计算请求耗时
    config.metadata = { startTime: new Date().getTime() }
    
    // 为每个请求生成唯一ID，方便追踪
    config.requestId = new Date().getTime() + Math.random().toString(36).substring(2, 15)
    console.log(`[API请求开始] ${config.method.toUpperCase()} ${config.url} - 请求ID: ${config.requestId}`)
    
    pendingRequests++
    
    // 添加授权信息
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    return config
  },
  error => {
    pendingRequests--
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    pendingRequests--
    
    // 计算请求耗时
    const endTime = new Date().getTime()
    const startTime = response.config.metadata.startTime
    const duration = endTime - startTime
    
    // 记录耗时过长的请求
    if (duration > 500) {
      console.warn(`[API耗时过长] ${response.config.method.toUpperCase()} ${response.config.url} - 耗时: ${duration}ms`)
    }
    
    console.log(`[API请求完成] ${response.config.method.toUpperCase()} ${response.config.url} - 状态: ${response.status} - 耗时: ${duration}ms`)
    
    // 直接返回响应数据，不再嵌套在data字段中
    return response.data
  },
  error => {
    pendingRequests--
    
    // 处理请求取消的情况
    if (axios.isCancel(error)) {
      console.info('请求已取消:', error.message)
      return Promise.reject(new Error('请求已取消'))
    }
    
    // 提取错误信息
    const { response, config } = error
    let errorMessage = '网络连接失败'
    let statusCode = 0
    
    if (response) {
      statusCode = response.status
      
      // 使用服务器返回的错误信息或默认错误信息
      errorMessage = response.data?.message || response.data?.error || ERROR_MESSAGES[statusCode] || '请求失败'
      
      // 记录服务器错误
      console.error(`[API错误] ${config.method.toUpperCase()} ${config.url} - 状态: ${statusCode} - 错误: ${errorMessage}`)
    } else if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      // 处理超时错误
      errorMessage = '请求超时，请稍后重试'
      console.error(`[API超时] ${config.method.toUpperCase()} ${config.url}`)
      
      // 对于超时请求可以考虑重试
      if (config && !config._retryCount) {
        config._retryCount = 1
        console.log(`[API重试] 第1次重试 ${config.method.toUpperCase()} ${config.url}`)
        return service(config)
      }
    } else {
      // 其他网络错误
      console.error(`[API网络错误] ${error.message}`)
    }
    
    // 显示错误消息
    ElMessage.error(errorMessage)
    
    return Promise.reject(error)
  }
)

/**
 * GET请求
 * @param {string} url - 请求URL
 * @param {Object} options - 请求配置
 * @returns {Promise}
 */
function get(url, options = {}) {
  return service({
    url,
    method: 'get',
    ...options
  })
}

/**
 * POST请求
 * @param {string} url - 请求URL
 * @param {Object} data - 请求数据
 * @param {Object} options - 请求配置
 * @returns {Promise}
 */
function post(url, data = {}, options = {}) {
  return service({
    url,
    method: 'post',
    data,
    ...options
  })
}

/**
 * PUT请求
 * @param {string} url - 请求URL
 * @param {Object} data - 请求数据
 * @param {Object} options - 请求配置
 * @returns {Promise}
 */
function put(url, data = {}, options = {}) {
  return service({
    url,
    method: 'put',
    data,
    ...options
  })
}

/**
 * DELETE请求
 * @param {string} url - 请求URL
 * @param {Object} options - 请求配置
 * @returns {Promise}
 */
function del(url, options = {}) {
  return service({
    url,
    method: 'delete',
    ...options
  })
}

/**
 * 上传文件
 * @param {string} url - 请求URL
 * @param {FormData} formData - 表单数据
 * @param {Object} options - 请求配置
 * @returns {Promise}
 */
function upload(url, formData, options = {}) {
  return service({
    url,
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    ...options
  })
}

export default {
  get,
  post,
  put,
  delete: del,
  upload,
  service
} 