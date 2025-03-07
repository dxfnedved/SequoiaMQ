/**
 * 股票API
 * 封装股票数据相关的API请求
 */
import { get, post, put, delete as del } from './request'

/**
 * 搜索股票
 * @param {string} keyword - 搜索关键词
 * @returns {Promise<Array>} - 搜索结果
 */
export function searchStocks(keyword) {
  return get('/api/stocks/search', {
    params: { keyword }
  })
}

/**
 * 获取股票信息
 * @param {string} code - 股票代码
 * @returns {Promise<Object>} - 股票信息
 */
export function getStockInfo(code) {
  return get(`/api/stocks/info/${code}`)
}

/**
 * 获取股票K线数据
 * @param {string} code - 股票代码
 * @param {string} period - 周期，可选值：daily, weekly, monthly
 * @param {number} count - 数量
 * @returns {Promise<Array>} - K线数据
 */
export function getStockKlines(code, period = 'daily', count = 90) {
  return get(`/api/stocks/klines/${code}`, {
    params: { period, count }
  })
}

/**
 * 获取股票最新价格
 * @param {string} code - 股票代码
 * @returns {Promise<Object>} - 价格数据
 */
export function getStockPrice(code) {
  return get(`/api/stocks/price/${code}`)
}

/**
 * 批量获取股票价格
 * @param {Array<string>} codes - 股票代码列表
 * @returns {Promise<Array>} - 价格数据列表
 */
export function getBatchStockPrices(codes) {
  return post('/api/stocks/prices', {
    codes
  })
}

/**
 * 获取股票自选列表
 * @returns {Promise<Array>} - 自选股列表
 */
export function getWatchlist() {
  return get('/api/watchlist')
}

/**
 * 添加股票到自选
 * @param {string} code - 股票代码
 * @param {string} name - 股票名称
 * @param {string} notes - 备注
 * @returns {Promise<Object>} - 添加结果
 */
export function addToWatchlist(code, name, notes = '') {
  return post('/api/watchlist', {
    code,
    name,
    notes
  })
}

/**
 * 从自选中删除股票
 * @param {string} code - 股票代码
 * @returns {Promise<Object>} - 删除结果
 */
export function removeFromWatchlist(code) {
  return del(`/api/watchlist/${code}`)
}

/**
 * 批量删除自选股
 * @param {Array<string>} codes - 股票代码列表
 * @returns {Promise<Object>} - 删除结果
 */
export function batchRemoveFromWatchlist(codes) {
  return post('/api/watchlist/batch-delete', {
    codes
  })
}

/**
 * 更新自选股备注
 * @param {string} code - 股票代码
 * @param {string} notes - 备注
 * @returns {Promise<Object>} - 更新结果
 */
export function updateWatchlistNotes(code, notes) {
  return put(`/api/watchlist/${code}`, {
    notes
  })
}

/**
 * 获取股票财务数据
 * @param {string} code - 股票代码
 * @returns {Promise<Object>} - 财务数据
 */
export function getStockFinancials(code) {
  return get(`/api/stocks/financials/${code}`)
}

/**
 * 获取公司信息
 * @param {string} code - 股票代码
 * @returns {Promise<Object>} - 公司信息
 */
export function getCompanyInfo(code) {
  return get(`/api/stocks/company/${code}`)
}

/**
 * 获取行业列表
 * @returns {Promise<Array>} - 行业列表
 */
export function getIndustries() {
  return get('/api/stocks/industries')
}

/**
 * 获取行业内股票
 * @param {string} industry - 行业名称
 * @returns {Promise<Array>} - 行业内股票列表
 */
export function getStocksByIndustry(industry) {
  return get('/api/stocks/industry', {
    params: { industry }
  })
}

/**
 * 获取市场概览
 * @returns {Promise<Object>} - 市场概览数据
 */
export function getMarketOverview() {
  return get('/api/stocks/market-overview')
}

/**
 * 分析股票
 * @param {Object} params - 分析参数
 * @returns {Promise<Object>} - 分析结果
 */
export function analyzeStocks(params) {
  return post('/api/analysis', params)
}

/**
 * 获取分析历史
 * @returns {Promise<Array>} - 分析历史列表
 */
export function getAnalysisHistory() {
  return get('/api/analysis/history')
}

/**
 * 获取分析结果
 * @param {string} id - 分析ID
 * @returns {Promise<Object>} - 分析结果
 */
export function getAnalysisResult(id) {
  return get(`/api/analysis/${id}`)
} 
