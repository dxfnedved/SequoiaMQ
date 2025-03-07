import { defineStore } from 'pinia'

export const useWatchlistStore = defineStore('watchlist', {
  state: () => ({
    stocks: []
  }),
  
  getters: {
    stockCount: (state) => state.stocks.length
  },
  
  actions: {
    addStock(stock) {
      // 检查是否已存在
      if (!this.isInWatchlist(stock.code)) {
        this.stocks.push(stock)
        this.saveWatchlist()
      }
    },
    
    removeStock(code) {
      this.stocks = this.stocks.filter(stock => stock.code !== code)
      this.saveWatchlist()
    },
    
    isInWatchlist(code) {
      return this.stocks.some(stock => stock.code === code)
    },
    
    saveWatchlist() {
      localStorage.setItem('watchlist', JSON.stringify(this.stocks))
    },
    
    loadWatchlist() {
      try {
        const savedWatchlist = localStorage.getItem('watchlist')
        if (savedWatchlist) {
          this.stocks = JSON.parse(savedWatchlist)
        }
      } catch (error) {
        console.error('加载自选股失败:', error)
      }
    },
    
    clearWatchlist() {
      this.stocks = []
      this.saveWatchlist()
    }
  }
}) 