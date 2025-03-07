/**
 * 分析API
 * 封装策略分析相关的API请求
 */
import { get, post, del } from './request'

/**
 * 获取分析结果
 * @returns {Promise}
 */
export function fetchAnalysisResults() {
  return get('/analysis/results')
}

/**
 * 开始分析任务
 * @param {Object} params - 分析参数
 * @param {Array} params.strategies - 要使用的策略列表
 * @param {Array} params.stockCodes - 要分析的股票代码列表（可选）
 * @returns {Promise}
 */
export function startAnalysis(params) {
  return post('/analysis/start', params)
}

/**
 * 获取分析任务状态
 * @param {String} taskId - 任务ID
 * @returns {Promise}
 */
export function getAnalysisTaskStatus(taskId) {
  return get(`/analysis/task/${taskId}`)
}

/**
 * 取消分析任务
 * @param {String} taskId - 任务ID
 * @returns {Promise}
 */
export function cancelAnalysisTask(taskId) {
  return del(`/analysis/task/${taskId}`)
}

/**
 * 获取所有分析任务
 * @returns {Promise}
 */
export function getAllAnalysisTasks() {
  return get('/analysis/tasks')
}

/**
 * 获取可用的分析策略
 * @returns {Promise}
 */
export function getAvailableStrategies() {
  return get('/analysis/strategies')
}

/**
 * 获取特定股票的分析结果
 * @param {String} code - 股票代码
 * @returns {Promise}
 */
export function getStockAnalysisResult(code) {
  return get(`/analysis/stock/${code}`)
}

/**
 * 获取策略分析参数
 * @returns {Promise}
 */
export function getStrategyParams() {
  return get('/strategies/params')
}

/**
 * 运行策略分析
 * @param {Object} data - 分析参数
 * @returns {Promise}
 */
export function runStrategyAnalysis(data) {
  return post('/strategies/analyze', data)
}

/**
 * 获取策略分析结果
 * @param {String} resultId - 结果ID
 * @returns {Promise}
 */
export function getStrategyAnalysisResult(resultId) {
  return get(`/strategies/result/${resultId}`)
}

/**
 * 获取策略分析历史记录
 * @param {Object} params - 查询参数 (可选)
 * @returns {Promise}
 */
export function getStrategyAnalysisHistory(params) {
  return get('/strategies/history', { params })
}

/**
 * 获取股票策略分析历史
 * @param {String} stockCode - 股票代码
 * @param {Object} params - 查询参数 (可选)
 * @returns {Promise}
 */
export function getStockAnalysisHistory(stockCode, params) {
  return get(`/stocks/${stockCode}/analysis/history`, { params })
}

/**
 * 获取所有分析策略
 * @returns {Promise}
 */
export function getAllStrategies() {
  return get('/strategies')
}

/**
 * 获取特定股票的分析结果
 * @param {String} stockCode - 股票代码
 * @param {Array} strategies - 策略ID数组
 * @returns {Promise}
 */
export function getStockStrategyResults(stockCode, strategies) {
  return post(`/stocks/${stockCode}/strategies`, { strategies })
}

/**
 * 批量分析股票
 * @param {Object} data - 分析参数
 * @param {Array} data.stocks - 股票代码数组
 * @param {Array} data.strategies - 策略ID数组
 * @returns {Promise}
 */
export function analyzeBatchStocks(data) {
  return post('/analysis/batch', data)
}

/**
 * 获取最新的分析结果摘要
 * @param {Number} limit - 返回结果数量限制
 * @returns {Promise}
 */
export function getLatestAnalysisResults(limit = 10) {
  return get('/analysis/latest', { params: { limit } })
}

/**
 * 获取分析收藏夹列表
 * @returns {Promise}
 */
export function getAnalysisFavorites() {
  return get('/analysis/favorites')
}

/**
 * 添加分析结果到收藏夹
 * @param {String} resultId - 结果ID
 * @returns {Promise}
 */
export function addAnalysisFavorite(resultId) {
  return post('/analysis/favorites', { resultId })
}

/**
 * 从收藏夹移除分析结果
 * @param {String} resultId - 结果ID
 * @returns {Promise}
 */
export function removeAnalysisFavorite(resultId) {
  return get(`/analysis/favorites/remove/${resultId}`)
} 