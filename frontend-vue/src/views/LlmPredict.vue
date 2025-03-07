<template>
  <div class="llm-predict-container">
    <h1>LLM大模型分析</h1>
    <div class="content-wrapper">
      <div class="section info-section">
        <h2>LLM模型信息</h2>
        <div class="model-info">
          <div class="info-item">
            <span class="label">模型:</span>
            <span class="value">DeepSeek-Chat</span>
          </div>
          <div class="info-item">
            <span class="label">数据来源:</span>
            <span class="value">财经新闻, 技术指标, K线数据</span>
          </div>
          <div class="info-item">
            <span class="label">分析能力:</span>
            <span class="value">市场情绪, 趋势分析, 风险评估</span>
          </div>
        </div>
      </div>
      
      <div class="section config-section">
        <h2>大模型分析配置</h2>
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
            
            <el-form-item label="数据源选择">
              <el-checkbox v-model="formData.config.includeTechnical">技术指标</el-checkbox>
              <el-checkbox v-model="formData.config.includeNews">新闻资讯</el-checkbox>
              <el-checkbox v-model="formData.config.includeFinancial">财务数据</el-checkbox>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="startPrediction" :loading="loading" :disabled="!formData.stockCode">
                开始分析
              </el-button>
              <el-button @click="resetForm">重置</el-button>
            </el-form-item>
          </el-form>
          
          <!-- 任务进度条 -->
          <div v-if="taskId" class="task-progress">
            <h3>分析进度</h3>
            <el-progress 
              :percentage="taskProgress" 
              :status="taskStatus === 'error' ? 'exception' : (taskStatus === 'completed' ? 'success' : '')"
            />
            <p class="task-message">{{ taskMessage }}</p>
          </div>
        </div>
      </div>
      
      <!-- 分析结果展示 -->
      <div v-if="showResult && predictionResult" class="section result-section">
        <h2>分析结果</h2>
        <div class="result-info">
          <div class="info-header">
            <div>
              <span class="stock-code">{{ predictionResult.code }}</span>
              <span class="stock-name">{{ predictionResult.name }}</span>
            </div>
            <div class="analysis-date">
              分析日期: {{ formatDate(predictionResult.date) }}
            </div>
          </div>
          
          <div v-if="predictionResult.analysis" class="analysis-content">
            <div class="trend-box" :class="getTrendClass(predictionResult.analysis.trend)">
              <span class="trend-label">趋势:</span>
              <span class="trend-value">{{ getTrendText(predictionResult.analysis.trend) }}</span>
            </div>
            
            <div class="recommendation-box">
              <span class="recommendation-label">建议:</span>
              <span class="recommendation-value">{{ predictionResult.analysis.recommendation }}</span>
            </div>
            
            <div class="summary-box">
              <h4>分析摘要</h4>
              <p>{{ predictionResult.analysis.summary }}</p>
            </div>
            
            <div class="factors-box">
              <h4>影响因素</h4>
              <ul>
                <li v-for="(factor, index) in predictionResult.analysis.factors" :key="index">
                  {{ factor }}
                </li>
              </ul>
            </div>
          </div>
          
          <div class="price-prediction">
            <h4>价格预测</h4>
            <div class="prediction-chart">
              <!-- 这里可以添加图表组件 -->
              <table class="prediction-table">
                <thead>
                  <tr>
                    <th>日期</th>
                    <th>预测价格</th>
                    <th>信心度</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(pred, index) in predictionResult.predictions" :key="index">
                    <td>{{ pred.date }}</td>
                    <td>{{ pred.price.toFixed(2) }}</td>
                    <td>{{ (pred.confidence * 100).toFixed(0) }}%</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { searchStocks, getStockInfo } from '@/api/stock'
import { fetchWatchlist } from '@/api/watchlist'
import { requestLlmAnalysis, getLlmAnalysisResult } from '@/api/prediction'
import StockSearchInput from '@/components/StockSearchInput.vue'

export default {
  name: 'LlmPredict',
  components: {
    StockSearchInput
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const formRef = ref(null)
    
    const formData = reactive({
      stockCode: '',
      stockName: '',
      config: {
        includeTechnical: true,
        includeNews: true,
        includeFinancial: false
      }
    })
    
    const loading = ref(false)
    const searching = ref(false)
    const showResult = ref(false)
    const predictionResult = ref(null)
    const taskId = ref('')
    const taskStatus = ref('')
    const taskProgress = ref(0)
    const taskMessage = ref('')
    const pollTimer = ref(null)
    
    const autoAnalyzeAfterSelect = ref(true)
    
    const formatDate = (dateString) => {
      const date = new Date(dateString)
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
    }
    
    const handleStockSelect = (item) => {
      formData.stockCode = item.code
      formData.stockName = item.name
      
      if (item.isWatchlist) {
        console.log('从自选股中选择了股票:', item.code)
      }
      
      if (autoAnalyzeAfterSelect.value) {
        startPrediction()
      }
    }
    
    const handleKeyDown = (event) => {
      if (event.key === 'Enter' && formData.stockCode && formData.stockName) {
        startPrediction()
      }
    }
    
    const startPrediction = async () => {
      if (!formData.stockCode) {
        ElMessage.warning('请先选择股票')
        return
      }
      
      loading.value = true
      
      try {
        const requestData = {
          stockCode: formData.stockCode,
          config: formData.config
        }
        
        const response = await requestLlmAnalysis(requestData)
        taskId.value = response.data.taskId
        
        taskStatus.value = 'processing'
        taskProgress.value = 0
        taskMessage.value = '正在准备数据...'
        
        pollTaskStatus()
      } catch (error) {
        console.error('提交分析任务失败:', error)
        ElMessage.error('提交分析任务失败，请稍后重试')
        loading.value = false
      }
    }
    
    const pollTaskStatus = async () => {
      if (!taskId.value) return
      
      try {
        const response = await getLlmAnalysisResult(taskId.value)
        
        if (response.code === 200) {
          if (response.data.status === 'completed') {
            taskStatus.value = 'completed'
            taskProgress.value = 100
            taskMessage.value = '分析完成'
            loading.value = false
            
            predictionResult.value = response.data
            showResult.value = true
          } else if (response.data.status === 'processing') {
            taskStatus.value = 'processing'
            taskProgress.value = response.data.progress || 0
            taskMessage.value = response.data.message || '正在分析...'
            
            pollTimer.value = setTimeout(pollTaskStatus, 2000)
          } else if (response.data.status === 'error') {
            taskStatus.value = 'error'
            taskMessage.value = response.data.message || '分析失败'
            loading.value = false
            ElMessage.error('分析失败: ' + response.data.message)
          }
        } else {
          throw new Error('获取任务状态失败')
        }
      } catch (error) {
        console.error('获取任务状态失败:', error)
        taskStatus.value = 'error'
        taskMessage.value = '获取任务状态失败'
        loading.value = false
        ElMessage.error('获取任务状态失败，请稍后重试')
      }
    }
    
    const resetForm = () => {
      formData.stockCode = ''
      formData.stockName = ''
      formData.config.includeTechnical = true
      formData.config.includeNews = true
      formData.config.includeFinancial = false
      
      showResult.value = false
      predictionResult.value = null
      taskId.value = ''
      taskStatus.value = ''
      taskProgress.value = 0
      taskMessage.value = ''
      
      if (pollTimer.value) {
        clearTimeout(pollTimer.value)
      }
    }
    
    const getTrendClass = (trend) => {
      if (trend === 'up' || trend === 'strong_up') {
        return 'trend-up'
      } else if (trend === 'down' || trend === 'strong_down') {
        return 'trend-down'
      } else {
        return 'trend-neutral'
      }
    }
    
    const getTrendText = (trend) => {
      const trendMap = {
        'strong_up': '强烈看涨',
        'up': '看涨',
        'neutral': '中性',
        'down': '看跌',
        'strong_down': '强烈看跌'
      }
      return trendMap[trend] || '未知'
    }
    
    onMounted(async () => {
      window.addEventListener('keydown', handleKeyDown)
      
      const { stockCode } = route.query
      if (stockCode) {
        formData.stockCode = stockCode
        try {
          const response = await getStockInfo(stockCode)
          if (response.code === 200 && response.data) {
            formData.stockName = response.data.name
            if (autoAnalyzeAfterSelect.value) {
              startPrediction()
            }
          }
        } catch (error) {
          console.error('获取股票信息失败:', error)
        }
      }
    })
    
    onBeforeUnmount(() => {
      window.removeEventListener('keydown', handleKeyDown)
      if (pollTimer.value) {
        clearTimeout(pollTimer.value)
      }
    })
    
    return {
      formRef,
      formData,
      loading,
      searching,
      showResult,
      predictionResult,
      taskId,
      taskStatus,
      taskProgress,
      taskMessage,
      handleStockSelect,
      startPrediction,
      resetForm,
      formatDate,
      getTrendClass,
      getTrendText
    }
  }
}
</script>

<style scoped>
.llm-predict-container {
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
}

.section {
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  padding: 20px;
  margin-bottom: 20px;
  width: 100%;
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
  flex: 1 0 100%;
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

.form-wrapper {
  padding: 10px 0;
}

.stock-suggestion {
  display: flex;
  align-items: center;
  padding: 8px 0;
}

.stock-suggestion span {
  margin-right: 10px;
}

.watchlist-tag {
  background-color: #409EFF;
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}

.task-progress {
  margin-top: 20px;
  padding: 15px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.task-message {
  margin-top: 10px;
  color: #606266;
}

.result-info {
  margin-top: 15px;
}

.info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.stock-code {
  font-size: 18px;
  font-weight: bold;
  margin-right: 10px;
}

.stock-name {
  font-size: 16px;
  color: #606266;
}

.analysis-date {
  color: #909399;
  font-size: 14px;
}

.analysis-content {
  padding: 15px;
  background-color: #f9fafc;
  border-radius: 4px;
  margin-bottom: 20px;
}

.trend-box, .recommendation-box {
  display: inline-flex;
  align-items: center;
  margin-right: 20px;
  margin-bottom: 15px;
  padding: 6px 12px;
  border-radius: 4px;
  background-color: #f0f2f5;
}

.trend-bullish {
  background-color: rgba(103, 194, 58, 0.1);
  color: #67c23a;
}

.trend-bearish {
  background-color: rgba(245, 108, 108, 0.1);
  color: #f56c6c;
}

.trend-neutral {
  background-color: rgba(144, 147, 153, 0.1);
  color: #909399;
}

.trend-label, .recommendation-label {
  font-weight: 500;
  margin-right: 5px;
}

.summary-box, .factors-box {
  margin-top: 15px;
}

.summary-box h4, .factors-box h4, .price-prediction h4 {
  font-size: 16px;
  margin-bottom: 10px;
  color: #303133;
}

.factors-box ul {
  padding-left: 20px;
}

.factors-box li {
  margin-bottom: 5px;
}

.price-prediction {
  margin-top: 20px;
}

.prediction-chart {
  margin-top: 15px;
}

.prediction-table {
  width: 100%;
  border-collapse: collapse;
}

.prediction-table th, .prediction-table td {
  border: 1px solid #ebeef5;
  padding: 8px 12px;
  text-align: center;
}

.prediction-table th {
  background-color: #f5f7fa;
  color: #606266;
}

.prediction-table tr:nth-child(even) {
  background-color: #fafafa;
}
</style> 