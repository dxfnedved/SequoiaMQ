/**
 * 预测结果状态管理库
 * 使用Pinia管理LSTM和LLM预测结果数据
 */
import { defineStore } from 'pinia'
import { runLstmPrediction, runLlmPrediction, fetchPredictionHistory } from '@/api/prediction'

// 定义预测结果状态仓库
export const usePredictionStore = defineStore('prediction', {
  // 状态
  state: () => ({
    // LSTM预测结果
    lstmResults: {},
    // LLM预测结果
    llmResults: {},
    // 历史预测结果
    predictionHistory: [],
    // 当前预测详情
    currentPrediction: null,
    // 预测进度
    predictionProgress: 0,
    // 预测状态 idle | running | completed | error
    predictionStatus: 'idle',
    // 预测类型 lstm | llm
    predictionType: null,
    // 加载状态
    loading: false,
    // 错误信息
    error: null,
    // 预测配置
    predictionConfig: {
      // LSTM配置
      lstm: {
        timeSteps: 20,
        epochs: 100,
        batchSize: 32,
        lookAhead: 5
      },
      // LLM配置
      llm: {
        includeTechnical: true,
        includeNews: true,
        includeFinancial: true,
        modelType: 'gpt-4'
      }
    }
  }),
  
  // 获取计算属性
  getters: {
    // 获取指定股票的LSTM预测结果
    getLstmResultForStock: (state) => (code) => {
      return state.lstmResults[code] || null
    },
    
    // 获取指定股票的LLM预测结果
    getLlmResultForStock: (state) => (code) => {
      return state.llmResults[code] || null
    },
    
    // 获取最近的预测历史
    recentPredictions: (state) => {
      return state.predictionHistory.slice().reverse().slice(0, 10)
    },
    
    // 预测是否正在运行
    isPredictionRunning: (state) => state.predictionStatus === 'running',
    
    // 按准确率排序的历史预测
    predictionsByAccuracy: (state) => {
      return [...state.predictionHistory].sort((a, b) => {
        return (b.accuracy || 0) - (a.accuracy || 0)
      })
    }
  },
  
  // 定义操作
  actions: {
    /**
     * 加载预测历史
     */
    async loadPredictionHistory() {
      this.loading = true
      this.error = null
      
      try {
        // 调用API获取预测历史
        const response = await fetchPredictionHistory()
        this.predictionHistory = response.data
      } catch (error) {
        console.error('加载预测历史失败:', error)
        this.error = '加载预测历史失败，请稍后重试'
      } finally {
        this.loading = false
      }
    },
    
    /**
     * 执行LSTM预测
     * @param {Object} params - 预测参数
     * @param {String} params.code - 股票代码
     * @param {String} params.name - 股票名称
     * @param {Object} params.config - 预测配置
     */
    async runLstmPrediction(params) {
      // 如果已经在预测中，则不重复启动
      if (this.predictionStatus === 'running') {
        return
      }
      
      this.predictionStatus = 'running'
      this.predictionType = 'lstm'
      this.predictionProgress = 0
      this.error = null
      
      try {
        const { code, name, config } = params
        
        // 合并配置
        const predictionConfig = {
          ...this.predictionConfig.lstm,
          ...(config || {})
        }
        
        // 调用API开始预测
        const response = await runLstmPrediction({
          code,
          name,
          config: predictionConfig
        })
        
        // 监听预测进度
        this._monitorPredictionProgress(response.data.taskId, code)
      } catch (error) {
        console.error('LSTM预测失败:', error)
        this.error = 'LSTM预测失败，请稍后重试'
        this.predictionStatus = 'error'
      }
    },
    
    /**
     * 执行LLM预测
     * @param {Object} params - 预测参数
     * @param {String} params.code - 股票代码
     * @param {String} params.name - 股票名称
     * @param {Object} params.config - 预测配置
     */
    async runLlmPrediction(params) {
      // 如果已经在预测中，则不重复启动
      if (this.predictionStatus === 'running') {
        return
      }
      
      this.predictionStatus = 'running'
      this.predictionType = 'llm'
      this.predictionProgress = 0
      this.error = null
      
      try {
        const { code, name, config } = params
        
        // 合并配置
        const predictionConfig = {
          ...this.predictionConfig.llm,
          ...(config || {})
        }
        
        // 调用API开始预测
        const response = await runLlmPrediction({
          code,
          name,
          config: predictionConfig
        })
        
        // 监听预测进度
        this._monitorPredictionProgress(response.data.taskId, code)
      } catch (error) {
        console.error('LLM预测失败:', error)
        this.error = 'LLM预测失败，请稍后重试'
        this.predictionStatus = 'error'
      }
    },
    
    /**
     * 监控预测进度
     * @param {String} taskId - 预测任务ID
     * @param {String} code - 股票代码
     * @private
     */
    async _monitorPredictionProgress(taskId, code) {
      // 这里简化处理，实际应使用WebSocket或轮询获取进度
      // 模拟进度更新
      const interval = setInterval(async () => {
        // 增加进度
        this.predictionProgress += 5
        
        // 完成预测
        if (this.predictionProgress >= 100) {
          clearInterval(interval)
          this.predictionProgress = 100
          this.predictionStatus = 'completed'
          
          try {
            // 模拟预测结果
            const result = {
              code,
              date: new Date().toISOString(),
              type: this.predictionType,
              predictions: Array.from({ length: 5 }, (_, i) => ({
                date: new Date(Date.now() + (i + 1) * 86400000).toISOString().split('T')[0],
                price: Math.random() * 100 + 50,
                confidence: Math.random() * 0.3 + 0.7
              })),
              metrics: {
                mse: Math.random() * 0.1,
                accuracy: Math.random() * 0.2 + 0.7
              }
            }
            
            // 存储结果
            if (this.predictionType === 'lstm') {
              this.lstmResults[code] = result
            } else {
              this.llmResults[code] = result
            }
            
            // 添加到历史记录
            this.predictionHistory.push(result)
            
            // 设置当前预测
            this.currentPrediction = result
          } catch (error) {
            console.error('获取预测结果失败:', error)
            this.error = '获取预测结果失败，请稍后重试'
          }
        }
      }, 1000)
    },
    
    /**
     * 中止预测进程
     */
    stopPrediction() {
      // 实际应调用API中止后端预测进程
      this.predictionStatus = 'idle'
      this.predictionProgress = 0
      this.predictionType = null
    },
    
    /**
     * 更新预测配置
     * @param {String} type - 预测类型 lstm 或 llm
     * @param {Object} config - 新的预测配置
     */
    updatePredictionConfig(type, config) {
      if (type === 'lstm') {
        this.predictionConfig.lstm = {
          ...this.predictionConfig.lstm,
          ...config
        }
      } else if (type === 'llm') {
        this.predictionConfig.llm = {
          ...this.predictionConfig.llm,
          ...config
        }
      }
    },
    
    /**
     * 设置当前预测详情
     * @param {Object} prediction - 预测详情
     */
    setCurrentPrediction(prediction) {
      this.currentPrediction = prediction
    },
    
    /**
     * 清除预测结果
     * @param {String} type - 预测类型 lstm 或 llm 或 all
     */
    clearPredictions(type = 'all') {
      if (type === 'lstm' || type === 'all') {
        this.lstmResults = {}
      }
      
      if (type === 'llm' || type === 'all') {
        this.llmResults = {}
      }
      
      if (type === 'all') {
        this.predictionHistory = []
        this.currentPrediction = null
      }
      
      this.predictionStatus = 'idle'
      this.predictionProgress = 0
      this.predictionType = null
    }
  }
}) 