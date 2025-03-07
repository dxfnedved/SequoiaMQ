<template>
  <div class="stock-search-container" :class="{ 'is-focused': isFocused }">
    <div class="search-input-wrapper">
      <div class="search-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
      </div>
      
      <input
        ref="inputRef"
        v-model="searchQuery"
        type="text"
        class="search-input"
        :placeholder="placeholder"
        @input="handleInput"
        @focus="handleFocus"
        @blur="handleBlur"
        @keydown.down.prevent="navigateResults('down')"
        @keydown.up.prevent="navigateResults('up')"
        @keydown.enter="selectHighlighted"
        @keydown.esc="clearSearch"
      />
      
      <button v-if="searchQuery" class="clear-button" @click="clearSearch">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>
    
    <div v-if="isDropdownVisible" class="search-results">
      <div v-if="loading" class="search-loading">
        <div class="loading-spinner"></div>
        <span>搜索中...</span>
      </div>
      
      <template v-else-if="results.length > 0">
        <div 
          v-for="(item, index) in results" 
          :key="item.code" 
          class="search-result-item"
          :class="{ 'is-highlighted': highlightedIndex === index }"
          @mouseenter="highlightedIndex = index"
          @click="selectStock(item)"
        >
          <div class="stock-basic-info">
            <div class="stock-name">{{ item.name }}</div>
            <div class="stock-code">{{ item.code }}</div>
          </div>
          
          <div class="stock-market">{{ getMarketName(item.code) }}</div>
        </div>
      </template>
      
      <div v-else-if="searched && !loading" class="search-empty">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line>
        </svg>
        <span>未找到相关股票</span>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { debounce } from 'lodash-es'
import { searchStocks } from '@/api/stock'

export default {
  name: 'StockSearchInput',
  props: {
    placeholder: {
      type: String,
      default: '输入股票代码或名称'
    },
    clearable: {
      type: Boolean,
      default: true
    },
    showFullInfo: {
      type: Boolean,
      default: false
    },
    initialValue: {
      type: [String, Object],
      default: ''
    },
    autoFocus: {
      type: Boolean,
      default: false
    }
  },
  emits: ['select', 'update:modelValue'],
  
  setup(props, { emit }) {
    const inputRef = ref(null)
    const searchQuery = ref('')
    const searchResults = ref([])
    const searchLoading = ref(false)
    const isFocused = ref(false)
    const isDropdownVisible = ref(false)
    const highlightedIndex = ref(0)
    const searched = ref(false)
    
    // 处理初始值
    onMounted(() => {
      if (props.initialValue) {
        if (typeof props.initialValue === 'string') {
          searchQuery.value = props.initialValue
        } else if (typeof props.initialValue === 'object') {
          searchQuery.value = props.initialValue.name || props.initialValue.code || ''
        }
      }
      
      if (props.autoFocus && inputRef.value) {
        nextTick(() => {
          inputRef.value.focus()
        })
      }
      
      // 添加点击外部关闭下拉框的事件
      document.addEventListener('click', handleClickOutside)
    })
    
    onBeforeUnmount(() => {
      document.removeEventListener('click', handleClickOutside)
    })
    
    // 查询股票
    const querySearch = async (query, callback) => {
      if (query.length < 1) {
        callback([]);
        return;
      }
      
      searchLoading.value = true;
      try {
        const result = await searchStocks(query);
        
        if (result && Array.isArray(result)) {
          searchResults.value = result.map(stock => ({
            code: stock.code,
            name: stock.name,
            market: stock.market || getMarketName(stock.code),
            industry: stock.industry || '',
            value: `${stock.name} (${stock.code})`,
          }));
          
          console.log('Search results:', searchResults.value);
          callback(searchResults.value);
        } else {
          console.error('Invalid search result format:', result);
          callback([]);
        }
      } catch (error) {
        console.error('Search error:', error);
        callback([]);
      } finally {
        searchLoading.value = false;
      }
    };
    
    // 标准化股票代码
    const standardizeCode = (code) => {
      // 去除可能的前缀
      if (code.includes('.')) {
        code = code.split('.')[0];
      }
      return code.trim();
    };
    
    // 获取市场名称
    const getMarketName = (code) => {
      const stdCode = standardizeCode(code);
      
      if (stdCode.startsWith('6')) {
        return '上海';
      } else if (stdCode.startsWith('0') || stdCode.startsWith('3')) {
        return '深圳';
      } else if (stdCode.startsWith('4')) {
        return '北京';
      } else if (stdCode.startsWith('8')) {
        return '北交所';
      } else {
        return '';
      }
    };
    
    // 处理输入
    const handleInput = () => {
      isDropdownVisible.value = true
      querySearch(searchQuery.value, (results) => {
        searchResults.value = results
        searched.value = results.length > 0
        highlightedIndex.value = 0
        isDropdownVisible.value = results.length > 0 || searched.value
      })
    }
    
    // 处理焦点
    const handleFocus = () => {
      isFocused.value = true
      isDropdownVisible.value = true
      
      if (searchQuery.value.trim()) {
        querySearch(searchQuery.value, (results) => {
          searchResults.value = results
          searched.value = results.length > 0
          highlightedIndex.value = 0
          isDropdownVisible.value = results.length > 0 || searched.value
        })
      }
    }
    
    const handleBlur = () => {
      isFocused.value = false
      
      // 延迟关闭下拉框，以便可以点击选项
      setTimeout(() => {
        if (!isFocused.value) {
          isDropdownVisible.value = false
        }
      }, 200)
    }
    
    // 处理点击外部
    const handleClickOutside = (event) => {
      const container = document.querySelector('.stock-search-container')
      if (container && !container.contains(event.target)) {
        isDropdownVisible.value = false
      }
    }
    
    // 清除搜索
    const clearSearch = () => {
      searchQuery.value = ''
      searchResults.value = []
      isDropdownVisible.value = false
      searched.value = false
      emit('update:modelValue', '')
    }
    
    // 导航结果
    const navigateResults = (direction) => {
      if (!searchResults.value.length) return
      
      if (direction === 'down') {
        highlightedIndex.value = (highlightedIndex.value + 1) % searchResults.value.length
      } else if (direction === 'up') {
        highlightedIndex.value = (highlightedIndex.value - 1 + searchResults.value.length) % searchResults.value.length
      }
    }
    
    // 选择高亮项
    const selectHighlighted = () => {
      if (searchResults.value.length && highlightedIndex.value >= 0) {
        selectStock(searchResults.value[highlightedIndex.value])
      }
    }
    
    // 选择股票
    const selectStock = (item) => {
      searchQuery.value = item.name
      isDropdownVisible.value = false
      
      const stockData = {
        code: item.code,
        name: item.name,
        market: item.market || getMarketName(item.code),
        industry: item.industry || '',
      }
      
      emit('select', stockData)
      emit('update:modelValue', stockData.code)
    }
    
    return {
      inputRef,
      searchQuery,
      searchResults,
      searchLoading,
      isFocused,
      isDropdownVisible,
      highlightedIndex,
      searched,
      handleInput,
      handleFocus,
      handleBlur,
      clearSearch,
      navigateResults,
      selectHighlighted,
      selectStock,
      getMarketName
    }
  }
}
</script>

<style scoped>
.stock-search-container {
  position: relative;
  width: 100%;
}

.search-input-wrapper {
  display: flex;
  align-items: center;
  position: relative;
  background-color: var(--bg-secondary);
  border: 2px solid var(--border-color);
  border-radius: var(--border-radius-lg);
  padding: 0.25rem 0.75rem;
  transition: all var(--transition-fast);
}

.stock-search-container.is-focused .search-input-wrapper {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.search-icon {
  display: flex;
  align-items: center;
  color: var(--text-tertiary);
  margin-right: 0.5rem;
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 0.875rem;
  padding: 0.75rem 0;
  outline: none;
  width: 100%;
}

.search-input::placeholder {
  color: var(--text-tertiary);
}

.clear-button {
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 50%;
  transition: all var(--transition-fast);
}

.clear-button:hover {
  color: var(--text-secondary);
  background-color: var(--bg-tertiary);
}

.search-results {
  position: absolute;
  top: calc(100% + 0.25rem);
  left: 0;
  right: 0;
  background-color: var(--bg-primary);
  border-radius: var(--border-radius-md);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-md);
  max-height: 300px;
  overflow-y: auto;
  z-index: 100;
}

.search-result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: background-color var(--transition-fast);
  border-bottom: 1px solid var(--border-color);
}

.search-result-item:last-child {
  border-bottom: none;
}

.search-result-item:hover,
.search-result-item.is-highlighted {
  background-color: var(--bg-secondary);
}

.stock-basic-info {
  display: flex;
  flex-direction: column;
}

.stock-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
}

.stock-code {
  font-size: 0.75rem;
  color: var(--text-tertiary);
}

.stock-market {
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  border-radius: 1rem;
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
}

.search-loading,
.search-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
  color: var(--text-tertiary);
  flex-direction: column;
  gap: 0.75rem;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--bg-tertiary);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style> 