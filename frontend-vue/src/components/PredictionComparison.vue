<!-- 预测结果比较组件 -->
<template>
  <div class="prediction-comparison">
    <div class="comparison-header">
      <h3>预测结果比较</h3>
      <p class="comparison-description">比较不同模型的预测结果，帮助您做出更准确的投资决策</p>
    </div>
    
    <div class="comparison-content">
      <el-tabs v-model="activeTab" class="comparison-tabs">
        <el-tab-pane label="图表比较" name="chart">
          <div class="chart-container" ref="chartContainer"></div>
        </el-tab-pane>
        
        <el-tab-pane label="指标比较" name="metrics">
          <div class="metrics-comparison">
            <div class="metrics-header">
              <div class="metric-name">指标</div>
              <div class="model-name">LSTM模型</div>
              <div class="model-name">LLM模型</div>
              <div class="difference">差异</div>
            </div>
            
            <div class="metrics-body">
              <div v-for="(metric, index) in comparisonMetrics" :key="index" class="metric-row">
                <div class="metric-name">{{ metric.name }}</div>
                <div class="model-value" :class="getValueClass(metric.lstm)">{{ formatValue(metric.lstm, metric.format) }}</div>
                <div class="model-value" :class="getValueClass(metric.llm)">{{ formatValue(metric.llm, metric.format) }}</div>
                <div class="difference" :class="getDifferenceClass(metric.difference)">
                  {{ formatDifference(metric.difference, metric.format) }}
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="预测详情" name="details">
          <div class="prediction-details">
            <div class="model-details">
              <h4>LSTM模型预测</h4>
              <div class="detail-content">
                <div class="detail-item" v-for="(detail, key) in lstmDetails" :key="key">
                  <div class="detail-label">{{ getDetailLabel(key) }}</div>
                  <div class="detail-value" :class="getDetailValueClass(key, detail)">{{ formatDetailValue(key, detail) }}</div>
                </div>
              </div>
            </div>
            
            <div class="model-details">
              <h4>LLM模型预测</h4>
              <div class="detail-content">
                <div class="detail-item" v-for="(detail, key) in llmDetails" :key="key">
                  <div class="detail-label">{{ getDetailLabel(key) }}</div>
                  <div class="detail-value" :class="getDetailValueClass(key, detail)">{{ formatDetailValue(key, detail) }}</div>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
    
    <div class="comparison-actions">
      <el-button type="primary" @click="exportComparison">导出比较结果</el-button>
      <el-button @click="refreshData">刷新数据</el-button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { 
  TitleComponent, 
  TooltipComponent, 
  LegendComponent, 
  GridComponent,
  DataZoomComponent,
  MarkLineComponent,
  MarkPointComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

// 注册必要的组件
echarts.use([
  TitleComponent, 
  TooltipComponent, 
  LegendComponent, 
  GridComponent,
  DataZoomComponent,
  MarkLineComponent,
  MarkPointComponent,
  LineChart,
  CanvasRenderer
])

export default {
  name: 'PredictionComparison',
  props: {
    // LSTM预测结果
    lstmResult: {
      type: Object,
      default: () => ({})
    },
    // LLM预测结果
    llmResult: {
      type: Object,
      default: () => ({})
    },
    // 股票信息
    stockInfo: {
      type: Object,
      default: () => ({})
    }
  },
  setup(props) {
    // 当前激活的标签页
    const activeTab = ref('chart')
    // 图表容器引用
    const chartContainer = ref(null)
    // 图表实例
    let chartInstance = null
    
    // 计算比较指标
    const comparisonMetrics = computed(() => {
      if (!props.lstmResult || !props.llmResult) return []
      
      return [
        {
          name: '预测准确率',
          lstm: props.lstmResult.accuracy || 0,
          llm: props.llmResult.accuracy || 0,
          difference: (props.lstmResult.accuracy || 0) - (props.llmResult.accuracy || 0),
          format: 'percentage'
        },
        {
          name: '预测趋势',
          lstm: props.lstmResult.trend || 'neutral',
          llm: props.llmResult.trend || 'neutral',
          difference: compareTrends(props.lstmResult.trend, props.llmResult.trend),
          format: 'trend'
        },
        {
          name: '预测置信度',
          lstm: props.lstmResult.confidence || 0,
          llm: props.llmResult.confidence || 0,
          difference: (props.lstmResult.confidence || 0) - (props.llmResult.confidence || 0),
          format: 'percentage'
        },
        {
          name: '预测价格变化',
          lstm: props.lstmResult.priceChange || 0,
          llm: props.llmResult.priceChange || 0,
          difference: (props.lstmResult.priceChange || 0) - (props.llmResult.priceChange || 0),
          format: 'percentage'
        },
        {
          name: '预测时间范围',
          lstm: props.lstmResult.timeRange || 0,
          llm: props.llmResult.timeRange || 0,
          difference: (props.lstmResult.timeRange || 0) - (props.llmResult.timeRange || 0),
          format: 'days'
        }
      ]
    })
    
    // LSTM详情
    const lstmDetails = computed(() => {
      return props.lstmResult || {}
    })
    
    // LLM详情
    const llmDetails = computed(() => {
      return props.llmResult || {}
    })
    
    // 比较趋势
    const compareTrends = (trend1, trend2) => {
      const trendMap = {
        'up': 2,
        'neutral': 1,
        'down': 0
      }
      
      return trendMap[trend1] - trendMap[trend2]
    }
    
    // 格式化值
    const formatValue = (value, format) => {
      if (format === 'percentage') {
        return `${(value * 100).toFixed(2)}%`
      } else if (format === 'trend') {
        const trendText = {
          'up': '上涨',
          'neutral': '中性',
          'down': '下跌'
        }
        return trendText[value] || '未知'
      } else if (format === 'days') {
        return `${value}天`
      }
      return value
    }
    
    // 格式化差异
    const formatDifference = (difference, format) => {
      if (format === 'percentage') {
        return difference > 0 ? `+${(difference * 100).toFixed(2)}%` : `${(difference * 100).toFixed(2)}%`
      } else if (format === 'trend') {
        if (difference === 0) return '一致'
        return difference > 0 ? 'LSTM更乐观' : 'LLM更乐观'
      } else if (format === 'days') {
        return difference > 0 ? `+${difference}天` : `${difference}天`
      }
      return difference > 0 ? `+${difference}` : `${difference}`
    }
    
    // 获取值的样式类
    const getValueClass = (value) => {
      if (typeof value === 'number') {
        return value > 0 ? 'positive' : value < 0 ? 'negative' : 'neutral'
      } else if (typeof value === 'string') {
        return value === 'up' ? 'positive' : value === 'down' ? 'negative' : 'neutral'
      }
      return 'neutral'
    }
    
    // 获取差异的样式类
    const getDifferenceClass = (difference) => {
      if (typeof difference === 'number') {
        return difference > 0 ? 'positive' : difference < 0 ? 'negative' : 'neutral'
      }
      return 'neutral'
    }
    
    // 获取详情标签
    const getDetailLabel = (key) => {
      const labelMap = {
        'accuracy': '准确率',
        'trend': '趋势',
        'confidence': '置信度',
        'priceChange': '价格变化',
        'timeRange': '时间范围',
        'predictedPrice': '预测价格',
        'predictedDate': '预测日期',
        'method': '预测方法',
        'modelVersion': '模型版本'
      }
      return labelMap[key] || key
    }
    
    // 获取详情值的样式类
    const getDetailValueClass = (key, value) => {
      if (key === 'trend') {
        return value === 'up' ? 'positive' : value === 'down' ? 'negative' : 'neutral'
      } else if (key === 'priceChange' || key === 'accuracy' || key === 'confidence') {
        return value > 0 ? 'positive' : value < 0 ? 'negative' : 'neutral'
      }
      return ''
    }
    
    // 格式化详情值
    const formatDetailValue = (key, value) => {
      if (key === 'accuracy' || key === 'confidence') {
        return `${(value * 100).toFixed(2)}%`
      } else if (key === 'trend') {
        const trendText = {
          'up': '上涨',
          'neutral': '中性',
          'down': '下跌'
        }
        return trendText[value] || '未知'
      } else if (key === 'priceChange') {
        return value > 0 ? `+${(value * 100).toFixed(2)}%` : `${(value * 100).toFixed(2)}%`
      } else if (key === 'timeRange') {
        return `${value}天`
      } else if (key === 'predictedPrice') {
        return `¥${value.toFixed(2)}`
      } else if (key === 'predictedDate') {
        return new Date(value).toLocaleDateString()
      }
      return value
    }
    
    // 初始化图表
    const initChart = () => {
      if (!chartContainer.value) return
      
      // 创建图表实例
      chartInstance = echarts.init(chartContainer.value)
      
      // 更新图表
      updateChart()
      
      // 监听窗口大小变化
      window.addEventListener('resize', () => {
        chartInstance.resize()
      })
    }
    
    // 更新图表
    const updateChart = () => {
      if (!chartInstance) return
      
      const option = {
        title: {
          text: `${props.stockInfo.name || ''} (${props.stockInfo.code || ''}) 预测比较`,
          left: 'center'
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross',
            label: {
              backgroundColor: '#6a7985'
            }
          }
        },
        legend: {
          data: ['历史价格', 'LSTM预测', 'LLM预测'],
          bottom: 10
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '15%',
          top: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: generateDateArray()
        },
        yAxis: {
          type: 'value',
          name: '价格',
          axisLabel: {
            formatter: '{value} ¥'
          }
        },
        dataZoom: [
          {
            type: 'inside',
            start: 50,
            end: 100
          },
          {
            start: 50,
            end: 100
          }
        ],
        series: [
          {
            name: '历史价格',
            type: 'line',
            data: generateHistoricalData(),
            symbol: 'none',
            lineStyle: {
              width: 2
            }
          },
          {
            name: 'LSTM预测',
            type: 'line',
            data: generateLstmData(),
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: {
              width: 2,
              type: 'dashed'
            },
            markPoint: {
              data: [
                { type: 'max', name: '最高点' },
                { type: 'min', name: '最低点' }
              ]
            }
          },
          {
            name: 'LLM预测',
            type: 'line',
            data: generateLlmData(),
            symbol: 'triangle',
            symbolSize: 6,
            lineStyle: {
              width: 2,
              type: 'dotted'
            },
            markPoint: {
              data: [
                { type: 'max', name: '最高点' },
                { type: 'min', name: '最低点' }
              ]
            }
          }
        ]
      }
      
      // 设置图表选项
      chartInstance.setOption(option)
    }
    
    // 生成日期数组
    const generateDateArray = () => {
      const dates = []
      const today = new Date()
      
      // 历史日期
      for (let i = 30; i >= 1; i--) {
        const date = new Date(today)
        date.setDate(today.getDate() - i)
        dates.push(date.toLocaleDateString())
      }
      
      // 当前日期
      dates.push(today.toLocaleDateString())
      
      // 未来日期
      for (let i = 1; i <= 10; i++) {
        const date = new Date(today)
        date.setDate(today.getDate() + i)
        dates.push(date.toLocaleDateString())
      }
      
      return dates
    }
    
    // 生成历史数据
    const generateHistoricalData = () => {
      // 这里应该使用实际的历史数据
      // 为了演示，我们生成一些随机数据
      const data = []
      const basePrice = 100
      
      for (let i = 0; i < 31; i++) {
        data.push(basePrice + Math.random() * 10 - 5)
      }
      
      // 未来日期没有历史数据
      for (let i = 0; i < 10; i++) {
        data.push(null)
      }
      
      return data
    }
    
    // 生成LSTM预测数据
    const generateLstmData = () => {
      // 这里应该使用实际的LSTM预测数据
      // 为了演示，我们生成一些随机数据
      const data = []
      const basePrice = 100
      
      // 历史日期没有预测数据
      for (let i = 0; i < 30; i++) {
        data.push(null)
      }
      
      // 当前日期和未来日期的预测
      for (let i = 0; i < 11; i++) {
        const trend = props.lstmResult.trend || 'neutral'
        const factor = trend === 'up' ? 1 : trend === 'down' ? -1 : 0
        data.push(basePrice + factor * i * 2 + Math.random() * 4 - 2)
      }
      
      return data
    }
    
    // 生成LLM预测数据
    const generateLlmData = () => {
      // 这里应该使用实际的LLM预测数据
      // 为了演示，我们生成一些随机数据
      const data = []
      const basePrice = 100
      
      // 历史日期没有预测数据
      for (let i = 0; i < 30; i++) {
        data.push(null)
      }
      
      // 当前日期和未来日期的预测
      for (let i = 0; i < 11; i++) {
        const trend = props.llmResult.trend || 'neutral'
        const factor = trend === 'up' ? 1 : trend === 'down' ? -1 : 0
        data.push(basePrice + factor * i * 1.5 + Math.random() * 3 - 1.5)
      }
      
      return data
    }
    
    // 导出比较结果
    const exportComparison = () => {
      // 实现导出功能
      console.log('导出比较结果')
    }
    
    // 刷新数据
    const refreshData = () => {
      // 实现刷新功能
      console.log('刷新数据')
    }
    
    // 监听结果变化
    watch([() => props.lstmResult, () => props.llmResult], () => {
      updateChart()
    })
    
    // 组件挂载后初始化图表
    onMounted(() => {
      initChart()
    })
    
    return {
      activeTab,
      chartContainer,
      comparisonMetrics,
      lstmDetails,
      llmDetails,
      formatValue,
      formatDifference,
      getValueClass,
      getDifferenceClass,
      getDetailLabel,
      getDetailValueClass,
      formatDetailValue,
      exportComparison,
      refreshData
    }
  }
}
</script>

<style lang="scss" scoped>
.prediction-comparison {
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  padding: 20px;
  margin-bottom: 20px;
  
  @media (max-width: $sm) {
    padding: 15px;
  }
}

.comparison-header {
  margin-bottom: 20px;
  
  h3 {
    font-size: 18px;
    margin-bottom: 8px;
    
    @media (max-width: $sm) {
      font-size: 16px;
    }
  }
  
  .comparison-description {
    color: #606266;
    font-size: 14px;
    
    @media (max-width: $sm) {
      font-size: 12px;
    }
  }
}

.chart-container {
  height: 400px;
  width: 100%;
  
  @media (max-width: $md) {
    height: 300px;
  }
  
  @media (max-width: $sm) {
    height: 250px;
  }
}

.metrics-comparison {
  width: 100%;
  border: 1px solid #EBEEF5;
  border-radius: 4px;
  overflow: hidden;
}

.metrics-header {
  display: flex;
  background-color: #F5F7FA;
  padding: 12px 15px;
  font-weight: bold;
  border-bottom: 1px solid #EBEEF5;
  
  @media (max-width: $sm) {
    padding: 10px;
  }
}

.metrics-body {
  .metric-row {
    display: flex;
    padding: 12px 15px;
    border-bottom: 1px solid #EBEEF5;
    
    &:last-child {
      border-bottom: none;
    }
    
    @media (max-width: $sm) {
      padding: 10px;
    }
  }
}

.metric-name, .model-name, .model-value, .difference {
  flex: 1;
  
  @media (max-width: $sm) {
    font-size: 13px;
  }
}

.metric-name {
  flex: 1.5;
  font-weight: 500;
}

.positive {
  color: #67C23A;
}

.negative {
  color: #F56C6C;
}

.neutral {
  color: #909399;
}

.prediction-details {
  display: flex;
  gap: 20px;
  
  @media (max-width: $md) {
    flex-direction: column;
  }
}

.model-details {
  flex: 1;
  border: 1px solid #EBEEF5;
  border-radius: 4px;
  overflow: hidden;
  
  h4 {
    margin: 0;
    padding: 12px 15px;
    background-color: #F5F7FA;
    border-bottom: 1px solid #EBEEF5;
    
    @media (max-width: $sm) {
      padding: 10px;
      font-size: 14px;
    }
  }
  
  .detail-content {
    padding: 15px;
    
    @media (max-width: $sm) {
      padding: 10px;
    }
  }
  
  .detail-item {
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    @media (max-width: $sm) {
      font-size: 13px;
    }
  }
  
  .detail-label {
    color: #606266;
  }
  
  .detail-value {
    font-weight: 500;
  }
}

.comparison-actions {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  
  @media (max-width: $sm) {
    flex-direction: column;
    
    .el-button {
      width: 100%;
    }
  }
}

// 暗色模式适配
.dark-mode {
  .prediction-comparison {
    background-color: #1f1f1f;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.3);
  }
  
  .comparison-description {
    color: #a3a6ad;
  }
  
  .metrics-comparison {
    border-color: #363b4d;
  }
  
  .metrics-header {
    background-color: #262626;
    border-bottom-color: #363b4d;
  }
  
  .metrics-body .metric-row {
    border-bottom-color: #363b4d;
  }
  
  .model-details {
    border-color: #363b4d;
    
    h4 {
      background-color: #262626;
      border-bottom-color: #363b4d;
    }
    
    .detail-label {
      color: #a3a6ad;
    }
  }
}
</style> 