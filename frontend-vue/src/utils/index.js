/**
 * 工具函数索引文件
 * 统一导出所有工具函数，方便在组件中引用
 */

// 导出辅助函数
export * from './helpers'

// 导出WebSocket管理器
export { default as wsManager } from './websocket'

// 默认导出所有工具
export default {
  ...require('./helpers'),
  wsManager: require('./websocket').default
} 