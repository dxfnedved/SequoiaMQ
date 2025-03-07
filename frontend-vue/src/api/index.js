/**
 * API索引文件
 * 统一导出所有API，方便在组件中引�?
 */

// 导出请求工具
export * from './request.simple'

// 导出股票相关API
export * as stockApi from './stock'

// 导出自选股相关API
export * as watchlistApi from './watchlist'

// 导出分析相关API
export * as analysisApi from './analysis'

// 导出预测相关API
export * as predictionApi from './prediction'

// 导出系统相关API
export * as systemApi from './system'

// 导出用户相关API
export * as usersApi from './users'

// 默认导出所有API
export default {
  stock: require('./stock'),
  watchlist: require('./watchlist'),
  analysis: require('./analysis'),
  prediction: require('./prediction'),
  system: require('./system'),
  users: require('./users')
} 
