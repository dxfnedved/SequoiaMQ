<template>
  <div class="stock-card" @click="$emit('click')">
    <div class="deco-dot top-right"></div>
    <div class="deco-dot bottom-left"></div>
    
    <div class="stock-header">
      <div class="stock-info">
        <h3 class="stock-name">{{ stock.name }}</h3>
        <div class="stock-code">{{ formattedCode }}</div>
      </div>
      
      <div class="stock-actions">
        <button class="action-btn" 
          :class="{ 'active': inWatchlist }" 
          @click.stop="$emit('toggle-watchlist', stock)"
          :title="inWatchlist ? '从自选股移除' : '添加到自选股'">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
          </svg>
        </button>
        
        <button class="action-btn" @click.stop="$emit('analyze', stock.code)" title="分析">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
          </svg>
        </button>
      </div>
    </div>
    
    <div class="stock-price-section">
      <div class="current-price">{{ formattedPrice }}</div>
      <div class="price-change" :class="priceChangeClass">
        <div class="change-value">{{ formattedPriceChange }}</div>
        <div class="change-percent">{{ formattedPriceChangePercent }}</div>
      </div>
    </div>
    
    <div class="stock-trend">
      <svg class="trend-chart" viewBox="0 0 100 20" preserveAspectRatio="none">
        <path :d="trendPath" :stroke="trendColor" stroke-width="1.5" fill="none" />
      </svg>
    </div>
    
    <div class="stock-metrics">
      <div class="metric">
        <div class="metric-label">开盘</div>
        <div class="metric-value">{{ formattedOpen }}</div>
      </div>
      
      <div class="metric">
        <div class="metric-label">最高</div>
        <div class="metric-value">{{ formattedHigh }}</div>
      </div>
      
      <div class="metric">
        <div class="metric-label">最低</div>
        <div class="metric-value">{{ formattedLow }}</div>
      </div>
      
      <div class="metric">
        <div class="metric-label">成交量</div>
        <div class="metric-value">{{ formattedVolume }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'StockCard',
  props: {
    stock: {
      type: Object,
      required: true
    },
    inWatchlist: {
      type: Boolean,
      default: false
    }
  },
  emits: ['click', 'toggle-watchlist', 'analyze'],
  setup(props) {
    // 格式化代码
    const formattedCode = computed(() => {
      if (!props.stock.code) return '';
      const code = props.stock.code;
      if (code.startsWith('SH') || code.startsWith('SZ') || code.startsWith('BJ')) {
        return code;
      }
      // 添加市场前缀
      if (code.startsWith('6')) {
        return 'SH' + code;
      } else if (code.startsWith('0') || code.startsWith('3')) {
        return 'SZ' + code;
      } else if (code.startsWith('4') || code.startsWith('8')) {
        return 'BJ' + code;
      }
      return code;
    });
    
    // 格式化价格
    const formattedPrice = computed(() => {
      return props.stock.price ? props.stock.price.toFixed(2) : '0.00';
    });
    
    // 格式化价格变动
    const formattedPriceChange = computed(() => {
      if (!props.stock.priceChange && props.stock.priceChange !== 0) return '+0.00';
      const change = props.stock.priceChange;
      return (change >= 0 ? '+' : '') + change.toFixed(2);
    });
    
    // 格式化价格变动百分比
    const formattedPriceChangePercent = computed(() => {
      if (!props.stock.priceChangePercent && props.stock.priceChangePercent !== 0) return '+0.00%';
      const changePercent = props.stock.priceChangePercent;
      return (changePercent >= 0 ? '+' : '') + changePercent.toFixed(2) + '%';
    });
    
    // 价格变动样式类
    const priceChangeClass = computed(() => {
      if (!props.stock.priceChange && props.stock.priceChange !== 0) return '';
      return props.stock.priceChange >= 0 ? 'price-up' : 'price-down';
    });
    
    // 格式化开盘价
    const formattedOpen = computed(() => {
      return props.stock.open ? props.stock.open.toFixed(2) : '0.00';
    });
    
    // 格式化最高价
    const formattedHigh = computed(() => {
      return props.stock.high ? props.stock.high.toFixed(2) : '0.00';
    });
    
    // 格式化最低价
    const formattedLow = computed(() => {
      return props.stock.low ? props.stock.low.toFixed(2) : '0.00';
    });
    
    // 格式化成交量
    const formattedVolume = computed(() => {
      if (!props.stock.volume && props.stock.volume !== 0) return '0';
      const volume = props.stock.volume;
      
      if (volume >= 100000000) {
        return (volume / 100000000).toFixed(2) + '亿';
      } else if (volume >= 10000) {
        return (volume / 10000).toFixed(2) + '万';
      }
      
      return volume.toString();
    });
    
    // 模拟趋势线数据
    const trendPath = computed(() => {
      // 为了简单起见，我们使用一个简单的正弦曲线
      // 在实际应用中，应该使用真实的股票历史价格数据
      // 大约生成10个点
      let path = 'M 0 10 ';
      if (props.stock.priceChange >= 0) {
        for (let i = 1; i <= 10; i++) {
          const x = i * 10;
          const y = 10 - Math.sin(i * 0.5) * 5 - (i * 0.3);
          path += `L ${x} ${y} `;
        }
      } else {
        for (let i = 1; i <= 10; i++) {
          const x = i * 10;
          const y = 10 + Math.sin(i * 0.5) * 5 + (i * 0.3);
          path += `L ${x} ${y} `;
        }
      }
      return path;
    });
    
    // 趋势线颜色
    const trendColor = computed(() => {
      return props.stock.priceChange >= 0 ? 'var(--color-up)' : 'var(--color-down)';
    });
    
    return {
      formattedCode,
      formattedPrice,
      formattedPriceChange,
      formattedPriceChangePercent,
      priceChangeClass,
      formattedOpen,
      formattedHigh,
      formattedLow,
      formattedVolume,
      trendPath,
      trendColor
    };
  }
}
</script>

<style scoped>
.stock-card {
  background-color: var(--bg-primary);
  border-radius: var(--border-radius-lg);
  padding: 1.25rem;
  border: 1px solid var(--border-color);
  transition: all var(--transition-normal);
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.stock-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
  border-color: var(--border-color-hover);
}

.stock-card::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background: linear-gradient(90deg, var(--primary-color), var(--primary-light));
  opacity: 0;
  transition: opacity var(--transition-normal);
}

.stock-card:hover::before {
  opacity: 1;
}

.stock-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.25rem;
}

.stock-info {
  overflow: hidden;
}

.stock-name {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0 0 0.25rem 0;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stock-code {
  font-size: 0.875rem;
  color: var(--text-tertiary);
}

.stock-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-secondary);
  color: var(--text-secondary);
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
  overflow: hidden;
}

.action-btn::after {
  content: "";
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  background-color: rgba(255, 255, 255, 0.1);
  transform: scale(0);
  transition: transform 0.3s ease;
  border-radius: 50%;
}

.action-btn:active::after {
  transform: scale(2);
}

.action-btn:hover {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.action-btn.active {
  background-color: var(--primary-color);
  color: white;
}

.stock-price-section {
  display: flex;
  align-items: baseline;
  margin-bottom: 0.75rem;
}

.current-price {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-right: 0.75rem;
}

.price-change {
  display: flex;
  flex-direction: column;
}

.change-value, .change-percent {
  font-size: 0.875rem;
  font-weight: 500;
}

.price-up {
  color: var(--color-up);
}

.price-down {
  color: var(--color-down);
}

.stock-trend {
  height: 30px;
  margin-bottom: 1rem;
  padding: 5px 0;
}

.trend-chart {
  width: 100%;
  height: 100%;
}

.stock-metrics {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border-color);
}

.metric {
  display: flex;
  flex-direction: column;
}

.metric-label {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  margin-bottom: 0.25rem;
}

.metric-value {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
}

.deco-dot {
  position: absolute;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--primary-light);
  opacity: 0.4;
}

.deco-dot.top-right {
  top: 10px;
  right: 10px;
}

.deco-dot.bottom-left {
  bottom: 10px;
  left: 10px;
}

@media (max-width: 768px) {
  .stock-card {
    padding: 1rem;
  }
  
  .current-price {
    font-size: 1.5rem;
  }
}
</style> 