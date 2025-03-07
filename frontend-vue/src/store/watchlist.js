/**
 * 自选股状态管理库
 * 使用Pinia管理自选股数据
 */
import { defineStore } from 'pinia'
import { fetchWatchlist, addToWatchlist, removeFromWatchlist, updateWatchlistItem, fetchWatchlistDetails, clearWatchlist } from '@/api/watchlist'

// 定义自选股状态仓库
export const useWatchlistStore = defineStore('watchlist', {
  // 状态
  state: () => ({
    // 自选股列表
    stocks: [],
    // 加载状态
    loading: false,
    // 错误信息
    error: null,
    // 最后更新时间
    lastUpdated: null
  }),
  
  // 获取计算属性
  getters: {
    // 获取股票数量
    stockCount: (state) => state.stocks.length,
    
    // 检查股票是否在自选股列表中
    isInWatchlist: (state) => (code) => {
      return state.stocks.some(stock => stock.code === code)
    },
    
    // 按行业分组的股票
    stocksByIndustry: (state) => {
      const groups = {}
      state.stocks.forEach(stock => {
        const industry = stock.industry || '未分类'
        if (!groups[industry]) {
          groups[industry] = []
        }
        groups[industry].push(stock)
      })
      return groups
    },
    
    // 获取最新价格变动的股票（涨跌幅排序）
    stocksByChange: (state) => {
      return [...state.stocks].sort((a, b) => {
        // 按涨跌幅排序（如果有）
        if (a.change !== undefined && b.change !== undefined) {
          return b.change - a.change
        }
        return 0
      })
    }
  },
  
  // 定义操作
  actions: {
    /**
     * 加载自选股列表
     */
    async loadWatchlist() {
      // 设置加载状态
      this.loading = true
      this.error = null
      
      try {
        // 调用API获取自选股列表
        const response = await fetchWatchlist()
        this.stocks = response.data
        this.lastUpdated = new Date()
        return this.stocks
      } catch (error) {
        console.error('加载自选股失败:', error)
        this.error = '加载自选股失败，请稍后重试'
        throw error
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 加载带有实时价格的自选股详情
     */
    async loadWatchlistDetails() {
      this.loading = true
      this.error = null
      
      try {
        const response = await fetchWatchlistDetails()
        this.stocks = response.data
        this.lastUpdated = new Date()
        return this.stocks
      } catch (error) {
        console.error('加载自选股详情失败:', error)
        this.error = '加载自选股详情失败，请稍后重试'
        throw error
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 添加股票到自选股
     * @param {Object} stock - 要添加的股票信息
     */
    async addStock(stock) {
      // 如果已经存在，则不添加
      if (this.isInWatchlist(stock.code)) {
        return
      }
      
      this.loading = true
      this.error = null
      
      try {
        // 调用API添加自选股
        await addToWatchlist(stock)
        
        // 更新本地状态
        this.stocks.push(stock)
        this.lastUpdated = new Date()
      } catch (error) {
        console.error('添加自选股失败:', error)
        this.error = '添加自选股失败，请稍后重试'
        throw error
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 从自选股移除股票
     * @param {String} code - 要移除的股票代码
     */
    async removeStock(code) {
      this.loading = true
      this.error = null
      
      try {
        // 调用API移除自选股
        await removeFromWatchlist(code)
        
        // 更新本地状态
        this.stocks = this.stocks.filter(stock => stock.code !== code)
        this.lastUpdated = new Date()
      } catch (error) {
        console.error('删除自选股失败:', error)
        this.error = '删除自选股失败，请稍后重试'
        throw error
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 更新自选股信息
     * @param {String} code - 股票代码
     * @param {Object} data - 更新数据
     */
    async updateStock(code, data) {
      this.loading = true
      this.error = null
      
      try {
        // 调用API更新自选股
        await updateWatchlistItem(code, data)
        
        // 更新本地状态
        const index = this.stocks.findIndex(stock => stock.code === code)
        if (index !== -1) {
          this.stocks[index] = {
            ...this.stocks[index],
            ...data
          }
        }
        
        this.lastUpdated = new Date()
      } catch (error) {
        console.error('更新自选股失败:', error)
        this.error = '更新自选股失败，请稍后重试'
        throw error
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 获取单个股票详情
     * @param {String} code - 股票代码
     */
    async getStockDetail(code) {
      try {
        // 先从本地状态中查找
        const stock = this.stocks.find(s => s.code === code)
        if (stock) {
          return stock
        }
        
        // 如果本地没有，尝试从API获取
        const response = await fetchWatchlistDetails()
        const stockDetail = response.data.find(s => s.code === code)
        
        return stockDetail || null
      } catch (error) {
        console.error('获取股票详情失败:', error)
        throw error
      }
    },
    
    /**
     * 批量更新股票数据
     * @param {Array} updatedStocks - 更新的股票数据
     */
    updateStocksData(updatedStocks) {
      // 遍历需要更新的股票
      updatedStocks.forEach(updatedStock => {
        // 查找本地股票
        const index = this.stocks.findIndex(s => s.code === updatedStock.code)
        if (index !== -1) {
          // 合并更新数据
          this.stocks[index] = {
            ...this.stocks[index],
            ...updatedStock
          }
        }
      })
      
      this.lastUpdated = new Date()
    },
    
    /**
     * 清除所有自选股
     */
    async clearWatchlist() {
      this.loading = true
      this.error = null
      
      try {
        // 清空所有自选股
        await clearWatchlist()
        
        // 更新本地状态
        this.stocks = []
        this.lastUpdated = new Date()
      } catch (error) {
        console.error('清空自选股失败:', error)
        this.error = '清空自选股失败，请稍后重试'
        throw error
      } finally {
        this.loading = false
      }
    }
  }
}) 