/**
 * Axios请求封装
 * 集中处理HTTP请求配置、拦截器和错误处理
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const service = axios.create({
  // 基础URL，会自动添加到请求URL前面
  baseURL: '/api',
  // 请求超时时间
  timeout: 30000
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    // 在请求发送前可以做一些操作
    // 例如添加token到请求头
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers['Authorization'] = `Bearer ${token}`
    // }
    
    return config
  },
  error => {
    // 请求错误处理
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    // 获取响应数据
    const res = response.data
    
    // 根据后端的状态码判断响应状态
    // 这里假设后端返回的格式是 { code: number, data: any, message: string }
    if (res.code === 200 || res.code === undefined) {
      return res
    }
    
    // 处理错误响应
    ElMessage({
      message: res.message || '请求失败',
      type: 'error',
      duration: 5 * 1000
    })
    
    // 处理特定错误码
    if (res.code === 401) {
      // 未授权，可以在这里处理登出逻辑
      // logout()
    }
    
    return Promise.reject(new Error(res.message || '请求失败'))
  },
  error => {
    console.error('响应错误:', error)
    
    // 错误消息处理
    const message = error.response?.data?.message || error.message || '网络错误'
    
    ElMessage({
      message,
      type: 'error',
      duration: 5 * 1000
    })
    
    return Promise.reject(error)
  }
)

/**
 * GET请求
 * @param {string} url - 请求地址
 * @param {object} params - 请求参数
 * @param {object} config - 其他配置
 * @returns {Promise}
 */
export function get(url, params = {}, config = {}) {
  return service({
    url,
    method: 'get',
    params,
    ...config
  })
}

/**
 * POST请求
 * @param {string} url - 请求地址
 * @param {object} data - 请求数据
 * @param {object} config - 其他配置
 * @returns {Promise}
 */
export function post(url, data = {}, config = {}) {
  return service({
    url,
    method: 'post',
    data,
    ...config
  })
}

/**
 * PUT请求
 * @param {string} url - 请求地址
 * @param {object} data - 请求数据
 * @param {object} config - 其他配置
 * @returns {Promise}
 */
export function put(url, data = {}, config = {}) {
  return service({
    url,
    method: 'put',
    data,
    ...config
  })
}

/**
 * DELETE请求
 * @param {string} url - 请求地址
 * @param {object} data - 请求数据
 * @param {object} config - 其他配置
 * @returns {Promise}
 */
export function del(url, data = {}, config = {}) {
  return service({
    url,
    method: 'delete',
    data,
    ...config
  })
}

/**
 * 文件上传请求
 * @param {string} url - 请求地址
 * @param {FormData} formData - 表单数据
 * @param {function} progressCallback - 进度回调函数
 * @returns {Promise}
 */
export function upload(url, formData, progressCallback) {
  return service({
    url,
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    onUploadProgress: progressEvent => {
      if (progressCallback) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        progressCallback(progress)
      }
    }
  })
}

export default service 