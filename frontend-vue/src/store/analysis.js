/**
 * 分析结果状态管理库
 * 使用Pinia管理策略分析结果数据
 */
import { defineStore } from 'pinia'
import { fetchAnalysisResults, runAnalysis } from '@/api/analysis'

// 定义分析结果状态仓库
export const useAnalysisStore = defineStore('analysis', {
  // 状态
  state: () => ({
    // 分析结果列表
    results: [],
    // 当前分析详情
    currentAnalysis: null,
    // 分析进度
    analysisProgress: 0,
    // 分析状态 idle | running | completed | error
    analysisStatus: 'idle',
    // 加载状态
    loading: false,
    // 错误信息
    error: null,
    // 最后分析时间
    lastAnalyzed: null,
    // 分析策略配置
    strategyConfig: {
      // 启用的策略
      enabledStrategies: [
        'RSRS_Strategy',
        'TurtleStrategy',
        'LowBacktraceStrategy'
      ],
      // 分析优先级
      priorities: {
        'RSRS_Strategy': 1,
        'TurtleStrategy': 2,
        'LowBacktraceStrategy': 3
      },
      // 是否使用并行分析
      useParallel: true,
      // 并行线程数
      maxWorkers: 8
    }
  }),
  
  // 获取计算属性
  getters: {
    // 获取具有买入信号的股票
    buySignals: (state) => {
      return state.results.filter(result => 
        result && result.buy_signals && result.buy_signals > 0
      )
    },
    
    // 获取具有卖出信号的股票
    sellSignals: (state) => {
      return state.results.filter(result => 
        result && result.sell_signals && result.sell_signals > 0
      )
    },
    
    // 按信号强度排序的结果
    resultsByStrength: (state) => {
      return [...state.results].sort((a, b) => {
        // 首先按买入信号数量排序
        if (a.buy_signals !== b.buy_signals) {
          return b.buy_signals - a.buy_signals
        }
        
        // 其次按信号强度排序
        const aStrength = a.signal_details?.[0]?.strength || 0
        const bStrength = b.signal_details?.[0]?.strength || 0
        return bStrength - aStrength
      })
    },
    
    // 分析是否正在运行
    isAnalysisRunning: (state) => state.analysisStatus === 'running',
    
    // 分析是否完成
    isAnalysisCompleted: (state) => state.analysisStatus === 'completed',
    
    // 分析结果统计
    analysisStats: (state) => {
      return {
        totalAnalyzed: state.results.length,
        buySignals: state.buySignals.length,
        sellSignals: state.sellSignals.length,
        noSignals: state.results.length - state.buySignals.length - state.sellSignals.length,
        lastUpdated: state.lastAnalyzed
      }
    }
  },
  
  // 定义操作
  actions: {
    /**
     * 加载分析结果
     */
    async loadAnalysisResults() {
      this.loading = true
      this.error = null
      
      try {
        // 调用API获取分析结果
        const response = await fetchAnalysisResults()
        this.results = response.data
        this.lastAnalyzed = new Date()
        this.analysisStatus = 'completed'
      } catch (error) {
        console.error('加载分析结果失败:', error)
        this.error = '加载分析结果失败，请稍后重试'
        this.analysisStatus = 'error'
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 执行股票分析
     * @param {Array} stocks - 要分析的股票列表，如果为空则分析所有股票
     */
    async startAnalysis(stocks = []) {
      // 如果已经在分析中，则不重复启动
      if (this.analysisStatus === 'running') {
        return
      }
      
      this.analysisStatus = 'running'
      this.analysisProgress = 0
      this.error = null
      
      try {
        // 调用API开始分析
        const response = await runAnalysis({
          stocks: stocks,
          config: this.strategyConfig
        })
        
        // 监听分析进度
        this._monitorAnalysisProgress(response.data.taskId)
      } catch (error) {
        console.error('启动分析失败:', error)
        this.error = '启动分析失败，请稍后重试'
        this.analysisStatus = 'error'
      }
    },
    
    /**
     * 监控分析进度
     * @param {String} taskId - 分析任务ID
     * @private
     */
    async _monitorAnalysisProgress(taskId) {
      // 这里简化处理，实际应使用WebSocket或轮询获取进度
      // 模拟进度更新
      const interval = setInterval(async () => {
        // 增加进度
        this.analysisProgress += 5
        
        // 完成分析
        if (this.analysisProgress >= 100) {
          clearInterval(interval)
          this.analysisProgress = 100
          this.analysisStatus = 'completed'
          this.lastAnalyzed = new Date()
          
          // 完成后加载最新结果
          await this.loadAnalysisResults()
        }
      }, 1000)
    },
    
    /**
     * 中止分析进程
     */
    stopAnalysis() {
      // 实际应调用API中止后端分析进程
      this.analysisStatus = 'idle'
      this.analysisProgress = 0
    },
    
    /**
     * 更新策略配置
     * @param {Object} config - 新的策略配置
     */
    updateStrategyConfig(config) {
      this.strategyConfig = {
        ...this.strategyConfig,
        ...config
      }
    },
    
    /**
     * 设置当前分析的股票详情
     * @param {Object} stockAnalysis - 股票分析详情
     */
    setCurrentAnalysis(stockAnalysis) {
      this.currentAnalysis = stockAnalysis
    },
    
    /**
     * 清除分析结果
     */
    clearResults() {
      if (confirm('确定要清空所有分析结果吗？此操作不可恢复!')) {
        this.results = []
        this.currentAnalysis = null
        this.analysisStatus = 'idle'
        this.analysisProgress = 0
      }
    }
  }
}) 