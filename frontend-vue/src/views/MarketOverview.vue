<template>
  <div class="market-overview-container page-container">
    <header class="page-header">
      <h1 class="page-title">市场行情</h1>
      <div class="header-actions">
        <button class="btn btn-outline" @click="refreshMarketData">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M23 4v6h-6"></path>
            <path d="M1 20v-6h6"></path>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10"></path>
            <path d="M20.49 15a9 9 0 0 1-14.85 3.36L1 14"></path>
          </svg>
          <span>刷新数据</span>
        </button>
      </div>
    </header>
    
    <!-- 主要指数 -->
    <section class="market-section">
      <h2 class="section-title">主要指数</h2>
      
      <div v-if="loadingIndices" class="loading-container">
        <div class="loading-spinner"></div>
        <p>正在加载指数数据...</p>
      </div>
      
      <div v-else class="indices-grid">
        <div v-for="(index, idx) in marketIndices" :key="idx" class="index-card">
          <div class="index-name">{{ index.name }}</div>
          <div class="index-price">{{ formatNumber(index.price) }}</div>
          <div class="index-changes">
            <div class="change-value" :class="getPriceChangeClass(index.change)">
              {{ formatPriceChange(index.change) }}
            </div>
            <div class="change-percent" :class="getPriceChangeClass(index.changePercent)">
              {{ formatPercentChange(index.changePercent) }}
            </div>
          </div>
        </div>
      </div>
    </section>
    
    <!-- 行业板块 -->
    <section class="market-section">
      <h2 class="section-title">行业板块</h2>
      
      <div class="section-header">
        <div class="view-options">
          <button 
            v-for="option in viewOptions" 
            :key="option.value" 
            class="view-option" 
            :class="{ 'active': currentView === option.value }"
            @click="currentView = option.value"
          >
            {{ option.label }}
          </button>
        </div>
        
        <div class="sort-options">
          <span class="sort-label">排序:</span>
          <button 
            v-for="sort in sortOptions" 
            :key="sort.value" 
            class="sort-option" 
            :class="{ 'active': currentSort === sort.value }"
            @click="currentSort = sort.value"
          >
            {{ sort.label }}
          </button>
        </div>
      </div>
      
      <div v-if="loadingSectors" class="loading-container">
        <div class="loading-spinner"></div>
        <p>正在加载板块数据...</p>
      </div>
      
      <div v-else class="sectors-grid">
        <div v-for="sector in sortedSectors" :key="sector.code" class="sector-card">
          <div class="sector-header">
            <div class="sector-name">{{ sector.name }}</div>
            <div class="sector-details">
              <div class="sector-volume">成交: {{ formatVolume(sector.volume) }}</div>
            </div>
          </div>
          
          <div class="sector-data">
            <div v-if="currentView === 'change'" class="sector-change-wrapper">
              <div class="sector-bar-container">
                <div 
                  class="sector-bar" 
                  :class="getPriceChangeClass(sector.changePercent)"
                  :style="getBarStyle(sector.changePercent)"
                ></div>
              </div>
              <div class="sector-change-value" :class="getPriceChangeClass(sector.changePercent)">
                {{ formatPercentChange(sector.changePercent) }}
              </div>
            </div>
            
            <div v-else-if="currentView === 'leaders'" class="sector-leaders">
              <div v-for="(stock, index) in sector.leadingStocks.slice(0, 3)" :key="index" class="leader-stock">
                <div class="leader-name">{{ stock.name }}</div>
                <div class="leader-change" :class="getPriceChangeClass(stock.changePercent)">
                  {{ formatPercentChange(stock.changePercent) }}
                </div>
              </div>
            </div>
            
            <div v-else class="sector-price">
              <div class="price-value">{{ formatNumber(sector.price) }}</div>
              <div class="price-changes">
                <div class="change-value" :class="getPriceChangeClass(sector.change)">
                  {{ formatPriceChange(sector.change) }}
                </div>
              </div>
            </div>
          </div>
          
          <button class="view-sector-btn" @click="viewSectorDetails(sector)">查看详情</button>
        </div>
      </div>
    </section>
    
    <!-- 市场热度 -->
    <section class="market-section">
      <h2 class="section-title">市场热度</h2>
      
      <div class="heatmap-header">
        <div class="heatmap-title">
          <span>个股涨跌分布</span>
        </div>
        <div class="heatmap-legend">
          <div class="legend-item">
            <div class="legend-color legend-up-10"></div>
            <span>涨停</span>
          </div>
          <div class="legend-item">
            <div class="legend-color legend-up-5"></div>
            <span>涨5%+</span>
          </div>
          <div class="legend-item">
            <div class="legend-color legend-up-0"></div>
            <span>涨0-5%</span>
          </div>
          <div class="legend-item">
            <div class="legend-color legend-down-0"></div>
            <span>跌0-5%</span>
          </div>
          <div class="legend-item">
            <div class="legend-color legend-down-5"></div>
            <span>跌5%+</span>
          </div>
          <div class="legend-item">
            <div class="legend-color legend-down-10"></div>
            <span>跌停</span>
          </div>
        </div>
      </div>
      
      <div v-if="loadingHeatmap" class="loading-container">
        <div class="loading-spinner"></div>
        <p>正在加载热度数据...</p>
      </div>
      
      <div v-else class="market-heatmap">
        <div class="heatmap-stats">
          <div class="stats-item">
            <div class="stats-label">上涨</div>
            <div class="stats-value up">{{ marketStats.up }}</div>
          </div>
          <div class="stats-item">
            <div class="stats-label">下跌</div>
            <div class="stats-value down">{{ marketStats.down }}</div>
          </div>
          <div class="stats-item">
            <div class="stats-label">平盘</div>
            <div class="stats-value">{{ marketStats.flat }}</div>
          </div>
          <div class="stats-item">
            <div class="stats-label">涨停</div>
            <div class="stats-value up">{{ marketStats.limitUp }}</div>
          </div>
          <div class="stats-item">
            <div class="stats-label">跌停</div>
            <div class="stats-value down">{{ marketStats.limitDown }}</div>
          </div>
        </div>
        
        <div class="heatmap-grid">
          <div 
            v-for="(stock, index) in heatmapData" 
            :key="index" 
            class="heatmap-cell"
            :class="getHeatmapClass(stock.changePercent)"
            @click="viewStockDetails(stock)"
          >
            <div class="cell-name">{{ stock.name }}</div>
            <div class="cell-change">{{ formatPercentChange(stock.changePercent) }}</div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getMarketIndices, getIndustrySectors, getMarketHeatmap } from '@/api/market'

export default {
  name: 'MarketOverview',
  setup() {
    const router = useRouter()
    
    // 数据加载状态
    const loadingIndices = ref(true)
    const loadingSectors = ref(true)
    const loadingHeatmap = ref(true)
    
    // 市场指数数据
    const marketIndices = ref([])
    
    // 行业板块数据
    const sectorData = ref([])
    const currentView = ref('change')
    const currentSort = ref('change')
    
    // 市场热度数据
    const heatmapData = ref([])
    const marketStats = ref({
      up: 0,
      down: 0,
      flat: 0,
      limitUp: 0,
      limitDown: 0
    })
    
    // 视图选项
    const viewOptions = [
      { label: '涨跌幅', value: 'change' },
      { label: '领涨股', value: 'leaders' },
      { label: '价格', value: 'price' }
    ]
    
    // 排序选项
    const sortOptions = [
      { label: '涨幅', value: 'change' },
      { label: '跌幅', value: 'change-asc' },
      { label: '成交额', value: 'volume' }
    ]
    
    // 获取市场指数
    const fetchMarketIndices = async () => {
      loadingIndices.value = true
      try {
        const response = await getMarketIndices()
        marketIndices.value = response.data || []
      } catch (error) {
        console.error('获取市场指数失败:', error)
        ElMessage.error('获取市场指数失败，请稍后重试')
      } finally {
        loadingIndices.value = false
      }
    }
    
    // 获取行业板块
    const fetchSectors = async () => {
      loadingSectors.value = true
      try {
        const response = await getIndustrySectors()
        sectorData.value = response.data || []
      } catch (error) {
        console.error('获取板块数据失败:', error)
        ElMessage.error('获取板块数据失败，请稍后重试')
      } finally {
        loadingSectors.value = false
      }
    }
    
    // 获取市场热度图
    const fetchHeatmap = async () => {
      loadingHeatmap.value = true
      try {
        const response = await getMarketHeatmap()
        if (response.data) {
          heatmapData.value = response.data.stocks || []
          marketStats.value = response.data.stats || {
            up: 0,
            down: 0,
            flat: 0,
            limitUp: 0,
            limitDown: 0
          }
        }
      } catch (error) {
        console.error('获取市场热度图失败:', error)
        ElMessage.error('获取市场热度图失败，请稍后重试')
      } finally {
        loadingHeatmap.value = false
      }
    }
    
    // 刷新所有市场数据
    const refreshMarketData = () => {
      fetchMarketIndices()
      fetchSectors()
      fetchHeatmap()
      ElMessage.success('正在刷新市场数据')
    }
    
    // 格式化数字
    const formatNumber = (num) => {
      if (num === undefined || num === null) return '0.00'
      return parseFloat(num).toFixed(2)
    }
    
    // 格式化价格变动
    const formatPriceChange = (change) => {
      if (change === undefined || change === null) return '+0.00'
      return (change >= 0 ? '+' : '') + parseFloat(change).toFixed(2)
    }
    
    // 格式化百分比变动
    const formatPercentChange = (change) => {
      if (change === undefined || change === null) return '+0.00%'
      return (change >= 0 ? '+' : '') + parseFloat(change).toFixed(2) + '%'
    }
    
    // 格式化成交量
    const formatVolume = (volume) => {
      if (!volume && volume !== 0) return '0'
      
      if (volume >= 100000000) {
        return (volume / 100000000).toFixed(2) + '亿'
      } else if (volume >= 10000) {
        return (volume / 10000).toFixed(2) + '万'
      }
      
      return volume.toString()
    }
    
    // 获取价格变动样式类
    const getPriceChangeClass = (change) => {
      if (!change && change !== 0) return ''
      return parseFloat(change) >= 0 ? 'price-up' : 'price-down'
    }
    
    // 获取热度图单元格样式类
    const getHeatmapClass = (change) => {
      if (!change && change !== 0) return 'cell-flat'
      
      const pct = parseFloat(change)
      if (pct >= 9.5) return 'cell-up-limit'
      if (pct >= 5) return 'cell-up-5'
      if (pct > 0) return 'cell-up-0'
      if (pct <= -9.5) return 'cell-down-limit'
      if (pct <= -5) return 'cell-down-5'
      if (pct < 0) return 'cell-down-0'
      return 'cell-flat'
    }
    
    // 获取板块涨跌幅条形图样式
    const getBarStyle = (changePercent) => {
      if (!changePercent) return { width: '0%' }
      
      const pct = parseFloat(changePercent)
      const absChange = Math.abs(pct)
      // 最大宽度为95%
      const width = Math.min(absChange * 10, 95)
      
      return { width: `${width}%` }
    }
    
    // 按当前排序获取排序后的板块数据
    const sortedSectors = computed(() => {
      const data = [...sectorData.value]
      
      switch (currentSort.value) {
        case 'change':
          return data.sort((a, b) => (b.changePercent || 0) - (a.changePercent || 0))
          
        case 'change-asc':
          return data.sort((a, b) => (a.changePercent || 0) - (b.changePercent || 0))
          
        case 'volume':
          return data.sort((a, b) => (b.volume || 0) - (a.volume || 0))
          
        default:
          return data
      }
    })
    
    // 查看板块详情
    const viewSectorDetails = (sector) => {
      router.push({
        name: 'sector-detail',
        params: { code: sector.code },
        query: { name: sector.name }
      })
    }
    
    // 查看股票详情
    const viewStockDetails = (stock) => {
      router.push({
        name: 'stock-detail',
        params: { code: stock.code }
      })
    }
    
    // 初始化
    onMounted(() => {
      fetchMarketIndices()
      fetchSectors()
      fetchHeatmap()
    })
    
    return {
      // 状态
      loadingIndices,
      loadingSectors,
      loadingHeatmap,
      
      // 数据
      marketIndices,
      sectorData,
      heatmapData,
      marketStats,
      
      // 筛选和排序
      viewOptions,
      sortOptions,
      currentView,
      currentSort,
      sortedSectors,
      
      // 方法
      refreshMarketData,
      formatNumber,
      formatPriceChange,
      formatPercentChange,
      formatVolume,
      getPriceChangeClass,
      getHeatmapClass,
      getBarStyle,
      viewSectorDetails,
      viewStockDetails
    }
  }
}
</script>

<style scoped>
.market-overview-container {
  padding: 2rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.page-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 1rem;
}

.market-section {
  margin-bottom: 3rem;
  background-color: var(--bg-primary);
  border-radius: var(--border-radius-lg);
  padding: 1.5rem;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-top: 0;
  margin-bottom: 1.5rem;
}

.loading-container {
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

/* 指数样式 */
.indices-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.index-card {
  padding: 1.25rem;
  border-radius: var(--border-radius-md);
  background-color: var(--bg-secondary);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.index-name {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.index-price {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.index-changes {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.change-value,
.change-percent {
  font-size: 0.875rem;
  font-weight: 500;
}

.price-up {
  color: var(--color-up);
}

.price-down {
  color: var(--color-down);
}

/* 行业板块样式 */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.view-options,
.sort-options {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.sort-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-right: 0.25rem;
}

.view-option,
.sort-option {
  padding: 0.375rem 0.75rem;
  border-radius: var(--border-radius-md);
  font-size: 0.875rem;
  font-weight: 500;
  background-color: var(--bg-secondary);
  color: var(--text-secondary);
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.view-option:hover,
.sort-option:hover {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.view-option.active,
.sort-option.active {
  background-color: var(--primary-color);
  color: white;
}

.sectors-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.sector-card {
  padding: 1.25rem;
  border-radius: var(--border-radius-md);
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  transition: all var(--transition-normal);
}

.sector-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-3px);
}

.sector-header {
  margin-bottom: 1rem;
}

.sector-name {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.sector-details {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.sector-data {
  margin-bottom: 1rem;
  min-height: 50px;
}

.sector-change-wrapper {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.sector-bar-container {
  flex: 1;
  height: 6px;
  background-color: var(--bg-tertiary);
  border-radius: 3px;
  overflow: hidden;
}

.sector-bar {
  height: 100%;
  border-radius: 3px;
}

.sector-bar.price-up {
  background-color: var(--color-up);
}

.sector-bar.price-down {
  background-color: var(--color-down);
}

.sector-change-value {
  font-size: 0.875rem;
  font-weight: 500;
  width: 60px;
  text-align: right;
}

.sector-leaders {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.leader-stock {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.leader-name {
  font-size: 0.875rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 65%;
}

.leader-change {
  font-size: 0.875rem;
  font-weight: 500;
}

.sector-price {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.price-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.price-changes {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.view-sector-btn {
  width: 100%;
  padding: 0.5rem;
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
  border: none;
  border-radius: var(--border-radius-sm);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.view-sector-btn:hover {
  background-color: var(--primary-color);
  color: white;
}

/* 热度图样式 */
.heatmap-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.heatmap-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
}

.heatmap-legend {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
}

.legend-up-10 {
  background-color: #ef4444;
}

.legend-up-5 {
  background-color: #f97316;
}

.legend-up-0 {
  background-color: #f59e0b;
}

.legend-down-0 {
  background-color: #10b981;
}

.legend-down-5 {
  background-color: #059669;
}

.legend-down-10 {
  background-color: #047857;
}

.heatmap-stats {
  display: flex;
  justify-content: space-around;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.stats-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 80px;
}

.stats-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-bottom: 0.375rem;
}

.stats-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.stats-value.up {
  color: var(--color-up);
}

.stats-value.down {
  color: var(--color-down);
}

.heatmap-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 0.5rem;
}

.heatmap-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 0.75rem 0.5rem;
  border-radius: var(--border-radius-sm);
  cursor: pointer;
  transition: transform var(--transition-fast);
}

.heatmap-cell:hover {
  transform: scale(1.05);
}

.cell-name {
  font-size: 0.75rem;
  font-weight: 500;
  color: white;
  margin-bottom: 0.25rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
}

.cell-change {
  font-size: 0.75rem;
  color: white;
  opacity: 0.9;
}

.cell-up-limit {
  background-color: #ef4444;
}

.cell-up-5 {
  background-color: #f97316;
}

.cell-up-0 {
  background-color: #f59e0b;
}

.cell-flat {
  background-color: #9ca3af;
}

.cell-down-0 {
  background-color: #10b981;
}

.cell-down-5 {
  background-color: #059669;
}

.cell-down-limit {
  background-color: #047857;
}

@media (max-width: 768px) {
  .market-overview-container {
    padding: 1rem;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .indices-grid,
  .sectors-grid {
    grid-template-columns: 1fr;
  }
  
  .heatmap-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .heatmap-grid {
    grid-template-columns: repeat(auto-fill, minmax(70px, 1fr));
  }
}
</style> 