<!-- 自选股管理页面 -->
<template>
  <div class="watchlist-container">
    <h1>自选股观察列表</h1>
    
    <div class="watchlist-header">
      <div class="search-wrapper">
        <StockSearchInput
          v-model="searchQuery"
          placeholder="搜索股票添加到自选"
          :clearable="true"
          @select="handleSelectStock"
        />
      </div>
      <div class="actions-wrapper">
        <el-autocomplete 
          v-model="searchQuery" 
          :fetch-suggestions="querySearch"
          placeholder="搜索股票代码或名称" 
          class="search-input"
          @select="handleSelect"
          :trigger-on-focus="false"
          :debounce="300"
        >
          <template #default="{ item }">
            <div class="stock-suggestion">
              <span class="stock-code">{{ item.code }}</span>
              <span class="stock-name">{{ item.name }}</span>
              <span v-if="item.inWatchlist" class="in-watchlist-tag">已添加</span>
            </div>
          </template>
        </el-autocomplete>
        <button class="add-button" @click="showAddStockDialog" :disabled="!canAddStock">
          <i class="icon-plus"></i> 添加股票
        </button>
      </div>
      <div class="actions-wrapper">
        <button class="action-button" @click="refreshWatchlist" :disabled="loading">
          <i class="icon-refresh"></i> 刷新数据
        </button>
        <button class="action-button" @click="analyzeWatchlist" :disabled="selectedStocks.length === 0">
          <i class="icon-analyze"></i> 分析选中股票
        </button>
        <button v-if="selectedStocks.length > 0" class="action-button danger" @click="batchRemoveStocks">
          <i class="icon-delete"></i> 批量删除
        </button>
      </div>
    </div>
    
    <!-- 状态指示区 -->
    <div class="status-bar" v-if="loading || error">
      <div v-if="loading" class="loading-indicator">
        <i class="icon-loading"></i> 数据加载中...
      </div>
      <div v-if="error" class="error-message">
        <i class="icon-error"></i> {{ error }}
      </div>
    </div>
    
    <div class="watchlist-content">
      <table class="watchlist-table">
        <thead>
          <tr>
            <th class="checkbox-column">
              <input type="checkbox" v-model="selectAll" @change="toggleSelectAll">
            </th>
            <th>代码</th>
            <th>名称</th>
            <th>最新价</th>
            <th>涨跌幅</th>
            <th>成交量</th>
            <th>备注</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="8" class="empty-message">
              <i class="icon-loading"></i> 加载中...
            </td>
          </tr>
          <tr v-else-if="filteredStocks.length === 0">
            <td colspan="8" class="empty-message">
              暂无自选股，请添加股票到观察列表
            </td>
          </tr>
          <tr v-for="stock in filteredStocks" :key="stock.code" :class="{ 'selected': selectedStocks.includes(stock.code) }">
            <td class="checkbox-column">
              <input type="checkbox" :value="stock.code" v-model="selectedStocks">
            </td>
            <td>{{ stock.code }}</td>
            <td>{{ stock.name }}</td>
            <td :class="getPriceClass(stock.price_change)">
              {{ stock.price ? stock.price.toFixed(2) : '-' }}
            </td>
            <td :class="getPriceClass(stock.price_change)">
              {{ stock.price_change ? (stock.price_change * 100).toFixed(2) + '%' : '-' }}
            </td>
            <td>{{ stock.volume ? formatVolume(stock.volume) : '-' }}</td>
            <td class="notes-column" @click="editStockNotes(stock)">
              <span class="notes-text">{{ stock.notes || '点击添加备注' }}</span>
            </td>
            <td class="action-column">
              <div class="action-buttons">
                <button class="icon-button view-button" @click="viewStockDetail(stock.code)" title="查看详情">
                  <i class="icon-view"></i>
                </button>
                <button class="icon-button analyze-button" @click="showAnalysisOptions(stock)" title="分析">
                  <i class="icon-analyze"></i>
                </button>
                <button class="icon-button edit-button" @click="editStock(stock)" title="编辑">
                  <i class="icon-edit"></i>
                </button>
                <button class="icon-button remove-button" @click="removeStock(stock.code)" title="删除">
                  <i class="icon-delete"></i>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- 添加股票对话框 -->
    <div v-if="showAddDialog" class="dialog-overlay">
      <div class="dialog-container">
        <div class="dialog-header">
          <h3>添加股票</h3>
          <button class="close-button" @click="showAddDialog = false">×</button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <label>股票代码/名称</label>
            <el-autocomplete 
              v-model="stockToAdd.input" 
              :fetch-suggestions="querySearch"
              placeholder="输入股票代码或名称" 
              class="form-input"
              @select="handleAddSelect"
              :trigger-on-focus="true"
              :debounce="300"
            >
              <template #default="{ item }">
                <div class="stock-suggestion">
                  <span class="stock-code">{{ item.code }}</span>
                  <span class="stock-name">{{ item.name }}</span>
                </div>
              </template>
            </el-autocomplete>
          </div>
          <div class="form-group">
            <label>备注 (选填)</label>
            <textarea 
              v-model="stockToAdd.notes" 
              placeholder="添加备注信息" 
              class="form-textarea"
            ></textarea>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="cancel-button" @click="showAddDialog = false">取消</button>
          <button class="confirm-button" @click="addStock" :disabled="!stockToAdd.code">添加</button>
        </div>
      </div>
    </div>
    
    <!-- 编辑股票对话框 -->
    <div v-if="showEditDialog" class="dialog-overlay">
      <div class="dialog-container">
        <div class="dialog-header">
          <h3>编辑股票信息</h3>
          <button class="close-button" @click="showEditDialog = false">×</button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <label>股票代码</label>
            <input 
              type="text" 
              v-model="editingStock.code" 
              disabled
              class="form-input"
            >
            <small>股票代码不可修改</small>
          </div>
          <div class="form-group">
            <label>股票名称</label>
            <input 
              type="text" 
              v-model="editingStock.name" 
              placeholder="股票名称" 
              class="form-input"
            >
          </div>
          <div class="form-group">
            <label>备注</label>
            <textarea 
              v-model="editingStock.notes" 
              placeholder="添加备注信息" 
              class="form-textarea"
            ></textarea>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="cancel-button" @click="showEditDialog = false">取消</button>
          <button class="confirm-button" @click="updateStock">保存</button>
        </div>
      </div>
    </div>
    
    <!-- 编辑备注快捷对话框 -->
    <div v-if="showNotesDialog" class="dialog-overlay">
      <div class="dialog-container">
        <div class="dialog-header">
          <h3>编辑备注 - {{ editingStock.name }}</h3>
          <button class="close-button" @click="showNotesDialog = false">×</button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <textarea 
              v-model="editingStock.notes" 
              placeholder="添加备注信息" 
              class="form-textarea"
              rows="5"
            ></textarea>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="cancel-button" @click="showNotesDialog = false">取消</button>
          <button class="confirm-button" @click="saveNotes">保存备注</button>
        </div>
      </div>
    </div>
    
    <!-- 股票详情对话框 -->
    <div v-if="showDetailDialog" class="dialog-overlay">
      <div class="dialog-container detail-dialog">
        <div class="dialog-header">
          <h3>股票详情 - {{ detailStock.name }} ({{ detailStock.code }})</h3>
          <button class="close-button" @click="showDetailDialog = false">×</button>
        </div>
        <div class="dialog-body">
          <div v-if="detailLoading" class="loading-container">
            <i class="icon-loading"></i> 加载中...
          </div>
          <div v-else-if="detailError" class="error-container">
            <i class="icon-error"></i> {{ detailError }}
          </div>
          <div v-else class="stock-detail-content">
            <div class="detail-section">
              <h4>基本信息</h4>
              <div class="detail-item">
                <span class="detail-label">股票代码:</span>
                <span class="detail-value">{{ detailStock.code }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">股票名称:</span>
                <span class="detail-value">{{ detailStock.name }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">当前价格:</span>
                <span class="detail-value" :class="getPriceClass(detailStock.price_change)">
                  {{ detailStock.price ? detailStock.price.toFixed(2) : '-' }}
                </span>
              </div>
              <div class="detail-item">
                <span class="detail-label">涨跌幅:</span>
                <span class="detail-value" :class="getPriceClass(detailStock.price_change)">
                  {{ detailStock.price_change ? (detailStock.price_change * 100).toFixed(2) + '%' : '-' }}
                </span>
              </div>
              <div class="detail-item">
                <span class="detail-label">成交量:</span>
                <span class="detail-value">
                  {{ detailStock.volume ? formatVolume(detailStock.volume) : '-' }}
                </span>
              </div>
              <div class="detail-item">
                <span class="detail-label">添加时间:</span>
                <span class="detail-value">{{ formatDate(detailStock.add_time) }}</span>
              </div>
            </div>
            
            <div class="detail-section">
              <h4>备注</h4>
              <div class="detail-notes">
                {{ detailStock.notes || '暂无备注' }}
              </div>
              <button class="text-button" @click="editStockNotes(detailStock)">
                编辑备注
              </button>
            </div>
            
            <div class="detail-section">
              <h4>操作</h4>
              <div class="detail-actions">
                <button class="action-button" @click="analyzeStock(detailStock.code)">
                  <i class="icon-analyze"></i> 分析该股票
                </button>
                <button class="action-button" @click="editStock(detailStock)">
                  <i class="icon-edit"></i> 编辑信息
                </button>
                <button class="action-button danger" @click="removeStockFromDetail(detailStock.code)">
                  <i class="icon-delete"></i> 删除
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 股票分析选项对话框 -->
    <div v-if="showAnalysisDialog" class="dialog-overlay">
      <div class="dialog-container">
        <div class="dialog-header">
          <h3>股票分析选项</h3>
          <button class="close-button" @click="showAnalysisDialog = false">×</button>
        </div>
        <div class="dialog-body">
          <div class="analysis-options">
            <div class="option-card" @click="goToStrategyAnalysis">
              <div class="option-icon"><i class="icon-strategy"></i></div>
              <div class="option-title">策略分析</div>
              <div class="option-desc">使用多种交易策略进行股票分析</div>
            </div>
            <div class="option-card" @click="goToLstmAnalysis">
              <div class="option-icon"><i class="icon-ai"></i></div>
              <div class="option-title">LSTM预测</div>
              <div class="option-desc">基于深度学习的股价走势预测</div>
            </div>
            <div class="option-card" @click="goToLlmAnalysis">
              <div class="option-icon"><i class="icon-llm"></i></div>
              <div class="option-title">LLM大模型分析</div>
              <div class="option-desc">利用大型语言模型分析股票前景</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 历史分析结果卡片 -->
    <div v-if="showHistoryPanel && currentStock" class="history-panel">
      <div class="history-header">
        <h3>{{ currentStock.name }} ({{ currentStock.code }}) 分析历史</h3>
        <button class="close-button" @click="showHistoryPanel = false">×</button>
      </div>
      <div class="history-content">
        <div v-if="loadingHistory" class="loading-message">
          加载历史数据中...
        </div>
        <div v-else-if="analysisHistory.length === 0" class="empty-message">
          暂无历史分析数据
        </div>
        <div v-else class="history-list">
          <div v-for="(item, index) in analysisHistory" :key="index" class="history-item">
            <div class="history-type">{{ getAnalysisTypeName(item.type) }}</div>
            <div class="history-date">{{ formatDate(item.date) }}</div>
            <div class="history-result" :class="getResultClass(item.result)">
              {{ getResultText(item.result) }}
            </div>
            <button class="view-detail-btn" @click="viewHistoryDetail(item)">查看详情</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { useWatchlistStore } from '@/store/watchlist'
import { searchStocks, getBatchStockPrices } from '@/api/stock'
import { getStockAnalysisHistory } from '@/api/analysis'

// 引入状态管理
const watchlistStore = useWatchlistStore()
const router = useRouter()

// 数据
const loading = ref(false)
const error = ref(null)
const watchlist = ref([])
const searchQuery = ref('')
const selectedStocks = ref([])
const selectAll = ref(false)

// 对话框控制
const showAddDialog = ref(false)
const showEditDialog = ref(false)
const showNotesDialog = ref(false)
const showDetailDialog = ref(false)
const showAnalysisDialog = ref(false)
const showHistoryPanel = ref(false)

// 编辑数据
const stockToAdd = ref({
  input: '',
  code: '',
  name: '',
  notes: ''
})
const editingStock = ref({
  code: '',
  name: '',
  notes: ''
})
const detailStock = ref({})
const detailLoading = ref(false)
const detailError = ref(null)
const analysisHistory = ref([])
const loadingHistory = ref(false)
const currentStock = ref(null)

// 计算属性
const filteredStocks = computed(() => {
  if (!searchQuery.value) {
    return watchlist.value
  }
  
  const query = searchQuery.value.toLowerCase()
  return watchlist.value.filter(stock => 
    stock.code.toLowerCase().includes(query) || 
    stock.name.toLowerCase().includes(query)
  )
})

// 生命周期钩子
onMounted(async () => {
  await loadWatchlist()
})

// 方法
const loadWatchlist = async () => {
  loading.value = true
  error.value = null
  
  try {
    // 调用store的loadWatchlist方法
    await watchlistStore.loadWatchlist()
    watchlist.value = watchlistStore.stocks || []
  } catch (err) {
    console.error('加载自选股失败:', err)
    error.value = '加载自选股失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

const showAddStockDialog = () => {
  stockToAdd.value = { input: '', code: '', name: '', notes: '' }
  showAddDialog.value = true
}

const addStock = async () => {
  if (!stockToAdd.value.code) {
    ElMessage.warning('请输入股票代码')
    return
  }
  
  loading.value = true
  
  try {
    await watchlistStore.addStock(stockToAdd.value)
    ElMessage.success('添加股票成功')
    showAddDialog.value = false
    await loadWatchlist()
  } catch (err) {
    ElMessage.error('添加股票失败: ' + (err.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const editStock = (stock) => {
  editingStock.value = { ...stock }
  showEditDialog.value = true
}

const updateStock = async () => {
  if (!editingStock.value.name) {
    ElMessage.warning('股票名称不能为空')
    return
  }
  
  loading.value = true
  
  try {
    await watchlistStore.updateStock(
      editingStock.value.code,
      {
        name: editingStock.value.name,
        notes: editingStock.value.notes
      }
    )
    ElMessage.success('更新股票信息成功')
    showEditDialog.value = false
    showNotesDialog.value = false
    
    // 如果是在详情页编辑的，更新详情页数据
    if (showDetailDialog.value) {
      detailStock.value = { ...editingStock.value }
    }
    
    await loadWatchlist()
  } catch (err) {
    ElMessage.error('更新股票信息失败: ' + (err.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const editStockNotes = (stock) => {
  editingStock.value = { ...stock }
  showNotesDialog.value = true
}

const saveNotes = async () => {
  loading.value = true
  
  try {
    await watchlistStore.updateStock(
      editingStock.value.code,
      { notes: editingStock.value.notes }
    )
    ElMessage.success('更新备注成功')
    showNotesDialog.value = false
    
    // 如果是在详情页编辑的，更新详情页数据
    if (showDetailDialog.value) {
      detailStock.value.notes = editingStock.value.notes
    }
    
    await loadWatchlist()
  } catch (err) {
    ElMessage.error('更新备注失败: ' + (err.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const removeStock = async (code) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除股票 ${code} 吗?`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    loading.value = true
    
    await watchlistStore.removeStock(code)
    ElMessage.success('删除成功')
    
    // 如果是在详情页删除的，关闭详情页
    if (showDetailDialog.value && detailStock.value.code === code) {
      showDetailDialog.value = false
    }
    
    await loadWatchlist()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('删除失败: ' + (err.message || '未知错误'))
    }
  } finally {
    loading.value = false
  }
}

const removeStockFromDetail = async (code) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除股票 ${code} 吗?`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    loading.value = true
    
    await watchlistStore.removeStock(code)
    ElMessage.success('删除成功')
    showDetailDialog.value = false
    
    await loadWatchlist()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('删除失败: ' + (err.message || '未知错误'))
    }
  } finally {
    loading.value = false
  }
}

const batchRemoveStocks = async () => {
  if (selectedStocks.value.length === 0) {
    ElMessage.warning('请至少选择一只股票')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedStocks.value.length} 只股票吗?`,
      '批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    loading.value = true
    
    for (const code of selectedStocks.value) {
      await watchlistStore.removeStock(code)
    }
    
    ElMessage.success(`成功删除 ${selectedStocks.value.length} 只股票`)
    selectedStocks.value = []
    selectAll.value = false
    
    await loadWatchlist()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('批量删除失败: ' + (err.message || '未知错误'))
    }
  } finally {
    loading.value = false
  }
}

const viewStockDetail = async (code) => {
  detailLoading.value = true
  detailError.value = null
  showDetailDialog.value = true
  
  try {
    // 从当前列表中查找股票信息
    const stock = watchlist.value.find(s => s.code === code)
    if (stock) {
      detailStock.value = { ...stock }
    } else {
      // 如果没有找到，尝试从API获取
      const stockDetails = await watchlistStore.getStockDetail(code)
      detailStock.value = stockDetails || { code, name: '未知' }
    }
  } catch (err) {
    console.error('获取股票详情失败:', err)
    detailError.value = '获取股票详情失败'
  } finally {
    detailLoading.value = false
  }
}

const getPriceClass = (change) => {
  if (!change) return ''
  return change > 0 ? 'price-up' : (change < 0 ? 'price-down' : '')
}

const formatVolume = (volume) => {
  if (!volume) return '-'
  
  if (volume >= 100000000) {
    return (volume / 100000000).toFixed(2) + '亿'
  } else if (volume >= 10000) {
    return (volume / 10000).toFixed(2) + '万'
  } else {
    return volume.toString()
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (err) {
    return dateStr
  }
}

const toggleSelectAll = () => {
  if (selectAll.value) {
    selectedStocks.value = watchlist.value.map(stock => stock.code)
  } else {
    selectedStocks.value = []
  }
}

const refreshWatchlist = async () => {
  ElMessage.info('正在刷新数据...')
  
  try {
    loading.value = true
    // 获取详细信息（包含实时价格）
    await watchlistStore.loadWatchlistDetails()
    watchlist.value = watchlistStore.stocks || []
    ElMessage.success('数据刷新成功')
  } catch (err) {
    ElMessage.error('刷新数据失败: ' + (err.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const analyzeWatchlist = () => {
  if (selectedStocks.value.length === 0) {
    ElMessage.warning('请至少选择一只股票进行分析')
    return
  }
  
  // 跳转到分析页面
  router.push({
    name: 'analysis',
    query: { 
      stocks: selectedStocks.value.join(',')
    }
  })
}

const analyzeStock = (code) => {
  // 跳转到分析页面
  router.push({
    name: 'analysis',
    query: { 
      stocks: code
    }
  })
}

// 搜索股票的自动完成功能
const querySearch = async (query, callback) => {
  if (query.length < 1) {
    callback([]);
    return;
  }

  try {
    loading.value = true;
    const res = await searchStocks(query);
    
    // 确保正确处理API返回结果
    let stocks = [];
    if (res && res.data && Array.isArray(res.data)) {
      stocks = res.data.map(item => {
        // 检查是否已经在自选股列表中
        const inWatchlist = watchlist.value.some(
          stock => stock.code === item.code
        );
        return {
          ...item,
          inWatchlist
        };
      });
    }
    
    // 记录搜索结果以便后续使用
    searchResults.value = stocks;
    callback(stocks);
  } catch (error) {
    console.error("搜索股票时出错:", error);
    callback([]);
  } finally {
    loading.value = false;
  }
}

// 选择搜索结果
const handleSelect = (item) => {
  if (!item) return;
  
  // 如果已经在自选股中，提示用户
  if (item.inWatchlist) {
    ElMessage.warning(`${item.name}(${item.code}) 已在自选股列表中`);
    return;
  }
  
  // 添加到自选股
  addStockToWatchlist(item);
}

// 添加对话框中选择股票
const handleAddSelect = (item) => {
  stockToAdd.value.code = item.code;
  stockToAdd.value.name = item.name;
}

// 显示股票分析选项
const showAnalysisOptions = (stock) => {
  currentStock.value = stock;
  showAnalysisDialog.value = true;
}

// 进入策略分析页面
const goToStrategyAnalysis = () => {
  showAnalysisDialog.value = false;
  router.push({
    name: 'MultiStrategy',
    query: { stock: currentStock.value.code }
  });
}

// 进入LSTM预测页面
const goToLstmAnalysis = () => {
  showAnalysisDialog.value = false;
  router.push({
    name: 'LstmPredict',
    query: { stock: currentStock.value.code }
  });
}

// 进入LLM分析页面
const goToLlmAnalysis = () => {
  showAnalysisDialog.value = false;
  router.push({
    name: 'LlmPredict',
    query: { stock: currentStock.value.code }
  });
}

// 查看股票历史分析结果
const viewStockAnalysisHistory = async (stock) => {
  currentStock.value = stock;
  loadingHistory.value = true;
  showHistoryPanel.value = true;
  
  try {
    analysisHistory.value = await getStockAnalysisHistory(stock.code);
  } catch (error) {
    console.error('获取分析历史失败:', error);
    detailError.value = '获取分析历史失败';
  } finally {
    loadingHistory.value = false;
  }
}

// 查看历史分析详情
const viewHistoryDetail = (item) => {
  // 根据类型跳转到不同的详情页
  if (item.type === 'strategy') {
    router.push({
      name: 'AnalysisResult',
      params: { id: item.id }
    });
  } else if (item.type === 'lstm') {
    router.push({
      name: 'LstmPredict',
      query: { resultId: item.id }
    });
  } else if (item.type === 'llm') {
    router.push({
      name: 'LlmPredict',
      query: { resultId: item.id }
    });
  }
}

// 获取分析类型名称
const getAnalysisTypeName = (type) => {
  const typeMap = {
    'strategy': '策略分析',
    'lstm': 'LSTM预测',
    'llm': 'LLM分析'
  };
  return typeMap[type] || '未知类型';
}

// 获取结果样式类
const getResultClass = (result) => {
  if (result === 'buy' || result === 'strong_buy') {
    return 'positive';
  } else if (result === 'sell' || result === 'strong_sell') {
    return 'negative';
  }
  return 'neutral';
}

// 获取结果文本
const getResultText = (result) => {
  const resultMap = {
    'strong_buy': '强烈推荐买入',
    'buy': '建议买入',
    'hold': '建议持有',
    'sell': '建议卖出',
    'strong_sell': '强烈建议卖出'
  };
  return resultMap[result] || '未知结果';
}

// 搜索相关
const searchResults = ref([]);
const selectedStock = ref(null);

// 计算属性：是否可以添加股票
const canAddStock = computed(() => {
  return selectedStock.value && 
         !watchlist.value.some(item => item.code === selectedStock.value.code);
});

// 添加选中的股票到自选股
const addSelectedStock = async () => {
  if (!selectedStock.value) return;
  
  // 检查是否已经在自选股中
  if (watchlist.value.some(item => item.code === selectedStock.value.code)) {
    ElMessage.warning(`股票 ${selectedStock.value.code} 已经在自选股列表中`);
    return;
  }
  
  try {
    loading.value = true;
    
    const stockToAdd = {
      code: selectedStock.value.code,
      name: selectedStock.value.name,
      notes: ''
    };
    
    const response = await watchlistStore.addStock(stockToAdd);
    
    if (response.code === 200) {
      ElMessage.success(`股票 ${stockToAdd.code} 添加成功`);
      // 刷新自选股列表
      await loadWatchlist();
      // 清空搜索
      searchQuery.value = '';
      selectedStock.value = null;
    } else {
      ElMessage.error(response.message || '添加失败');
    }
  } catch (error) {
    console.error('添加股票失败:', error);
    ElMessage.error('添加股票失败');
  } finally {
    loading.value = false;
  }
};

// 添加到自选股
const addStockToWatchlist = async (stock) => {
  try {
    loading.value = true;
    await watchlistStore.addStock(stock);
    
    // 刷新自选股列表
    await loadWatchlist();
    
    ElMessage.success(`已添加 ${stock.name}(${stock.code}) 到自选股`);
    
    // 清空搜索结果
    searchQuery.value = '';
  } catch (error) {
    console.error("添加自选股失败:", error);
    ElMessage.error(`添加自选股失败: ${error.message || '未知错误'}`);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.watchlist-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

h1 {
  margin-bottom: 20px;
  color: #303133;
  font-size: 24px;
}

.watchlist-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
}

.search-wrapper {
  display: flex;
  gap: 10px;
  flex: 1;
}

.search-input {
  width: 250px;
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
}

.add-button {
  padding: 8px 16px;
  background-color: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: background-color 0.3s;
}

.add-button:hover {
  background-color: #66b1ff;
}

.actions-wrapper {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.action-button {
  padding: 8px 16px;
  background-color: white;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 5px;
  white-space: nowrap;
}

.action-button:hover {
  border-color: #409eff;
  color: #409eff;
}

.action-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
  border-color: #dcdfe6;
  color: #909399;
}

.action-button.danger {
  border-color: #f56c6c;
  color: #f56c6c;
}

.action-button.danger:hover {
  background-color: #f56c6c;
  color: white;
}

.status-bar {
  margin-bottom: 15px;
  padding: 10px;
  border-radius: 4px;
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #409eff;
}

.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #f56c6c;
}

.watchlist-content {
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.watchlist-table {
  width: 100%;
  border-collapse: collapse;
}

.watchlist-table th, 
.watchlist-table td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid #ebeef5;
}

.watchlist-table th {
  background-color: #f5f7fa;
  color: #606266;
  font-weight: 500;
}

.watchlist-table .checkbox-column {
  width: 40px;
  text-align: center;
}

.watchlist-table .notes-column {
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
}

.notes-text {
  color: #909399;
  font-style: italic;
}

.watchlist-table .action-column {
  width: 120px;
  text-align: center;
  white-space: nowrap;
}

.watchlist-table tr.selected {
  background-color: #f0f9ff;
}

.watchlist-table tr:hover {
  background-color: #f5f7fa;
}

.price-up {
  color: #f56c6c;
}

.price-down {
  color: #67c23a;
}

.icon-button {
  width: 30px;
  height: 30px;
  background: none;
  border: none;
  cursor: pointer;
  border-radius: 4px;
  position: relative;
  margin: 0 2px;
}

.icon-button::before {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.view-button:hover {
  background-color: #f0f9ff;
  color: #409eff;
}

.edit-button:hover {
  background-color: #f0f9eb;
  color: #67c23a;
}

.remove-button:hover {
  background-color: #fef0f0;
  color: #f56c6c;
}

.empty-message {
  text-align: center;
  padding: 30px;
  color: #909399;
}

/* 图标字体 - 实际项目中应使用图标字体或SVG图标 */
.icon-refresh::before {
  content: "↻";
}

.icon-analyze::before {
  content: "📊";
}

.icon-view::before {
  content: "👁";
}

.icon-edit::before {
  content: "✎";
}

.icon-delete::before {
  content: "✕";
}

.icon-plus::before {
  content: "+";
}

.icon-loading::before {
  content: "⟳";
  display: inline-block;
  animation: spin 1s linear infinite;
}

.icon-error::before {
  content: "⚠";
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 对话框样式 */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.dialog-container {
  background-color: white;
  border-radius: 4px;
  width: 400px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.detail-dialog {
  width: 500px;
}

.dialog-header {
  padding: 15px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #ebeef5;
}

.dialog-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.close-button {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #909399;
}

.dialog-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-size: 14px;
  color: #606266;
}

.form-group small {
  color: #909399;
  font-size: 12px;
}

.form-input {
  width: 100%;
  padding: 10px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
}

.form-input:disabled {
  background-color: #f5f7fa;
  cursor: not-allowed;
}

.form-textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  min-height: 80px;
  resize: vertical;
}

.dialog-footer {
  padding: 15px 20px;
  text-align: right;
  border-top: 1px solid #ebeef5;
}

.cancel-button, .confirm-button {
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  margin-left: 10px;
}

.cancel-button {
  background-color: white;
  border: 1px solid #dcdfe6;
  color: #606266;
}

.cancel-button:hover {
  border-color: #c6e2ff;
  color: #409eff;
}

.confirm-button {
  background-color: #409eff;
  color: white;
  border: none;
}

.confirm-button:hover {
  background-color: #66b1ff;
}

.confirm-button:disabled {
  background-color: #a0cfff;
  cursor: not-allowed;
}

/* 详情页样式 */
.stock-detail-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-section {
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 15px;
}

.detail-section:last-child {
  border-bottom: none;
}

.detail-section h4 {
  margin-top: 0;
  margin-bottom: 10px;
  color: #303133;
}

.detail-item {
  display: flex;
  margin-bottom: 8px;
}

.detail-label {
  flex: 0 0 100px;
  color: #909399;
}

.detail-value {
  flex: 1;
  word-break: break-word;
}

.detail-notes {
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 10px;
  min-height: 60px;
  white-space: pre-wrap;
}

.detail-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.text-button {
  background: none;
  border: none;
  color: #409eff;
  cursor: pointer;
  padding: 0;
}

.text-button:hover {
  text-decoration: underline;
}

.loading-container, .error-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  flex-direction: column;
  gap: 10px;
}

@media (max-width: 768px) {
  .watchlist-header {
    flex-direction: column;
  }
  
  .search-input {
    width: 100%;
  }
  
  .watchlist-table {
    font-size: 14px;
  }
  
  .watchlist-table th, 
  .watchlist-table td {
    padding: 8px;
  }
  
  .dialog-container {
    width: 95%;
  }
}

.stock-suggestion {
  display: flex;
  align-items: center;
  padding: 8px 0;
}

.stock-code {
  font-weight: bold;
  margin-right: 10px;
  min-width: 80px;
}

.stock-name {
  color: #606266;
  flex: 1;
}

.in-watchlist-tag {
  background-color: #f0f0f0;
  color: #909399;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}

.action-buttons {
  display: flex;
  justify-content: space-between;
  gap: 5px;
}

.analyze-button {
  background-color: #409eff;
  color: white;
}

.analyze-button:hover {
  background-color: #66b1ff;
}

.analysis-options {
  display: flex;
  gap: 15px;
  justify-content: center;
}

.option-card {
  width: 160px;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.option-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px 0 rgba(0, 0, 0, 0.15);
}

.option-icon {
  font-size: 28px;
  margin-bottom: 10px;
  color: #409EFF;
}

.option-title {
  font-weight: bold;
  margin-bottom: 5px;
  color: #303133;
}

.option-desc {
  font-size: 12px;
  color: #606266;
}

.history-panel {
  position: fixed;
  right: 20px;
  top: 80px;
  width: 400px;
  background: white;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  z-index: 100;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid #ebeef5;
}

.history-content {
  padding: 15px;
  max-height: 400px;
  overflow-y: auto;
}

.history-item {
  display: flex;
  align-items: center;
  padding: 10px;
  border-bottom: 1px solid #ebeef5;
}

.history-type {
  width: 100px;
  font-weight: bold;
}

.history-date {
  width: 100px;
  color: #606266;
}

.history-result {
  width: 120px;
  padding: 2px 6px;
  border-radius: 4px;
  text-align: center;
}

.history-result.positive {
  background-color: rgba(103, 194, 58, 0.1);
  color: #67c23a;
}

.history-result.negative {
  background-color: rgba(245, 108, 108, 0.1);
  color: #f56c6c;
}

.history-result.neutral {
  background-color: rgba(144, 147, 153, 0.1);
  color: #909399;
}

.view-detail-btn {
  padding: 2px 8px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: white;
  color: #606266;
  cursor: pointer;
  margin-left: auto;
}

.view-detail-btn:hover {
  color: #409eff;
  border-color: #c6e2ff;
  background-color: #ecf5ff;
}
</style> 