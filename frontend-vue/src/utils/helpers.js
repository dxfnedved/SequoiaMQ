/**
 * 辅助函数模块
 * 提供常用的工具函数
 */

/**
 * 格式化日期时间
 * @param {Date|String|Number} date - 日期对象、字符串或时间戳
 * @param {String} format - 格式化模板，默认为 'YYYY-MM-DD HH:mm:ss'
 * @returns {String} 格式化后的日期字符串
 */
export function formatDateTime(date, format = 'YYYY-MM-DD HH:mm:ss') {
  if (!date) return ''
  
  const d = date instanceof Date ? date : new Date(date)
  if (isNaN(d.getTime())) return ''
  
  const padZero = (num) => String(num).padStart(2, '0')
  
  const replacements = {
    YYYY: d.getFullYear(),
    MM: padZero(d.getMonth() + 1),
    DD: padZero(d.getDate()),
    HH: padZero(d.getHours()),
    mm: padZero(d.getMinutes()),
    ss: padZero(d.getSeconds()),
    SSS: String(d.getMilliseconds()).padStart(3, '0')
  }
  
  return format.replace(/YYYY|MM|DD|HH|mm|ss|SSS/g, match => replacements[match])
}

/**
 * 格式化数字
 * @param {Number} num - 要格式化的数字
 * @param {Number} digits - 小数位数，默认为2
 * @param {Boolean} useGrouping - 是否使用千分位分隔符，默认为true
 * @returns {String} 格式化后的数字字符串
 */
export function formatNumber(num, digits = 2, useGrouping = true) {
  if (num === null || num === undefined || isNaN(num)) return '--'
  
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
    useGrouping: useGrouping
  }).format(num)
}

/**
 * 格式化百分比
 * @param {Number} num - 要格式化的数字
 * @param {Number} digits - 小数位数，默认为2
 * @returns {String} 格式化后的百分比字符串
 */
export function formatPercent(num, digits = 2) {
  if (num === null || num === undefined || isNaN(num)) return '--'
  
  return new Intl.NumberFormat('zh-CN', {
    style: 'percent',
    minimumFractionDigits: digits,
    maximumFractionDigits: digits
  }).format(num)
}

/**
 * 格式化金额
 * @param {Number} num - 要格式化的金额
 * @param {String} currency - 货币代码，默认为'CNY'
 * @param {Number} digits - 小数位数，默认为2
 * @returns {String} 格式化后的金额字符串
 */
export function formatCurrency(num, currency = 'CNY', digits = 2) {
  if (num === null || num === undefined || isNaN(num)) return '--'
  
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: digits,
    maximumFractionDigits: digits
  }).format(num)
}

/**
 * 深拷贝对象
 * @param {*} obj - 要拷贝的对象
 * @returns {*} 拷贝后的对象
 */
export function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') return obj
  
  try {
    return JSON.parse(JSON.stringify(obj))
  } catch (e) {
    console.error('深拷贝对象失败:', e)
    return obj
  }
}

/**
 * 防抖函数
 * @param {Function} fn - 要执行的函数
 * @param {Number} delay - 延迟时间（毫秒）
 * @returns {Function} 防抖后的函数
 */
export function debounce(fn, delay = 300) {
  let timer = null
  
  return function(...args) {
    if (timer) clearTimeout(timer)
    
    timer = setTimeout(() => {
      fn.apply(this, args)
      timer = null
    }, delay)
  }
}

/**
 * 节流函数
 * @param {Function} fn - 要执行的函数
 * @param {Number} interval - 间隔时间（毫秒）
 * @returns {Function} 节流后的函数
 */
export function throttle(fn, interval = 300) {
  let lastTime = 0
  
  return function(...args) {
    const now = Date.now()
    
    if (now - lastTime >= interval) {
      fn.apply(this, args)
      lastTime = now
    }
  }
}

/**
 * 获取股票代码对应的交易所
 * @param {String} code - 股票代码
 * @returns {String} 交易所代码 (SH/SZ/BJ)
 */
export function getStockExchange(code) {
  if (!code) return ''
  
  // 去除可能的前缀
  const cleanCode = code.replace(/^(SH|SZ|BJ)/, '')
  
  if (cleanCode.startsWith('6') || cleanCode.startsWith('9')) {
    return 'SH' // 上海证券交易所
  } else if (cleanCode.startsWith('0') || cleanCode.startsWith('3')) {
    return 'SZ' // 深圳证券交易所
  } else if (cleanCode.startsWith('4') || cleanCode.startsWith('8')) {
    return 'BJ' // 北京证券交易所
  }
  
  return ''
}

/**
 * 格式化股票代码（添加交易所前缀）
 * @param {String} code - 股票代码
 * @returns {String} 格式化后的股票代码
 */
export function formatStockCode(code) {
  if (!code) return ''
  
  // 如果已经有前缀，直接返回
  if (/^(SH|SZ|BJ)/.test(code)) return code
  
  const exchange = getStockExchange(code)
  return exchange ? `${exchange}${code}` : code
}

/**
 * 获取股票涨跌颜色类名
 * @param {Number} change - 涨跌幅
 * @returns {String} 颜色类名
 */
export function getChangeColorClass(change) {
  if (!change && change !== 0) return ''
  
  if (change > 0) return 'text-red-500'
  if (change < 0) return 'text-green-500'
  return 'text-gray-500'
}

/**
 * 生成唯一ID
 * @param {String} prefix - ID前缀
 * @returns {String} 唯一ID
 */
export function generateUniqueId(prefix = '') {
  return `${prefix}${Date.now().toString(36)}-${Math.random().toString(36).substr(2, 9)}`
}

/**
 * 获取文件大小的可读表示
 * @param {Number} bytes - 字节数
 * @param {Number} decimals - 小数位数
 * @returns {String} 格式化后的文件大小
 */
export function formatFileSize(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(decimals))} ${sizes[i]}`
}

/**
 * 获取相对时间描述
 * @param {Date|String|Number} date - 日期对象、字符串或时间戳
 * @returns {String} 相对时间描述
 */
export function getRelativeTime(date) {
  if (!date) return ''
  
  const d = date instanceof Date ? date : new Date(date)
  if (isNaN(d.getTime())) return ''
  
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  
  // 转换为秒
  const seconds = Math.floor(diff / 1000)
  
  // 小于1分钟
  if (seconds < 60) {
    return '刚刚'
  }
  
  // 小于1小时
  if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60)
    return `${minutes}分钟前`
  }
  
  // 小于1天
  if (seconds < 86400) {
    const hours = Math.floor(seconds / 3600)
    return `${hours}小时前`
  }
  
  // 小于30天
  if (seconds < 2592000) {
    const days = Math.floor(seconds / 86400)
    return `${days}天前`
  }
  
  // 小于1年
  if (seconds < 31536000) {
    const months = Math.floor(seconds / 2592000)
    return `${months}个月前`
  }
  
  // 大于1年
  const years = Math.floor(seconds / 31536000)
  return `${years}年前`
} 