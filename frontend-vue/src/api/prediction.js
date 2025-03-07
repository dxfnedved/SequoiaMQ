/**
 * 预测API
 * 封装模型预测相关的API请求
 */
import { get, post } from './request'

/**
 * 启动LSTM预测任务
 * @param {Object} data - 预测参数
 * @returns {Promise}
 */
export function runLstmPrediction(data) {
  return post('/prediction/lstm/start', data)
}

/**
 * 获取预测任务状态
 * @param {String} taskId - 任务ID
 * @returns {Promise}
 */
export function getPredictionTaskStatus(taskId) {
  return get(`/prediction/status/${taskId}`)
}

/**
 * 获取LSTM预测结果
 * @param {String} resultId - 结果ID或任务ID
 * @returns {Promise}
 */
export function getLstmPredictionResult(resultId) {
  return get(`/prediction/lstm/result/${resultId}`)
}

/**
 * 获取LSTM预测历史记录
 * @param {Object} params - 查询参数 (可选)
 * @returns {Promise}
 */
export function getLstmPredictionHistory(params) {
  return get('/prediction/lstm/history', { params })
}

/**
 * 启动LLM预测任务
 * @param {Object} data - 预测参数
 * @returns {Promise}
 */
export function startLlmPrediction(data) {
  return post('/prediction/llm/start', data)
}

/**
 * 获取LLM预测结果
 * @param {String} resultId - 结果ID或任务ID
 * @returns {Promise}
 */
export function getLlmPredictionResult(resultId) {
  return get(`/prediction/llm/result/${resultId}`)
}

/**
 * 获取LLM预测历史记录
 * @param {Object} params - 查询参数 (可选)
 * @returns {Promise}
 */
export function getLlmPredictionHistory(params) {
  return get('/prediction/llm/history', { params })
}

/**
 * 获取可用的LLM模型列表
 * @returns {Promise}
 */
export function getAvailableLlmModels() {
  return get('/prediction/llm/models')
}

/**
 * 获取股票分析历史
 * @param {String} stockCode - 股票代码
 * @param {Object} params - 查询参数 (可选)
 * @returns {Promise}
 */
export function getStockAnalysisHistory(stockCode, params) {
  return get(`/stocks/${stockCode}/analysis/history`, { params })
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