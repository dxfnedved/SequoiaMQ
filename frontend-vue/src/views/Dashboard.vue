<!-- 
  仪表盘/概览组件 
  显示系统状态、最新分析结果和推荐股票等信息
-->
<template>
  <div class="dashboard-container page-container">
    <header class="dashboard-header">
      <div class="welcome-section">
        <h1 class="welcome-title">欢迎使用 SequoiaMQ</h1>
        <p class="welcome-subtitle">智能量化分析工具，助力您的投资决策</p>
      </div>
      
      <div class="dashboard-actions">
        <button class="btn btn-primary" @click="navigateTo('lstm-predict')">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
            <polyline points="17 6 23 6 23 12"></polyline>
          </svg>
          <span>开始LSTM预测</span>
        </button>
        <button class="btn btn-outline" @click="navigateTo('multi-strategy')">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
            <polyline points="2 17 12 22 22 17"></polyline>
            <polyline points="2 12 12 17 22 12"></polyline>
          </svg>
          <span>多策略分析</span>
        </button>
      </div>
    </header>
    
    <div class="dashboard-content">
      <div class="dashboard-section">
        <div class="section-header">
          <h2 class="section-title">我的自选股</h2>
          <button class="btn-text" @click="navigateTo('watchlist')">查看全部</button>
        </div>
        
        <div v-if="loadingWatchlist" class="loading-container">
          <div class="loading-spinner"></div>
          <p>正在加载自选股...</p>
        </div>
        
        <div v-else-if="watchlist.length === 0" class="empty-container">
          <div class="empty-illustration">
            <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"></rect>
              <line x1="7" y1="2" x2="7" y2="22"></line>
              <line x1="17" y1="2" x2="17" y2="22"></line>
              <line x1="2" y1="12" x2="22" y2="12"></line>
              <line x1="2" y1="7" x2="7" y2="7"></line>
              <line x1="2" y1="17" x2="7" y2="17"></line>
              <line x1="17" y1="17" x2="22" y2="17"></line>
              <line x1="17" y1="7" x2="22" y2="7"></line>
            </svg>
          </div>
          <p class="empty-text">您的自选股列表为空</p>
          <button class="btn btn-primary" @click="navigateTo('market')">
            <span>添加自选股</span>
          </button>
        </div>
        
        <div v-else class="stock-card-grid">
          <stock-card 
            v-for="stock in displayedWatchlist" 
            :key="stock.code" 
            :stock="stock"
            :in-watchlist="true"
            @click="navigateToStockDetail(stock.code)"
            @analyze="analyzeStock(stock.code)"
            @toggle-watchlist="removeFromWatchlist"
          />
        </div>
      </div>
      
      <div class="dashboard-section">
        <div class="section-header">
          <h2 class="section-title">分析工具</h2>
        </div>
        
        <div class="tools-grid">
          <div class="tool-card" @click="navigateTo('lstm-predict')">
            <div class="tool-icon bg-primary">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M2 20h.01"></path>
                <path d="M7 20v-4"></path>
                <path d="M12 20v-8"></path>
                <path d="M17 20V8"></path>
                <path d="M22 4v16"></path>
              </svg>
            </div>
            <div class="tool-info">
              <h3 class="tool-title">LSTM预测</h3>
              <p class="tool-description">使用思维增强型LSTM模型预测股票未来走势</p>
            </div>
          </div>
          
          <div class="tool-card" @click="navigateTo('llm-predict')">
            <div class="tool-icon bg-primary">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
              </svg>
            </div>
            <div class="tool-info">
              <h3 class="tool-title">LLM大模型分析</h3>
              <p class="tool-description">使用大型语言模型分析股票基本面和技术指标</p>
            </div>
          </div>
          
          <div class="tool-card" @click="navigateTo('multi-strategy')">
            <div class="tool-icon bg-primary">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
                <polyline points="2 17 12 22 22 17"></polyline>
                <polyline points="2 12 12 17 22 12"></polyline>
              </svg>
            </div>
            <div class="tool-info">
              <h3 class="tool-title">多策略组合</h3>
              <p class="tool-description">结合多种量化交易策略，提供全面分析</p>
            </div>
          </div>
          
          <div class="tool-card" @click="navigateTo('market')">
            <div class="tool-icon bg-primary">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"></rect>
                <line x1="7" y1="2" x2="7" y2="22"></line>
                <line x1="17" y1="2" x2="17" y2="22"></line>
                <line x1="2" y1="12" x2="22" y2="12"></line>
                <line x1="2" y1="7" x2="7" y2="7"></line>
                <line x1="2" y1="17" x2="7" y2="17"></line>
                <line x1="17" y1="17" x2="22" y2="17"></line>
                <line x1="17" y1="7" x2="22" y2="7"></line>
              </svg>
            </div>
            <div class="tool-info">
              <h3 class="tool-title">市场行情</h3>
              <p class="tool-description">查看实时市场数据和行业板块分析</p>
            </div>
          </div>
        </div>
      </div>
      
      <div class="dashboard-section">
        <div class="section-header">
          <h2 class="section-title">最近分析</h2>
          <button class="btn-text" @click="navigateTo('analysis-history')">查看全部</button>
        </div>
        
        <div v-if="loadingRecent" class="loading-container">
          <div class="loading-spinner"></div>
          <p>正在加载最近分析...</p>
        </div>
        
        <div v-else-if="recentAnalysis.length === 0" class="empty-container">
          <div class="empty-illustration">
            <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
            </svg>
          </div>
          <p class="empty-text">没有最近的分析记录</p>
          <button class="btn btn-primary" @click="navigateTo('lstm-predict')">
            <span>开始分析</span>
          </button>
        </div>
        
        <div v-else class="recent-analysis-list">
          <div v-for="(item, index) in recentAnalysis" :key="index" class="recent-analysis-item" @click="navigateToAnalysisDetail(item)">
            <div class="analysis-stock-info">
              <div class="analysis-stock-name">{{ item.stockName }}</div>
              <div class="analysis-stock-code">{{ item.stockCode }}</div>
            </div>
            
            <div class="analysis-details">
              <div class="analysis-type">{{ getAnalysisTypeName(item.type) }}</div>
              <div class="analysis-date">{{ formatDate(item.date) }}</div>
            </div>
            
            <div class="analysis-prediction" :class="getTrendClass(item.prediction)">
              {{ getTrendText(item.prediction) }}
            </div>
            
            <button class="btn-icon" @click.stop="reanalyzeStock(item)">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21.5 2v6h-6"></path>
                <path d="M2.5 12c0 5.523 4.477 10 10 10s10-4.477 10-10a9.966 9.966 0 0 0-2-6"></path>
                <path d="M14.5 11c-1.667 4-3.333 6-5 6s-3.333-2-5-6 1.133-8 5-8a5.76 5.76 0 0 1 5 8Z"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import StockCard from '@/components/StockCard.vue'
import { fetchWatchlist, removeFromWatchlist as apiRemoveFromWatchlist } from '@/api/watchlist'
import { getRecentAnalysis } from '@/api/analysis'

export default {
  name: 'Dashboard',
  components: {
    StockCard
  },
  setup() {
    const router = useRouter()
    
    // 自选股数据
    const watchlist = ref([])
    const loadingWatchlist = ref(true)
    
    // 最近分析数据
    const recentAnalysis = ref([])
    const loadingRecent = ref(true)
    
    // 获取自选股列表
    const fetchMyWatchlist = async () => {
      loadingWatchlist.value = true
      try {
        const response = await fetchWatchlist()
        watchlist.value = response.data || []
      } catch (error) {
        console.error('获取自选股失败:', error)
        ElMessage.error('获取自选股失败，请稍后重试')
      } finally {
        loadingWatchlist.value = false
      }
    }
    
    // 从自选股移除
    const removeFromWatchlist = async (stock) => {
      try {
        await apiRemoveFromWatchlist(stock.code)
        ElMessage.success(`已将 ${stock.name}(${stock.code}) 从自选股移除`)
        
        // 更新本地自选股列表
        const index = watchlist.value.findIndex(item => item.code === stock.code)
        if (index !== -1) {
          watchlist.value.splice(index, 1)
        }
      } catch (error) {
        console.error('移除自选股失败:', error)
        ElMessage.error('移除自选股失败，请稍后重试')
      }
    }
    
    // 获取最近分析记录
    const fetchRecentAnalysis = async () => {
      loadingRecent.value = true
      try {
        const response = await getRecentAnalysis({ limit: 5 })
        recentAnalysis.value = response.data || []
      } catch (error) {
        console.error('获取最近分析记录失败:', error)
      } finally {
        loadingRecent.value = false
      }
    }
    
    // 导航方法
    const navigateTo = (route) => {
      router.push({ name: route })
    }
    
    const navigateToStockDetail = (code) => {
      router.push({ name: 'stock-detail', params: { code } })
    }
    
    const navigateToAnalysisDetail = (analysis) => {
      const route = analysis.type === 'lstm' ? 'lstm-result' : 
                   analysis.type === 'llm' ? 'llm-result' : 'strategy-result'
                   
      router.push({ 
        name: route, 
        params: { id: analysis.id },
        query: { stock: analysis.stockCode }
      })
    }
    
    // 分析股票
    const analyzeStock = (code) => {
      router.push({ 
        name: 'lstm-predict',
        query: { stock: code }
      })
    }
    
    // 重新分析
    const reanalyzeStock = (item) => {
      const route = item.type === 'lstm' ? 'lstm-predict' : 
                   item.type === 'llm' ? 'llm-predict' : 'multi-strategy'
                   
      router.push({ 
        name: route,
        query: { stock: item.stockCode }
      })
    }
    
    // 辅助方法
    const formatDate = (dateString) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
    }
    
    const getAnalysisTypeName = (type) => {
      switch (type) {
        case 'lstm': return 'LSTM预测'
        case 'llm': return 'LLM分析'
        case 'strategy': return '策略分析'
        default: return '分析'
      }
    }
    
    const getTrendText = (trend) => {
      if (!trend) return '未知'
      if (typeof trend === 'number') {
        return trend > 0 ? '看涨' : trend < 0 ? '看跌' : '持平'
      }
      if (typeof trend === 'string') {
        return trend === 'up' ? '看涨' : 
               trend === 'down' ? '看跌' : 
               trend === 'neutral' ? '持平' : '未知'
      }
      return '未知'
    }
    
    const getTrendClass = (trend) => {
      if (!trend) return ''
      if (typeof trend === 'number') {
        return trend > 0 ? 'trend-up' : trend < 0 ? 'trend-down' : 'trend-neutral'
      }
      if (typeof trend === 'string') {
        return trend === 'up' ? 'trend-up' : 
               trend === 'down' ? 'trend-down' : 
               trend === 'neutral' ? 'trend-neutral' : ''
      }
      return ''
    }
    
    // 计算属性
    const displayedWatchlist = computed(() => {
      return watchlist.value.slice(0, 4) // 只显示前4个
    })
    
    // 生命周期
    onMounted(() => {
      fetchMyWatchlist()
      fetchRecentAnalysis()
    })
    
    return {
      watchlist,
      loadingWatchlist,
      recentAnalysis,
      loadingRecent,
      displayedWatchlist,
      navigateTo,
      navigateToStockDetail,
      navigateToAnalysisDetail,
      analyzeStock,
      reanalyzeStock,
      removeFromWatchlist,
      formatDate,
      getAnalysisTypeName,
      getTrendText,
      getTrendClass
    }
  }
}
</script>

<style scoped>
.dashboard-container {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.welcome-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.welcome-subtitle {
  font-size: 1.125rem;
  color: var(--text-secondary);
}

.dashboard-actions {
  display: flex;
  gap: 1rem;
}

.dashboard-section {
  margin-bottom: 3rem;
  background-color: var(--bg-primary);
  border-radius: var(--border-radius-lg);
  padding: 1.5rem;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.btn-text {
  background: none;
  border: none;
  color: var(--primary-color);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  padding: 0;
}

.btn-text:hover {
  text-decoration: underline;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  border-radius: var(--border-radius-md);
  font-weight: 500;
  transition: all var(--transition-fast);
  cursor: pointer;
}

.btn-primary {
  background-color: var(--primary-color);
  color: white;
  border: none;
}

.btn-primary:hover {
  background-color: var(--primary-light);
}

.btn-outline {
  background-color: transparent;
  border: 2px solid var(--primary-color);
  color: var(--primary-color);
}

.btn-outline:hover {
  background-color: var(--primary-color);
  color: white;
}

.loading-container, .empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  text-align: center;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--bg-tertiary);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-illustration {
  color: var(--text-tertiary);
  margin-bottom: 1rem;
}

.empty-text {
  font-size: 1rem;
  color: var(--text-secondary);
  margin-bottom: 1.5rem;
}

.stock-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 1.5rem;
}

.tool-card {
  display: flex;
  align-items: flex-start;
  padding: 1.5rem;
  border-radius: var(--border-radius-md);
  background-color: var(--bg-secondary);
  transition: all var(--transition-normal);
  cursor: pointer;
}

.tool-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--shadow-md);
}

.tool-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  margin-right: 1rem;
  color: white;
}

.tool-info {
  flex: 1;
}

.tool-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  color: var(--text-primary);
}

.tool-description {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 0;
}

.recent-analysis-list {
  display: flex;
  flex-direction: column;
}

.recent-analysis-item {
  display: flex;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
  transition: background-color var(--transition-fast);
  cursor: pointer;
}

.recent-analysis-item:last-child {
  border-bottom: none;
}

.recent-analysis-item:hover {
  background-color: var(--bg-secondary);
}

.analysis-stock-info {
  flex: 1;
  min-width: 0;
}

.analysis-stock-name {
  font-weight: 600;
  font-size: 1rem;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.analysis-stock-code {
  font-size: 0.875rem;
  color: var(--text-tertiary);
}

.analysis-details {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  margin: 0 1.5rem;
}

.analysis-type {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
}

.analysis-date {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.analysis-prediction {
  font-weight: 600;
  min-width: 60px;
  text-align: center;
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.875rem;
  margin-right: 1rem;
}

.trend-up {
  color: #ef4444;
  background-color: rgba(239, 68, 68, 0.1);
}

.trend-down {
  color: #10b981;
  background-color: rgba(16, 185, 129, 0.1);
}

.trend-neutral {
  color: #f59e0b;
  background-color: rgba(245, 158, 11, 0.1);
}

.btn-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: var(--bg-secondary);
  color: var(--text-secondary);
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-icon:hover {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 1rem;
  }
  
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .dashboard-actions {
    margin-top: 1rem;
    width: 100%;
  }
  
  .btn {
    flex: 1;
  }
  
  .stock-card-grid,
  .tools-grid {
    grid-template-columns: 1fr;
  }
  
  .recent-analysis-item {
    flex-wrap: wrap;
  }
  
  .analysis-details {
    flex-direction: row;
    justify-content: space-between;
    width: 100%;
    margin: 0.5rem 0;
  }
}
</style> 