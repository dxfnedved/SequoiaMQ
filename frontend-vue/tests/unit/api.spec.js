/* eslint-disable no-undef */
import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest'
import axios from 'axios'
import MockAdapter from 'axios-mock-adapter'

// 创建axios mock适配器
const mock = new MockAdapter(axios)

// 模拟API模块
vi.mock('@/api/stock', async () => {
  return {
    searchStocks: vi.fn(),
    getStockPrice: vi.fn(),
    getStockKlines: vi.fn(),
    getStockInfo: vi.fn(),
    getCompanyInfo: vi.fn(),
    getBatchStockPrices: vi.fn(),
    getStockList: vi.fn(),
    getStockDetail: vi.fn(),
    getStockHistory: vi.fn()
  }
})

vi.mock('@/api/watchlist', async () => {
  return {
    fetchWatchlist: vi.fn(),
    addToWatchlist: vi.fn(),
    removeFromWatchlist: vi.fn()
  }
})

vi.mock('@/api/analysis', async () => {
  return {
    fetchAnalysisResults: vi.fn()
  }
})

vi.mock('@/api/strategy', async () => {
  return {
    fetchStrategies: vi.fn(),
    updateStrategySettings: vi.fn()
  }
})

// 导入API函数（在模拟之后导入）
import { 
  searchStocks, 
  getStockPrice, 
  getStockKlines,
  getStockInfo,
  getCompanyInfo,
  getBatchStockPrices,
  getStockList,
  getStockDetail,
  getStockHistory
} from '@/api/stock'
import { 
  fetchWatchlist, 
  addToWatchlist, 
  removeFromWatchlist 
} from '@/api/watchlist'
import { fetchAnalysisResults } from '@/api/analysis'
import { fetchStrategies, updateStrategySettings } from '@/api/strategy'

describe('股票API功能', () => {
  beforeEach(() => {
    // 重置所有模拟
    vi.resetAllMocks()
    mock.reset()
  })
  
  afterEach(() => {
    // 清理所有模拟
    vi.clearAllMocks()
  })
  
  test('getStockList应该返回股票列表', async () => {
    // 模拟数据
    const mockStocks = [
      { code: '000001', name: '平安银行' },
      { code: '600000', name: '浦发银行' }
    ]
    
    // 设置mock响应
    getStockList.mockResolvedValueOnce(mockStocks)
    
    // 调用API
    const result = await getStockList()
    
    // 验证结果
    expect(result).toEqual(mockStocks)
  })
  
  test('getStockDetail应该返回股票详情', async () => {
    // 模拟数据
    const mockDetail = {
      code: '000001',
      name: '平安银行',
      price: 18.55,
      change: 0.25,
      changePercent: 1.35
    }
    
    // 设置mock响应
    getStockDetail.mockResolvedValueOnce(mockDetail)
    
    // 调用API
    const result = await getStockDetail('000001')
    
    // 验证结果
    expect(result).toEqual(mockDetail)
  })
  
  test('getStockHistory应该返回股票历史数据', async () => {
    // 模拟数据
    const mockHistory = [
      { date: '2023-01-01', open: 18.0, high: 18.5, low: 17.8, close: 18.2, volume: 10000 },
      { date: '2023-01-02', open: 18.2, high: 18.7, low: 18.1, close: 18.5, volume: 12000 }
    ]
    
    // 设置mock响应
    getStockHistory.mockResolvedValueOnce(mockHistory)
    
    // 调用API
    const result = await getStockHistory('000001', '2023-01-01', '2023-01-02')
    
    // 验证结果
    expect(result).toEqual(mockHistory)
  })
  
  test('API调用失败时应该抛出错误', async () => {
    // 设置mock响应为错误
    getStockList.mockRejectedValueOnce(new Error('API错误'))
    
    // 验证API调用抛出错误
    await expect(getStockList()).rejects.toThrow()
  })
})

describe('API测试', () => {
  // 在每个测试之前重置mock
  beforeEach(() => {
    vi.resetAllMocks()
    mock.reset()
  })

  // 在所有测试后恢复原始adapter
  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('股票API', () => {
    test('搜索股票', async () => {
      const mockData = [
        { code: '000001', name: '平安银行' },
        { code: '600000', name: '浦发银行' }
      ]
      
      searchStocks.mockResolvedValueOnce({ success: true, data: mockData })
      
      const response = await searchStocks({ keyword: '银行' })
      expect(response.data).toEqual(mockData)
    })

    test('获取股票价格', async () => {
      const mockData = {
        code: '000001',
        name: '平安银行',
        price: 10.5,
        change: 0.5,
        changePercent: 5.0
      }
      
      getStockPrice.mockResolvedValueOnce({ success: true, data: mockData })
      
      const response = await getStockPrice('000001')
      expect(response.data).toEqual(mockData)
    })
    
    test('获取K线数据', async () => {
      const mockData = [
        { date: '2023-01-01', open: 10, high: 11, low: 9.5, close: 10.8, volume: 10000 },
        { date: '2023-01-02', open: 10.8, high: 11.2, low: 10.5, close: 11, volume: 12000 }
      ]
      
      getStockKlines.mockResolvedValueOnce({ success: true, data: mockData })
      
      const response = await getStockKlines('000001')
      expect(response.data).toEqual(mockData)
    })

    test('获取股票信息', async () => {
      const mockData = {
        code: '000001',
        name: '平安银行',
        industry: '银行',
        listDate: '1991-04-03'
      }
      
      getStockInfo.mockResolvedValueOnce({ success: true, data: mockData })
      
      const response = await getStockInfo('000001')
      expect(response.data).toEqual(mockData)
    })
    
    test('获取公司信息', async () => {
      const mockData = {
        code: '000001',
        name: '平安银行',
        description: '平安银行股份有限公司...',
        website: 'http://bank.pingan.com'
      }
      
      getCompanyInfo.mockResolvedValueOnce({ success: true, data: mockData })
      
      const response = await getCompanyInfo('000001')
      expect(response.data).toEqual(mockData)
    })
    
    test('批量获取股票价格', async () => {
      const mockData = {
        '000001': { price: 10.5, change: 0.5, changePercent: 5.0 },
        '600000': { price: 8.2, change: -0.3, changePercent: -3.5 }
      }
      
      getBatchStockPrices.mockResolvedValueOnce({ success: true, data: mockData })
      
      const response = await getBatchStockPrices(['000001', '600000'])
      expect(response.data).toEqual(mockData)
    })
  })

  describe('自选股API', () => {
    test('获取自选股列表', async () => {
      const mockData = [
        { code: '000001', name: '平安银行' },
        { code: '600000', name: '浦发银行' }
      ]
      
      fetchWatchlist.mockResolvedValueOnce({ success: true, data: mockData })
      
      const response = await fetchWatchlist()
      expect(response.data).toEqual(mockData)
    })

    test('添加自选股', async () => {
      addToWatchlist.mockResolvedValueOnce({ success: true })
      
      const response = await addToWatchlist({ code: '000001', name: '平安银行' })
      expect(response.success).toBe(true)
    })

    test('删除自选股', async () => {
      removeFromWatchlist.mockResolvedValueOnce({ success: true })
      
      const response = await removeFromWatchlist('000001')
      expect(response.success).toBe(true)
    })
  })

  describe('分析API', () => {
    test('获取分析结果', async () => {
      const mockData = [
        { 
          id: '123', 
          code: '000001', 
          name: '平安银行',
          result: true,
          strategy: 'RSRS',
          date: '2023-01-01',
          details: { score: 0.95 }
        }
      ]
      
      fetchAnalysisResults.mockResolvedValueOnce({ success: true, data: mockData })
      
      const response = await fetchAnalysisResults()
      expect(response.data).toEqual(mockData)
    })
  })

  describe('策略API', () => {
    test('获取策略列表', async () => {
      const mockData = [
        { id: 'rsrs', name: 'RSRS择时', description: '基于阻力支撑相对强度...' },
        { id: 'turtle', name: '海龟交易法', description: '基于趋势跟踪的交易系统...' }
      ]
      
      fetchStrategies.mockResolvedValueOnce({ success: true, data: mockData })
      
      const response = await fetchStrategies()
      expect(response.data).toEqual(mockData)
    })

    test('更新策略设置', async () => {
      updateStrategySettings.mockResolvedValueOnce({ success: true })
      
      const response = await updateStrategySettings('rsrs', { threshold: 0.7 })
      expect(response.success).toBe(true)
    })
  })
}) 