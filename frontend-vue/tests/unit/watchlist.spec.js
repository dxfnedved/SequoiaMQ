import { describe, it, expect, beforeEach, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import WatchlistComponent from '@/components/Watchlist.vue'
import { useWatchlistStore } from '@/stores/watchlist'

describe('自选股功能', () => {
  beforeEach(() => {
    // 创建一个新的 Pinia 实例并使其处于激活状态
    setActivePinia(createPinia())
    
    // 重置所有模拟
    vi.resetAllMocks()
    
    // 模拟localStorage
    vi.spyOn(localStorage, 'getItem').mockImplementation((key) => {
      if (key === 'watchlist') return JSON.stringify([])
      return null
    })
    
    vi.spyOn(localStorage, 'setItem').mockImplementation(() => {})
  })
  
  it('初始化时自选股列表应该为空', () => {
    const watchlistStore = useWatchlistStore()
    expect(watchlistStore.stocks).toEqual([])
  })
  
  it('可以添加股票到自选股', () => {
    const watchlistStore = useWatchlistStore()
    const stockInfo = { code: '000001', name: '平安银行' }
    
    watchlistStore.addStock(stockInfo)
    
    expect(watchlistStore.stocks).toContainEqual(stockInfo)
    expect(localStorage.setItem).toHaveBeenCalledWith('watchlist', JSON.stringify([stockInfo]))
  })
  
  it('不能重复添加相同的股票', () => {
    const watchlistStore = useWatchlistStore()
    const stockInfo = { code: '000001', name: '平安银行' }
    
    watchlistStore.addStock(stockInfo)
    watchlistStore.addStock(stockInfo)
    
    expect(watchlistStore.stocks.length).toBe(1)
  })
  
  it('可以从自选股中移除股票', () => {
    const watchlistStore = useWatchlistStore()
    const stockInfo = { code: '000001', name: '平安银行' }
    
    watchlistStore.addStock(stockInfo)
    watchlistStore.removeStock('000001')
    
    expect(watchlistStore.stocks).toEqual([])
    expect(localStorage.setItem).toHaveBeenCalledWith('watchlist', JSON.stringify([]))
  })
  
  it('自选股组件应该正确渲染', () => {
    const wrapper = shallowMount(WatchlistComponent, {
      global: {
        plugins: [createPinia()],
        stubs: {
          'el-table': true,
          'el-table-column': true,
          'el-button': true,
          'el-empty': true,
          'el-dialog': true,
          'el-icon': true
        }
      }
    })
    expect(wrapper.exists()).toBe(true)
  })
  
  it('应该从localStorage加载自选股', () => {
    const savedStocks = [
      { code: '000001', name: '平安银行' },
      { code: '600000', name: '浦发银行' }
    ]
    
    // 先重置模拟
    vi.spyOn(localStorage, 'getItem').mockReset()
    
    // 模拟localStorage中存储的自选股
    vi.spyOn(localStorage, 'getItem').mockImplementation((key) => {
      if (key === 'watchlist') return JSON.stringify(savedStocks)
      return null
    })
    
    // 重新创建store以触发初始化
    setActivePinia(createPinia())
    const watchlistStore = useWatchlistStore()
    
    // 手动调用加载方法
    watchlistStore.loadWatchlist()
    
    expect(watchlistStore.stocks).toEqual(savedStocks)
  })
  
  it('可以检查股票是否在自选股中', () => {
    const watchlistStore = useWatchlistStore()
    const stockInfo = { code: '000001', name: '平安银行' }
    
    watchlistStore.addStock(stockInfo)
    
    expect(watchlistStore.isInWatchlist('000001')).toBe(true)
    expect(watchlistStore.isInWatchlist('600000')).toBe(false)
  })
}) 