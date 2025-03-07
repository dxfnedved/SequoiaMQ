<template>
  <div class="multi-strategy-page">
    <div class="page-header">
      <h2>多策略组合分析</h2>
      <p class="page-description">选择多个策略对股票进行综合分析，获取更全面的投资建议</p>
    </div>
    
    <div class="content-container">
      <div class="strategy-selection-section">
        <h3>选择策略</h3>
        <div class="strategy-selection">
          <div class="select-all">
            <el-checkbox v-model="selectAll" @change="handleSelectAllChange">全选</el-checkbox>
            <span class="selected-count">已选择 {{ selectedCount }} 个策略</span>
          </div>
          <div class="strategy-list">
            <div v-for="strategy in strategies" :key="strategy.id" class="strategy-item">
              <el-checkbox v-model="strategy.selected" @change="handleStrategyChange">{{ strategy.name }}</el-checkbox>
              <div class="strategy-description">{{ strategy.description }}</div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="analysis-config-section">
        <h3>分析配置</h3>
        <el-form :model="configForm" label-position="top">
          <el-form-item label="股票代码">
            <stock-search-input
              v-model="configForm.stockCode"
              placeholder="输入股票代码或名称"
              @select="handleSelect"
            />
          </el-form-item>
          
          <el-form-item label="周期">
            <el-select v-model="configForm.period">
              <el-option label="日线" value="daily" />
              <el-option label="周线" value="weekly" />
              <el-option label="月线" value="monthly" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="历史数据长度">
            <el-input-number v-model="configForm.dataLength" :min="60" :max="500" :step="10" />
          </el-form-item>
          
          <div v-if="hasAdvancedSettings" class="advanced-settings">
            <h4>高级参数设置</h4>
            <div v-for="strategy in selectedStrategiesWithParams" :key="strategy.id" class="strategy-params">
              <h5>{{ strategy.name }}</h5>
              <div class="params-list">
                <el-form-item v-for="(param, key) in strategy.params" :key="key" :label="param.name">
                  <el-input-number 
                    v-if="param.type === 'number'" 
                    v-model="configForm.params[strategy.id][key]" 
                    :min="param.min" 
                    :max="param.max" 
                    :step="param.step || 1" 
                  />
                  <el-select 
                    v-else-if="param.type === 'select'" 
                    v-model="configForm.params[strategy.id][key]"
                  >
                    <el-option 
                      v-for="option in param.options" 
                      :key="option.value" 
                      :label="option.label" 
                      :value="option.value" 
                    />
                  </el-select>
                  <el-input 
                    v-else 
                    v-model="configForm.params[strategy.id][key]" 
                  />
                </el-form-item>
              </div>
            </div>
          </div>
          
          <div class="form-actions">
            <el-button type="primary" :disabled="!canRunAnalysis" @click="runAnalysis" :loading="loading">
              运行分析
            </el-button>
            <el-button @click="resetConfig">重置</el-button>
          </div>
        </el-form>
      </div>
    </div>
    
    <div v-if="showResults" class="results-section">
      <h3>分析结果</h3>
      
      <el-tabs>
        <el-tab-pane label="综合评分">
          <div class="score-summary">
            <div class="score-cards">
              <div class="score-card" :class="getScoreClass(analysisResult.overallScore)">
                <div class="score-value">{{ analysisResult.overallScore }}</div>
                <div class="score-label">综合评分</div>
              </div>
              <div class="score-card" :class="getScoreClass(analysisResult.technicalScore)">
                <div class="score-value">{{ analysisResult.technicalScore }}</div>
                <div class="score-label">技术分析</div>
              </div>
              <div class="score-card" :class="getScoreClass(analysisResult.fundamentalScore)">
                <div class="score-value">{{ analysisResult.fundamentalScore }}</div>
                <div class="score-label">基本面</div>
              </div>
            </div>
            
            <div class="recommendation-container">
              <div class="recommendation" :class="getRecommendationClass(analysisResult.recommendation)">
                {{ getRecommendationText(analysisResult.recommendation) }}
              </div>
            </div>
          </div>
          
          <h4>策略评分明细</h4>
          <div class="strategy-scores">
            <div v-for="(score, index) in analysisResult.strategyScores" :key="index" class="strategy-score-item">
              <div class="strategy-name">{{ score.name }}</div>
              <el-progress :percentage="score.score" :color="getScoreColor(score.score)" :format="format => `${score.score}分`" />
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="技术指标">
          <div class="indicators">
            <div v-for="(group, groupName) in analysisResult.technicalIndicators" :key="groupName" class="indicator-group">
              <h4>{{ groupName }}</h4>
              <div class="indicator-list">
                <div v-for="(indicator, indName) in group" :key="indName" class="indicator-item">
                  <div class="indicator-name">{{ indName }}</div>
                  <div class="indicator-value" :class="getIndicatorClass(indicator)">{{ indicator.value }}</div>
                  <div class="indicator-signal" :class="getSignalClass(indicator.signal)">{{ getSignalText(indicator.signal) }}</div>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="策略分析">
          <div class="strategy-analysis">
            <div v-for="(analysis, index) in analysisResult.strategyAnalysis" :key="index" class="strategy-analysis-item">
              <h4>{{ analysis.name }}</h4>
              <div class="analysis-content">
                <p>{{ analysis.summary }}</p>
                <div class="key-points">
                  <h5>关键点</h5>
                  <ul>
                    <li v-for="(point, pointIndex) in analysis.keyPoints" :key="pointIndex">{{ point }}</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { searchStocks } from '@/api/stock'
import { runStrategyAnalysis, getStrategyParams } from '@/api/analysis'
import StockSearchInput from '@/components/StockSearchInput.vue'

export default {
  name: 'MultiStrategy',
  components: {
    StockSearchInput
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    
    // 策略列表
    const strategies = ref([
      { id: 'rsrs', name: 'RSRS择时策略', description: '基于阻力支撑相对强度的趋势跟踪策略', selected: false, params: null },
      { id: 'turtle', name: '海龟交易法则', description: '经典的趋势跟踪交易系统', selected: false, params: null },
      { id: 'low_atr', name: '低ATR策略', description: '寻找波动率较低的稳定股票', selected: false, params: null },
      { id: 'low_backtrace', name: '低回撤上涨策略', description: '寻找稳步上涨且回撤较小的股票', selected: false, params: null },
      { id: 'keep_increase', name: '持续上涨策略', description: '寻找连续上涨趋势的股票', selected: false, params: null },
      { id: 'ma250', name: '均线回踩策略', description: '寻找回踩长期均线并反弹的股票', selected: false, params: null },
      { id: 'alpha101', name: 'Alpha101因子', description: '基于WorldQuant的Alpha101因子的量化策略', selected: false, params: null },
      { id: 'alpha191', name: 'Alpha191因子', description: '基于191个量化因子的多因子策略', selected: false, params: null }
    ])
    
    // 全选状态
    const selectAll = ref(false)
    
    // 分析配置表单
    const configForm = ref({
      stockCode: '',
      stockName: '',
      period: 'daily',
      dataLength: 120,
      params: {}
    })
    
    // 初始化策略参数
    const initStrategyParams = async () => {
      try {
        const response = await getStrategyParams()
        const params = response.data
        
        strategies.value.forEach(strategy => {
          if (params[strategy.id]) {
            strategy.params = params[strategy.id]
            configForm.value.params[strategy.id] = {}
            
            // 初始化参数默认值
            Object.keys(strategy.params).forEach(key => {
              configForm.value.params[strategy.id][key] = strategy.params[key].default
            })
          }
        })
      } catch (error) {
        console.error('获取策略参数失败:', error)
      }
    }
    
    // 加载状态
    const loading = ref(false)
    
    // 分析结果
    const analysisResult = ref(null)
    const showResults = ref(false)
    
    // 初始化
    onMounted(async () => {
      await initStrategyParams()
      
      // 从URL参数中获取股票代码
      if (route.query.stock) {
        configForm.value.stockCode = route.query.stock
        // 可以在这里加载股票名称
      }
      
      // 默认选择一些策略
      strategies.value[0].selected = true // RSRS
      strategies.value[3].selected = true // 低回撤上涨
    })
    
    // 计算属性
    const selectedCount = computed(() => {
      return strategies.value.filter(s => s.selected).length
    })
    
    const selectedStrategies = computed(() => {
      return strategies.value.filter(s => s.selected)
    })
    
    const selectedStrategiesWithParams = computed(() => {
      return selectedStrategies.value.filter(s => s.params)
    })
    
    const hasAdvancedSettings = computed(() => {
      return selectedStrategiesWithParams.value.length > 0
    })
    
    const canRunAnalysis = computed(() => {
      return configForm.value.stockCode && selectedCount.value > 0
    })
    
    // 全选/取消全选
    const handleSelectAllChange = (val) => {
      strategies.value.forEach(strategy => {
        strategy.selected = val
      })
    }
    
    // 策略选择变化
    const handleStrategyChange = () => {
      selectAll.value = strategies.value.every(s => s.selected)
    }
    
    // 选择股票
    const handleSelect = (item) => {
      configForm.value.stockCode = item.code
      configForm.value.stockName = item.name
    }
    
    // 运行分析
    const runAnalysis = async () => {
      if (!canRunAnalysis.value) return
      
      loading.value = true
      
      try {
        // 准备请求数据
        const requestData = {
          stockCode: configForm.value.stockCode,
          period: configForm.value.period,
          dataLength: configForm.value.dataLength,
          strategies: selectedStrategies.value.map(s => ({
            id: s.id,
            params: configForm.value.params[s.id] || {}
          }))
        }
        
        // 调用分析API
        const response = await runStrategyAnalysis(requestData)
        analysisResult.value = response.data
        showResults.value = true
        
        // 滚动到结果区域
        setTimeout(() => {
          const resultsSection = document.querySelector('.results-section')
          if (resultsSection) {
            resultsSection.scrollIntoView({ behavior: 'smooth' })
          }
        }, 100)
      } catch (error) {
        console.error('策略分析失败:', error)
        // 显示错误提示
      } finally {
        loading.value = false
      }
    }
    
    // 重置配置
    const resetConfig = () => {
      configForm.value = {
        stockCode: '',
        stockName: '',
        period: 'daily',
        dataLength: 120,
        params: { ...configForm.value.params } // 保留参数设置
      }
    }
    
    // 评分样式
    const getScoreClass = (score) => {
      if (score >= 80) return 'excellent'
      if (score >= 60) return 'good'
      if (score >= 40) return 'neutral'
      return 'poor'
    }
    
    // 评分颜色
    const getScoreColor = (score) => {
      if (score >= 80) return '#67C23A'
      if (score >= 60) return '#E6A23C'
      if (score >= 40) return '#909399'
      return '#F56C6C'
    }
    
    // 建议样式
    const getRecommendationClass = (recommendation) => {
      const classMap = {
        'strong_buy': 'strong-buy',
        'buy': 'buy',
        'hold': 'hold',
        'sell': 'sell',
        'strong_sell': 'strong-sell'
      }
      return classMap[recommendation] || 'neutral'
    }
    
    // 建议文本
    const getRecommendationText = (recommendation) => {
      const textMap = {
        'strong_buy': '强烈推荐买入',
        'buy': '建议买入',
        'hold': '建议持有',
        'sell': '建议卖出',
        'strong_sell': '强烈建议卖出'
      }
      return textMap[recommendation] || '中性'
    }
    
    // 指标样式
    const getIndicatorClass = (indicator) => {
      return indicator.signal === 'positive' ? 'positive' : 
             indicator.signal === 'negative' ? 'negative' : 'neutral'
    }
    
    // 信号样式
    const getSignalClass = (signal) => {
      return signal === 'positive' ? 'positive' : 
             signal === 'negative' ? 'negative' : 'neutral'
    }
    
    // 信号文本
    const getSignalText = (signal) => {
      const textMap = {
        'positive': '看涨',
        'negative': '看跌',
        'neutral': '中性'
      }
      return textMap[signal] || '未知'
    }
    
    return {
      strategies,
      selectAll,
      configForm,
      loading,
      analysisResult,
      showResults,
      selectedCount,
      selectedStrategies,
      selectedStrategiesWithParams,
      hasAdvancedSettings,
      canRunAnalysis,
      handleSelectAllChange,
      handleStrategyChange,
      handleSelect,
      runAnalysis,
      resetConfig,
      getScoreClass,
      getScoreColor,
      getRecommendationClass,
      getRecommendationText,
      getIndicatorClass,
      getSignalClass,
      getSignalText
    }
  }
}
</script>

<style lang="scss" scoped>
.multi-strategy-page {
  padding: 20px;
  
  @media (max-width: $sm) {
    padding: 10px;
  }
}

.page-header {
  margin-bottom: 20px;
  
  h2 {
    font-size: 24px;
    margin-bottom: 8px;
    
    @media (max-width: $sm) {
      font-size: 20px;
    }
  }
  
  .page-description {
    color: #606266;
    font-size: 14px;
    
    @media (max-width: $sm) {
      font-size: 12px;
    }
  }
}

.content-container {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  
  @media (max-width: $md) {
    flex-direction: column;
  }
}

.strategy-selection-section, 
.analysis-config-section {
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  padding: 20px;
  
  @media (max-width: $sm) {
    padding: 15px;
  }
}

.strategy-selection-section {
  flex: 1;
  min-width: 300px;
  
  @media (max-width: $md) {
    width: 100%;
  }
}

.analysis-config-section {
  flex: 1;
  min-width: 300px;
  
  @media (max-width: $md) {
    width: 100%;
  }
}

.strategy-selection {
  margin-top: 15px;
}

.select-all {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  
  @media (max-width: $sm) {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
}

.selected-count {
  color: #409EFF;
  font-weight: 500;
}

.strategy-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 15px;
  
  @media (max-width: $sm) {
    grid-template-columns: 1fr;
  }
}

.strategy-item {
  padding: 10px;
  border: 1px solid #EBEEF5;
  border-radius: 4px;
  transition: all 0.3s;
  
  &:hover {
    border-color: #C0C4CC;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  }
}

.strategy-description {
  margin-top: 5px;
  color: #909399;
  font-size: 12px;
}

.advanced-settings {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #EBEEF5;
  
  h4 {
    margin-bottom: 15px;
  }
}

.strategy-params {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #F5F7FA;
  border-radius: 4px;
  
  h5 {
    margin-top: 0;
    margin-bottom: 10px;
  }
}

.params-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
  
  @media (max-width: $sm) {
    grid-template-columns: 1fr;
  }
}

.form-actions {
  margin-top: 20px;
  display: flex;
  gap: 10px;
  
  @media (max-width: $sm) {
    flex-direction: column;
    
    .el-button {
      width: 100%;
    }
  }
}

.results-section {
  margin-top: 30px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  padding: 20px;
  
  @media (max-width: $sm) {
    padding: 15px;
    margin-top: 20px;
  }
  
  h3 {
    margin-top: 0;
    margin-bottom: 20px;
    
    @media (max-width: $sm) {
      font-size: 16px;
    }
  }
}

.score-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-bottom: 20px;
  
  @media (max-width: $sm) {
    flex-direction: column;
    gap: 10px;
  }
}

.score-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  flex: 3;
  
  @media (max-width: $md) {
    flex-direction: column;
  }
}

.recommendation-container {
  flex: 2;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  
  @media (max-width: $md) {
    margin-top: 15px;
  }
}

.score-card {
  flex: 1;
  min-width: 120px;
  padding: 15px;
  border-radius: 4px;
  text-align: center;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  
  @media (max-width: $sm) {
    min-width: 100px;
    padding: 10px;
  }
}

.score-card.excellent {
  background-color: rgba(103, 194, 58, 0.1);
  color: #67c23a;
  border: 2px solid #67c23a;
}

.score-card.good {
  background-color: rgba(230, 162, 60, 0.1);
  color: #e6a23c;
  border: 2px solid #e6a23c;
}

.score-card.neutral {
  background-color: rgba(144, 147, 153, 0.1);
  color: #909399;
  border: 2px solid #909399;
}

.score-card.poor {
  background-color: rgba(245, 108, 108, 0.1);
  color: #f56c6c;
  border: 2px solid #f56c6c;
}

.score-value {
  font-size: 24px;
  font-weight: bold;
  
  @media (max-width: $sm) {
    font-size: 20px;
  }
}

.score-label {
  font-size: 14px;
  margin-top: 5px;
  
  @media (max-width: $sm) {
    font-size: 12px;
  }
}

.recommendation {
  font-size: 24px;
  font-weight: bold;
  padding: 10px 20px;
  border-radius: 4px;
  
  @media (max-width: $sm) {
    font-size: 18px;
    padding: 8px 15px;
  }
}

.recommendation.strong-buy {
  background-color: rgba(103, 194, 58, 0.1);
  color: #67c23a;
}

.recommendation.buy {
  background-color: rgba(144, 202, 100, 0.1);
  color: #90ca64;
}

.recommendation.hold {
  background-color: rgba(144, 147, 153, 0.1);
  color: #909399;
}

.recommendation.sell {
  background-color: rgba(230, 162, 60, 0.1);
  color: #e6a23c;
}

.recommendation.strong-sell {
  background-color: rgba(245, 108, 108, 0.1);
  color: #f56c6c;
}

.strategy-scores {
  margin-top: 20px;
}

.strategy-score-item {
  margin-bottom: 15px;
}

.strategy-name {
  margin-bottom: 5px;
  font-weight: 500;
}

.indicators {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  
  @media (max-width: $md) {
    flex-direction: column;
    gap: 15px;
  }
}

.indicator-group {
  flex: 1;
  min-width: 300px;
  
  @media (max-width: $md) {
    min-width: 100%;
  }
}

.indicator-list {
  margin-top: 10px;
}

.indicator-item {
  display: flex;
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
  
  @media (max-width: $sm) {
    flex-wrap: wrap;
  }
}

.indicator-name {
  flex: 2;
  color: #606266;
  
  @media (max-width: $sm) {
    flex: 1 0 100%;
    margin-bottom: 5px;
  }
}

.indicator-value {
  flex: 1;
  text-align: right;
  font-weight: 500;
  
  @media (max-width: $sm) {
    flex: 1;
    text-align: left;
  }
}

.indicator-signal {
  flex: 1;
  text-align: right;
  border-radius: 2px;
  padding: 0 8px;
  
  @media (max-width: $sm) {
    flex: 1;
    text-align: right;
  }
}

.indicator-value.positive, .indicator-signal.positive {
  color: #67c23a;
}

.indicator-value.negative, .indicator-signal.negative {
  color: #f56c6c;
}

.indicator-value.neutral, .indicator-signal.neutral {
  color: #909399;
}

.strategy-analysis {
  margin-top: 10px;
}

.strategy-analysis-item {
  margin-bottom: 25px;
  padding-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
}

.strategy-analysis-item:last-child {
  border-bottom: none;
}

.key-points {
  margin-top: 15px;
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  
  @media (max-width: $sm) {
    padding: 10px;
  }
}

.key-points h5 {
  margin-top: 0;
  margin-bottom: 10px;
  color: #303133;
  
  @media (max-width: $sm) {
    font-size: 14px;
  }
}

.key-points ul {
  margin: 0;
  padding-left: 20px;
  
  @media (max-width: $sm) {
    padding-left: 15px;
  }
}

.key-points li {
  margin-bottom: 5px;
  color: #606266;
  
  @media (max-width: $sm) {
    font-size: 13px;
  }
}

// 暗色模式适配
.dark-mode {
  .strategy-selection-section, 
  .analysis-config-section,
  .results-section {
    background-color: #1f1f1f;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.3);
  }
  
  .page-description {
    color: #a3a6ad;
  }
  
  .strategy-item {
    border-color: #363b4d;
    
    &:hover {
      border-color: #4c5269;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
    }
  }
  
  .strategy-description {
    color: #a3a6ad;
  }
  
  .advanced-settings {
    border-top-color: #363b4d;
  }
  
  .strategy-params {
    background-color: #262626;
  }
  
  .indicator-item {
    border-bottom-color: #363b4d;
  }
  
  .indicator-name {
    color: #a3a6ad;
  }
  
  .key-points {
    background-color: #262626;
    
    h5 {
      color: #e5eaf3;
    }
    
    li {
      color: #a3a6ad;
    }
  }
  
  .strategy-analysis-item {
    border-bottom-color: #363b4d;
  }
}
</style> 