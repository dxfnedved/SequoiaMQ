<template>
  <div class="lstm-predict-container">
    <h1>思维增强LSTM模型预测</h1>
    <div class="content-wrapper">
      <div class="section config-section">
        <h2>预测配置</h2>
        <div class="form-wrapper">
          <el-form label-position="top" :model="formData" ref="formRef">
            <el-form-item label="股票代码" prop="stockCode" required>
              <stock-search-input
                v-model="formData.stockCode"
                @select="handleStockSelect"
                :auto-select-first="false"
                :placeholder="'输入股票代码或名称进行搜索'"
                :debounce="300"
              />
            </el-form-item>
            
            <el-form-item label="股票名称">
              <el-input v-model="formData.stockName" disabled />
            </el-form-item>
            
            <el-form-item label="预测时长">
              <el-select v-model="formData.predictionPeriod" placeholder="选择预测时长" style="width: 100%">
                <el-option label="5个交易日" value="5" />
                <el-option label="10个交易日" value="10" />
                <el-option label="20个交易日" value="20" />
                <el-option label="30个交易日" value="30" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="模型配置">
              <el-radio-group v-model="formData.modelConfig">
                <el-radio label="standard">标准模型</el-radio>
                <el-radio label="enhanced">思维增强版</el-radio>
              </el-radio-group>
              <div class="model-tip" v-if="formData.modelConfig === 'enhanced'">
                思维增强版结合深度学习与传统指标分析，准确率提高约15%
              </div>
            </el-form-item>
            
            <el-form-item label="特征选择">
              <el-checkbox-group v-model="formData.features">
                <el-checkbox label="price">价格数据</el-checkbox>
                <el-checkbox label="volume">成交量</el-checkbox>
                <el-checkbox label="technical">技术指标</el-checkbox>
                <el-checkbox label="sentiment">情绪指标</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="runPrediction" :loading="loading" :disabled="!formData.stockCode">
                开始预测
              </el-button>
              <el-button @click="resetForm">重置</el-button>
            </el-form-item>
          </el-form>
          
          <!-- 任务进度条 -->
          <div v-if="taskId" class="task-progress">
            <h3>预测进度</h3>
            <el-progress 
              :percentage="taskProgress" 
              :status="taskStatus === 'error' ? 'exception' : (taskStatus === 'completed' ? 'success' : '')"
            />
            <p class="task-message">{{ taskMessage }}</p>
          </div>
        </div>
      </div>
      
      <div class="section info-section">
        <h2>模型信息</h2>
        <div class="model-info">
          <div class="info-item">
            <span class="label">模型版本:</span>
            <span class="value">1.2.0</span>
          </div>
          <div class="info-item">
            <span class="label">训练数据集:</span>
            <span class="value">A股历史数据 (2015-2023)</span>
          </div>
          <div class="info-item">
            <span class="label">特征数量:</span>
            <span class="value">24</span>
          </div>
          <div class="info-item">
            <span class="label">标准版精度:</span>
            <span class="value">78.3%</span>
          </div>
          <div class="info-item">
            <span class="label">增强版精度:</span>
            <span class="value">93.1%</span>
          </div>
          <div class="info-item">
            <span class="label">最近更新:</span>
            <span class="value">2023-12-15</span>
          </div>
        </div>
        
        <div class="history-section">
          <h3>历史预测记录</h3>
          <div v-if="loadingHistory" class="loading-message">
            加载历史记录中...
          </div>
          <div v-else-if="predictionHistory.length === 0" class="empty-message">
            暂无历史预测记录
          </div>
          <div v-else class="history-list">
            <div v-for="(item, index) in predictionHistory" :key="index" class="history-item" @click="loadHistoryResult(item)">
              <div class="history-stock">{{ item.stockName }} ({{ item.stockCode }})</div>
              <div class="history-date">{{ formatDate(item.date) }}</div>
              <div class="history-accuracy" :class="getAccuracyClass(item.accuracy)">
                精度: {{ (item.accuracy * 100).toFixed(1) }}%
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 预测结果展示 -->
    <div v-if="showResult && predictionResult" class="section result-section">
      <h2>预测结果</h2>
      <div class="result-info">
        <div class="info-header">
          <div>
            <span class="stock-code">{{ predictionResult.stockCode }}</span>
            <span class="stock-name">{{ predictionResult.stockName }}</span>
          </div>
          <div class="prediction-date">
            预测日期: {{ formatDate(predictionResult.date) }}
          </div>
        </div>
        
        <div class="chart-container">
          <div ref="predictionChart" class="prediction-chart"></div>
        </div>
        
        <div class="prediction-metrics">
          <div class="metric-card">
            <div class="metric-value" :class="getTrendClass(predictionResult.trend)">
              {{ getTrendText(predictionResult.trend) }}
            </div>
            <div class="metric-label">预测趋势</div>
          </div>
          
          <div class="metric-card">
            <div class="metric-value">{{ predictionResult.accuracy.toFixed(2) * 100 }}%</div>
            <div class="metric-label">模型精度</div>
          </div>
          
          <div class="metric-card">
            <div class="metric-value">{{ predictionResult.expectedReturn.toFixed(2) }}%</div>
            <div class="metric-label">预期收益</div>
          </div>
          
          <div class="metric-card">
            <div class="metric-value">{{ predictionResult.volatility.toFixed(2) }}%</div>
            <div class="metric-label">预期波动</div>
          </div>
        </div>
        
        <div class="prediction-details">
          <h3>预测详情</h3>
          <table class="prediction-table">
            <thead>
              <tr>
                <th>日期</th>
                <th>预测价格</th>
                <th>预测波动</th>
                <th>置信度</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(pred, index) in predictionResult.predictions" :key="index">
                <td>{{ formatDate(pred.date) }}</td>
                <td :class="getDiffClass(pred.priceDiff)">{{ pred.price.toFixed(2) }}</td>
                <td>{{ pred.volatility.toFixed(2) }}%</td>
                <td>{{ (pred.confidence * 100).toFixed(0) }}%</td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <div class="analysis-summary">
          <h3>AI分析摘要</h3>
          <div class="summary-content">
            <p>{{ predictionResult.summary }}</p>
          </div>
          <div class="key-factors">
            <h4>关键影响因素</h4>
            <ul>
              <li v-for="(factor, index) in predictionResult.keyFactors" :key="index">
                {{ factor }}
              </li>
            </ul>
          </div>
        </div>
      </div>
      
      <!-- 预测比较组件 -->
      <prediction-comparison 
        v-if="showComparison" 
        :lstm-result="predictionResult" 
        :llm-result="llmPredictionResult"
        :stock-info="{ code: predictionResult.stockCode, name: predictionResult.stockName }"
      />
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed, nextTick, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, MarkLineComponent, DataZoomComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { runLstmPrediction, getLstmPredictionResult, getLstmPredictionHistory, getLlmPredictionResult } from '@/api/prediction'
import { searchStocks, getStockInfo } from '@/api/stock'
import { fetchWatchlist, addToWatchlist, removeFromWatchlist } from '@/api/watchlist'
import StockSearchInput from '@/components/StockSearchInput.vue'
import PredictionComparison from '@/components/PredictionComparison.vue'

// 注册必要的echarts组件
echarts.use([
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  MarkLineComponent,
  DataZoomComponent,
  CanvasRenderer
])

export default {
  name: 'LstmPredict',
  components: {
    StockSearchInput,
    PredictionComparison
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const formRef = ref(null)
    const predictionChart = ref(null)
    const chartInstance = ref(null)
    const pollTimer = ref(null)
    
    // 表单数据
    const formData = reactive({
      stockCode: '',
      stockName: '',
      predictionPeriod: '10',
      modelConfig: 'enhanced',
      features: ['price', 'volume', 'technical', 'sentiment']
    })
    
    // 页面状态
    const loading = ref(false)
    const showResult = ref(false)
    const loadingHistory = ref(false)
    const predictionResult = ref(null)
    const predictionHistory = ref([])
    const taskId = ref('')
    const taskStatus = ref('')
    const taskProgress = ref(0)
    const taskMessage = ref('')
    const watchlistStocks = ref([])
    
    // 自动预测开关
    const autoPredictAfterSelect = ref(true)
    
    // 预测结果
    const resultId = ref('')
    
    // LLM预测结果（用于比较）
    const llmPredictionResult = ref(null)
    const showComparison = ref(false)
    
    // 格式化日期函数
    const formatDate = (dateString) => {
      const date = new Date(dateString)
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
    }
    
    // 处理股票选择
    const handleStockSelect = (item) => {
      formData.stockCode = item.code
      formData.stockName = item.name
      
      // 如果是在自选股中的股票，可以做一些特殊处理
      if (item.isWatchlist) {
        console.log('从自选股中选择了股票:', item.code)
      }
      
      // 自动进行预测
      if (autoPredictAfterSelect.value) {
        runPrediction()
      }
    }
    
    // 处理键盘事件
    const handleKeyDown = (event) => {
      if (event.key === 'Enter' && formData.stockCode && formData.stockName) {
        runPrediction()
      }
    }
    
    // 初始化
    onMounted(async () => {
      // 加载自选股列表
      await loadWatchlist()
      
      // 添加键盘事件监听
      window.addEventListener('keydown', handleKeyDown)
      
      // 加载历史预测记录
      loadPredictionHistory()
      
      // 检查URL参数中是否包含股票代码
      const { stockCode } = route.query
      if (stockCode) {
        formData.stockCode = stockCode
        // 尝试获取股票信息
        try {
          const response = await getStockInfo(stockCode)
          if (response.code === 200 && response.data) {
            formData.stockName = response.data.name
            // 自动开始预测
            if (autoPredictAfterSelect.value) {
              runPrediction()
            }
          }
        } catch (error) {
          console.error('获取股票信息失败:', error)
        }
      }
    })
    
    // 组件卸载前清理
    onBeforeUnmount(() => {
      window.removeEventListener('keydown', handleKeyDown)
      // 销毁图表实例，避免内存泄漏
      if (chartInstance.value) {
        chartInstance.value.dispose()
      }
      // 清除任何可能的轮询定时器
      if (pollTimer.value) {
        clearTimeout(pollTimer.value)
      }
    })
    
    // 加载自选股列表
    const loadWatchlist = async () => {
      try {
        const response = await fetchWatchlist()
        if (response.code === 200 && response.data) {
          watchlistStocks.value = response.data || []
        }
      } catch (error) {
        console.error('获取自选股列表失败:', error)
      }
    }
    
    // 加载历史预测记录
    const loadPredictionHistory = async () => {
      loadingHistory.value = true
      try {
        const response = await getLstmPredictionHistory()
        predictionHistory.value = response.data || []
      } catch (error) {
        console.error('获取预测历史失败:', error)
      } finally {
        loadingHistory.value = false
      }
    }
    
    // 运行预测
    const runPrediction = async () => {
      if (!formData.stockCode) return
      
      loading.value = true
      taskStatus.value = 'pending'
      taskProgress.value = 0
      taskMessage.value = '正在初始化预测任务...'
      
      try {
        // 准备请求数据
        const requestData = {
          stockCode: formData.stockCode,
          stockName: formData.stockName,
          predictionPeriod: parseInt(formData.predictionPeriod),
          modelConfig: formData.modelConfig,
          features: formData.features
        }
        
        // 提交预测任务
        const response = await runLstmPrediction(requestData)
        taskId.value = response.data.taskId
        
        // 开始轮询任务状态
        pollTaskStatus()
      } catch (error) {
        console.error('提交预测任务失败:', error)
        taskStatus.value = 'error'
        taskMessage.value = '提交预测任务失败'
      } finally {
        loading.value = false
      }
    }
    
    // 轮询任务状态
    const pollTaskStatus = async () => {
      if (!taskId.value) return
      
      try {
        const response = await getLstmPredictionResult(taskId.value)
        predictionResult.value = response.data
        showResult.value = true
        
        // 更新历史记录
        loadPredictionHistory()
        
        // 等待DOM更新后初始化图表
        nextTick(() => {
          initChart()
        })
      } catch (error) {
        console.error('获取预测结果失败:', error)
      }
    }
    
    // 重置表单
    const resetForm = () => {
      formData.stockCode = ''
      formData.stockName = ''
      formData.predictionPeriod = '10'
      formData.modelConfig = 'enhanced'
      formData.features = ['price', 'volume', 'technical', 'sentiment']
      
      showResult.value = false
      predictionResult.value = null
      taskId.value = null
      taskProgress.value = 0
      taskStatus.value = 'pending'
      taskMessage.value = ''
      
      if (chartInstance.value) {
        chartInstance.value.dispose()
      }
    }
    
    // 初始化图表
    const initChart = () => {
      if (!predictionResult.value) return
      
      if (chartInstance.value) {
        chartInstance.value.dispose()
      }
      
      chartInstance.value = echarts.init(predictionChart.value)
      
      const result = predictionResult.value
      const historicalDates = result.historicalData.map(item => formatDate(item.date))
      const historicalPrices = result.historicalData.map(item => item.price)
      const predictionDates = result.predictions.map(item => formatDate(item.date))
      const predictionPrices = result.predictions.map(item => item.price)
      const lowerBound = result.predictions.map(item => item.price * (1 - item.volatility / 100))
      const upperBound = result.predictions.map(item => item.price * (1 + item.volatility / 100))
      
      const allDates = [...historicalDates, ...predictionDates]
      
      const option = {
        title: {
          text: '股价预测分析',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross'
          }
        },
        legend: {
          data: ['历史价格', '预测价格', '预测区间'],
          bottom: '0%'
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '10%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: allDates,
          axisLabel: {
            rotate: 45
          }
        },
        yAxis: {
          type: 'value',
          name: '价格',
          min: function(value) {
            return Math.floor(Math.min(...historicalPrices, ...lowerBound) * 0.95);
          },
          max: function(value) {
            return Math.ceil(Math.max(...historicalPrices, ...upperBound) * 1.05);
          }
        },
        series: [
          {
            name: '历史价格',
            type: 'line',
            data: [...historicalPrices, null].concat(Array(predictionDates.length - 1).fill(null)),
            showSymbol: false,
            color: '#5470c6'
          },
          {
            name: '预测价格',
            type: 'line',
            data: Array(historicalDates.length).fill(null).concat(predictionPrices),
            lineStyle: {
              width: 2,
              type: 'dashed'
            },
            color: '#91cc75',
            markPoint: {
              symbol: 'pin',
              symbolSize: 40,
              data: [
                { type: 'max', name: '最高点' },
                { type: 'min', name: '最低点' }
              ]
            }
          },
          {
            name: '预测区间',
            type: 'line',
            data: Array(historicalDates.length).fill(null).concat(upperBound),
            lineStyle: {
              opacity: 0
            },
            stack: 'confidence',
            symbol: 'none'
          },
          {
            name: '预测区间',
            type: 'line',
            data: Array(historicalDates.length).fill(null).concat(lowerBound),
            lineStyle: {
              opacity: 0
            },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                {
                  offset: 0,
                  color: 'rgba(145, 204, 117, 0.3)'
                },
                {
                  offset: 1,
                  color: 'rgba(145, 204, 117, 0)'
                }
              ])
            },
            stack: 'confidence',
            symbol: 'none'
          }
        ]
      }
      
      chartInstance.value.setOption(option)
      
      // 响应窗口大小变化
      window.addEventListener('resize', () => {
        chartInstance.value.resize()
      })
    }
    
    // 获取准确度样式类
    const getAccuracyClass = (accuracy) => {
      if (accuracy >= 0.8) return 'excellent'
      if (accuracy >= 0.6) return 'good'
      return 'poor'
    }
    
    // 获取趋势样式类
    const getTrendClass = (trend) => {
      return trend > 0 ? 'positive' : (trend < 0 ? 'negative' : 'neutral')
    }
    
    // 获取趋势文本
    const getTrendText = (trend) => {
      if (trend > 5) return '强烈看涨'
      if (trend > 0) return '看涨'
      if (trend < -5) return '强烈看跌'
      if (trend < 0) return '看跌'
      return '震荡'
    }
    
    // 获取价格差异样式
    const getDiffClass = (diff) => {
      return diff > 0 ? 'positive' : (diff < 0 ? 'negative' : '')
    }
    
    // 获取LLM预测结果
    const fetchLlmPredictionResult = async () => {
      if (!predictionResult.value || !predictionResult.value.stockCode) return
      
      try {
        // 查询该股票的最新LLM预测结果
        const response = await getLlmPredictionResult(predictionResult.value.stockCode)
        if (response.code === 200 && response.data) {
          llmPredictionResult.value = response.data
          showComparison.value = true
        } else {
          showComparison.value = false
        }
      } catch (error) {
        console.error('获取LLM预测结果失败:', error)
        showComparison.value = false
      }
    }
    
    // 监听预测结果变化，获取LLM预测结果用于比较
    watch(predictionResult, (newVal) => {
      if (newVal && newVal.stockCode) {
        fetchLlmPredictionResult()
      } else {
        showComparison.value = false
      }
    })
    
    return {
      formRef,
      formData,
      loading,
      showResult,
      predictionResult,
      predictionHistory,
      loadingHistory,
      predictionChart,
      taskId,
      taskStatus,
      taskProgress,
      taskMessage,
      autoPredictAfterSelect,
      handleStockSelect,
      formatDate,
      resetForm,
      getAccuracyClass,
      getTrendClass,
      getTrendText,
      getDiffClass,
      llmPredictionResult,
      showComparison
    }
  }
}
</script>

<style scoped>
.lstm-predict-container {
  padding: 20px;
}

h1 {
  margin-bottom: 20px;
  color: #303133;
}

.content-wrapper {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-bottom: 20px;
}

.section {
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  padding: 20px;
  margin-bottom: 20px;
}

.info-section {
  flex: 1;
  min-width: 300px;
}

.config-section {
  flex: 2;
  min-width: 400px;
}

.result-section {
  width: 100%;
}

h2 {
  font-size: 18px;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
  color: #303133;
}

.model-info {
  margin-top: 20px;
}

.info-item {
  margin-bottom: 10px;
  display: flex;
}

.label {
  width: 120px;
  color: #606266;
  font-weight: 500;
}

.value {
  color: #303133;
}

.task-progress {
  margin-top: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.task-progress h3 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 16px;
  color: #303133;
}

.task-message {
  margin-top: 10px;
  color: #606266;
}

.stock-suggestion {
  display: flex;
  justify-content: space-between;
  padding: 5px 0;
}

.stock-code {
  font-weight: bold;
  color: #303133;
}

.stock-name {
  color: #606266;
}

.model-tip {
  margin-top: 5px;
  color: #409EFF;
  font-size: 12px;
}

.history-section {
  margin-top: 30px;
}

.history-section h3 {
  font-size: 16px;
  margin-bottom: 15px;
  color: #303133;
}

.loading-message, .empty-message {
  padding: 20px 0;
  text-align: center;
  color: #909399;
}

.history-list {
  max-height: 300px;
  overflow-y: auto;
}

.history-item {
  padding: 10px;
  border-bottom: 1px solid #ebeef5;
  cursor: pointer;
  transition: background-color 0.3s;
}

.history-item:hover {
  background-color: #f5f7fa;
}

.history-stock {
  font-weight: 500;
  color: #303133;
}

.history-date {
  margin-top: 5px;
  font-size: 12px;
  color: #909399;
}

.history-accuracy {
  margin-top: 5px;
  font-size: 12px;
  font-weight: 500;
}

.history-accuracy.excellent {
  color: #67c23a;
}

.history-accuracy.good {
  color: #e6a23c;
}

.history-accuracy.poor {
  color: #f56c6c;
}

.result-info {
  padding: 15px 0;
}

.info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.prediction-date {
  color: #909399;
  font-size: 14px;
}

.chart-container {
  margin-bottom: 30px;
}

.prediction-chart {
  width: 100%;
  height: 400px;
}

.prediction-metrics {
  display: flex;
  justify-content: space-between;
  margin-bottom: 30px;
}

.metric-card {
  flex: 1;
  padding: 15px;
  text-align: center;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin: 0 10px;
}

.metric-card:first-child {
  margin-left: 0;
}

.metric-card:last-child {
  margin-right: 0;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
}

.metric-value.positive {
  color: #67c23a;
}

.metric-value.negative {
  color: #f56c6c;
}

.metric-value.neutral {
  color: #909399;
}

.metric-label {
  color: #606266;
  font-size: 14px;
}

.prediction-details {
  margin-bottom: 30px;
}

.prediction-details h3 {
  font-size: 16px;
  margin-bottom: 15px;
  color: #303133;
}

.prediction-table {
  width: 100%;
  border-collapse: collapse;
}

.prediction-table th, .prediction-table td {
  padding: 10px;
  text-align: center;
  border-bottom: 1px solid #ebeef5;
}

.prediction-table th {
  font-weight: 500;
  color: #606266;
  background-color: #f5f7fa;
}

.prediction-table td.positive {
  color: #67c23a;
}

.prediction-table td.negative {
  color: #f56c6c;
}

.analysis-summary {
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.analysis-summary h3 {
  font-size: 16px;
  margin-top: 0;
  margin-bottom: 15px;
  color: #303133;
}

.summary-content {
  color: #303133;
  line-height: 1.6;
}

.key-factors {
  margin-top: 15px;
}

.key-factors h4 {
  margin-bottom: 10px;
  color: #303133;
  font-size: 14px;
}

.key-factors ul {
  padding-left: 20px;
  margin: 0;
}

.key-factors li {
  margin-bottom: 5px;
  color: #606266;
}

.stock-search-tip {
  margin-top: 5px;
  color: #909399;
  font-size: 12px;
}

.watchlist-tag {
  background-color: #f0f0f0;
  padding: 2px 5px;
  border-radius: 4px;
  margin-left: 5px;
  color: #606266;
  font-size: 12px;
}
</style> 