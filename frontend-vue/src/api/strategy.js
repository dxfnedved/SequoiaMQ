import { get, post, put, delete as del } from './request'

/**
 * 获取策略列表
 * @returns {Promise<Object>} 策略列表数据
 */
export function fetchStrategies() {
  return request({
    url: '/api/strategies',
    method: 'get'
  })
}

/**
 * 更新策略设置
 * @param {string} strategyId 策略ID
 * @param {Object} settings 策略设置
 * @returns {Promise<Object>} 更新结果
 */
export function updateStrategySettings(strategyId, settings) {
  return request({
    url: '/api/strategies/settings',
    method: 'post',
    data: {
      strategyId,
      settings
    }
  })
}

/**
 * 获取策略详情
 * @param {string} strategyId 策略ID
 * @returns {Promise<Object>} 策略详情
 */
export function getStrategyDetail(strategyId) {
  return request({
    url: `/api/strategies/${strategyId}`,
    method: 'get'
  })
}

/**
 * 启用/禁用策略
 * @param {string} strategyId 策略ID
 * @param {boolean} enabled 是否启用
 * @returns {Promise<Object>} 操作结果
 */
export function toggleStrategy(strategyId, enabled) {
  return request({
    url: '/api/strategies/toggle',
    method: 'post',
    data: {
      strategyId,
      enabled
    }
  })
}

/**
 * 获取策略执行历史
 * @param {string} strategyId 策略ID
 * @param {Object} params 查询参数
 * @returns {Promise<Object>} 策略执行历史
 */
export function getStrategyHistory(strategyId, params) {
  return request({
    url: `/api/strategies/${strategyId}/history`,
    method: 'get',
    params
  })
}

/**
 * 获取所有策略的执行统计
 * @returns {Promise<Object>} 策略执行统计
 */
export function getStrategyStats() {
  return request({
    url: '/api/strategies/stats',
    method: 'get'
  })
} 
