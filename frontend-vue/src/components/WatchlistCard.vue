<template>
  <div class="watchlist-card card">
    <div class="watchlist-card-header flex justify-between items-center">
      <div class="stock-info">
        <div class="stock-code">{{ stock.code }}</div>
        <div class="stock-name">{{ stock.name }}</div>
      </div>
      <div class="stock-price" :class="priceChangeClass">
        <div class="current-price">{{ stock.price }}</div>
        <div class="price-change flex items-center gap-xs">
          <span>{{ priceChangeText }}</span>
          <svg-icon :name="priceChangeIcon" class="change-icon" />
        </div>
      </div>
    </div>
    <div class="watchlist-card-body">
      <div class="indicators flex justify-between">
        <div class="indicator">
          <div class="indicator-label">成交量</div>
          <div class="indicator-value">{{ formatVolume(stock.volume) }}</div>
        </div>
        <div class="indicator">
          <div class="indicator-label">市值</div>
          <div class="indicator-value">{{ formatMarketCap(stock.marketCap) }}</div>
        </div>
        <div class="indicator">
          <div class="indicator-label">PE</div>
          <div class="indicator-value">{{ stock.pe || '-' }}</div>
        </div>
      </div>
    </div>
    <div class="watchlist-card-footer flex justify-between items-center">
      <div class="update-time">{{ formatTime(stock.updateTime) }}</div>
      <div class="actions flex gap-sm">
        <button class="btn btn-text" @click="('view', stock)">
          <svg-icon name="chart" />
          <span>图表</span>
        </button>
        <button class="btn btn-text" @click="('analyze', stock)">
          <svg-icon name="analyze" />
          <span>分析</span>
        </button>
        <button class="btn btn-text btn-danger" @click="('remove', stock)">
          <svg-icon name="delete" />
          <span>删除</span>
        </button>
      </div>
    </div>
  </div>
</template>


<script>
import { computed } from 'vue'
import SvgIcon from './SvgIcon.vue'

export default {
  name: 'WatchlistCard',
  components: {
    SvgIcon
  },
  props: {
    stock: {
      type: Object,
      required: true
    }
  },
  emits: ['view', 'analyze', 'remove'],
  setup(props) {
    // 计算价格变化的样式类
    const priceChangeClass = computed(() => {
      if (!props.stock.changePercent) return '';
      return props.stock.changePercent > 0 ? 'stock-up' : 'stock-down';
    });
    
    // 计算价格变化的文本
    const priceChangeText = computed(() => {
      if (!props.stock.changePercent) return '--';
      const prefix = props.stock.changePercent > 0 ? '+' : '';
      return ${prefix}%;
    });
    
    // 计算价格变化的图标
    const priceChangeIcon = computed(() => {
      return props.stock.changePercent > 0 ? 'arrow-up' : 'arrow-down';
    });
    
    // 格式化成交量
    const formatVolume = (volume) => {
      if (!volume) return '--';
      if (volume >= 100000000) {
        return ${(volume / 100000000).toFixed(2)}亿;
      } else if (volume >= 10000) {
        return ${(volume / 10000).toFixed(2)}万;
      }
      return volume.toString();
    };
    
    // 格式化市值
    const formatMarketCap = (marketCap) => {
      if (!marketCap) return '--';
      if (marketCap >= 100000000000) {
        return ${(marketCap / 100000000000).toFixed(2)}千亿;
      } else if (marketCap >= 100000000) {
        return ${(marketCap / 100000000).toFixed(2)}亿;
      }
      return marketCap.toString();
    };
    
    // 格式化时间
    const formatTime = (timestamp) => {
      if (!timestamp) return '--';
      const date = new Date(timestamp);
      return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    };
    
    return {
      priceChangeClass,
      priceChangeText,
      priceChangeIcon,
      formatVolume,
      formatMarketCap,
      formatTime
    };
  }
};
</script>


<style scoped>
.watchlist-card {
  border-radius: var(--radius-md);
  background-color: var(--bg-white);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-normal);
  overflow: hidden;
  margin-bottom: var(--space-md);
}

.watchlist-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.watchlist-card-header {
  padding: var(--space-md);
  border-bottom: 1px solid var(--divider-color);
}

.stock-info {
  display: flex;
  flex-direction: column;
}

.stock-code {
  font-family: var(--font-mono);
  font-weight: 600;
  font-size: var(--text-md);
  color: var(--text-primary);
}

.stock-name {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin-top: var(--space-xs);
}

.stock-price {
  text-align: right;
}

.current-price {
  font-family: var(--font-data);
  font-size: var(--text-xl);
  font-weight: 700;
}

.price-change {
  font-size: var(--text-sm);
  margin-top: var(--space-xs);
}

.change-icon {
  width: 14px;
  height: 14px;
}

.watchlist-card-body {
  padding: var(--space-md);
  background-color: var(--bg-light);
}

.indicators {
  display: flex;
  justify-content: space-between;
}

.indicator {
  text-align: center;
  flex: 1;
}

.indicator-label {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  margin-bottom: var(--space-xs);
}

.indicator-value {
  font-family: var(--font-data);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-primary);
}

.watchlist-card-footer {
  padding: var(--space-md);
  border-top: 1px solid var(--divider-color);
}

.update-time {
  font-size: var(--text-xs);
  color: var(--text-secondary);
}

.actions {
  display: flex;
  gap: var(--space-sm);
}

.stock-up {
  color: var(--stock-up);
}

.stock-down {
  color: var(--stock-down);
}

@media (max-width: 768px) {
  .watchlist-card-footer {
    flex-direction: column;
    gap: var(--space-sm);
  }
  
  .update-time {
    order: 2;
  }
  
  .actions {
    order: 1;
    width: 100%;
    justify-content: space-between;
  }
}
</style>
