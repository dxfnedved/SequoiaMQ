<template>
  <div class="analysis-result-container">
    <h1>分析结果</h1>
    
    <div class="summary-section">
      <div class="summary-card">
        <div class="summary-header">
          <h3>统计摘要</h3>
        </div>
        <div class="summary-content">
          <div class="stat-item">
            <span class="stat-label">分析股票总数:</span>
            <span class="stat-value">{{ resultSummary.totalStocks }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">买入信号数量:</span>
            <span class="stat-value highlight-buy">{{ resultSummary.buySignals }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">卖出信号数量:</span>
            <span class="stat-value highlight-sell">{{ resultSummary.sellSignals }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">分析完成时间:</span>
            <span class="stat-value">{{ resultSummary.completionTime }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="result-tabs">
      <div class="tab-header">
        <div 
          v-for="tab in tabs" 
          :key="tab.key" 
          class="tab-item" 
          :class="{ 'active': activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </div>
      </div>
      
      <div class="tab-content">
        <div v-if="activeTab === 'buy'" class="result-list">
          <p class="empty-message" v-if="buyResults.length === 0">暂无买入信号</p>
          <div v-else class="stock-list">
            <div class="stock-item" v-for="(stock, index) in buyResults" :key="index">
              <div class="stock-header">
                <div class="stock-name">{{ stock.name }}</div>
                <div class="stock-code">{{ stock.code }}</div>
              </div>
              <div class="stock-body">
                <div class="signal-tag buy">买入</div>
                <div class="strategy-name">{{ stock.strategy }}</div>
                <div class="signal-strength">
                  信号强度: {{ stock.strength }}
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="activeTab === 'sell'" class="result-list">
          <p class="empty-message" v-if="sellResults.length === 0">暂无卖出信号</p>
          <div v-else class="stock-list">
            <div class="stock-item" v-for="(stock, index) in sellResults" :key="index">
              <div class="stock-header">
                <div class="stock-name">{{ stock.name }}</div>
                <div class="stock-code">{{ stock.code }}</div>
              </div>
              <div class="stock-body">
                <div class="signal-tag sell">卖出</div>
                <div class="strategy-name">{{ stock.strategy }}</div>
                <div class="signal-strength">
                  信号强度: {{ stock.strength }}
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="activeTab === 'all'" class="result-list">
          <p class="empty-message" v-if="allResults.length === 0">暂无分析结果</p>
          <div v-else class="stock-list">
            <div class="stock-item" v-for="(stock, index) in allResults" :key="index">
              <div class="stock-header">
                <div class="stock-name">{{ stock.name }}</div>
                <div class="stock-code">{{ stock.code }}</div>
              </div>
              <div class="stock-body">
                <div class="signal-tag" :class="stock.signal">{{ stock.signal === 'buy' ? '买入' : '卖出' }}</div>
                <div class="strategy-name">{{ stock.strategy }}</div>
                <div class="signal-strength">
                  信号强度: {{ stock.strength }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AnalysisResult',
  data() {
    return {
      activeTab: 'buy',
      tabs: [
        { key: 'buy', label: '买入信号' },
        { key: 'sell', label: '卖出信号' },
        { key: 'all', label: '全部结果' }
      ],
      resultSummary: {
        totalStocks: 3600,
        buySignals: 28,
        sellSignals: 15,
        completionTime: '2023-03-01 15:30:45'
      },
      // 示例数据
      buyResults: [
        { name: '平安银行', code: '000001', signal: 'buy', strategy: 'RSRS策略', strength: 0.85 },
        { name: '万科A', code: '000002', signal: 'buy', strategy: '低回撤上涨策略', strength: 0.76 },
        { name: '中国神华', code: '601088', signal: 'buy', strategy: '海龟交易策略', strength: 0.92 },
      ],
      sellResults: [
        { name: '贵州茅台', code: '600519', signal: 'sell', strategy: 'RSRS策略', strength: 0.68 },
        { name: '宁德时代', code: '300750', signal: 'sell', strategy: '低回撤上涨策略', strength: 0.73 },
      ],
    };
  },
  computed: {
    allResults() {
      return [...this.buyResults, ...this.sellResults].sort((a, b) => b.strength - a.strength);
    }
  }
}
</script>

<style scoped>
.analysis-result-container {
  padding: 20px;
}

h1 {
  margin-bottom: 20px;
  color: #303133;
}

.summary-section {
  margin-bottom: 20px;
}

.summary-card {
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.summary-header {
  background-color: #f5f7fa;
  padding: 15px 20px;
  border-bottom: 1px solid #ebeef5;
}

.summary-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.summary-content {
  padding: 20px;
  display: flex;
  flex-wrap: wrap;
}

.stat-item {
  width: 50%;
  min-width: 200px;
  margin-bottom: 15px;
}

.stat-label {
  color: #606266;
  margin-right: 10px;
}

.stat-value {
  font-weight: 500;
  color: #303133;
}

.highlight-buy {
  color: #67c23a;
}

.highlight-sell {
  color: #f56c6c;
}

.result-tabs {
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.tab-header {
  display: flex;
  background-color: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.tab-item {
  padding: 15px 20px;
  cursor: pointer;
  transition: all 0.3s;
  border-bottom: 2px solid transparent;
  color: #606266;
}

.tab-item:hover {
  color: #409eff;
}

.tab-item.active {
  color: #409eff;
  border-bottom-color: #409eff;
}

.tab-content {
  padding: 20px;
}

.stock-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
}

.stock-item {
  background-color: #f5f7fa;
  border-radius: 4px;
  overflow: hidden;
  transition: all 0.3s;
  border: 1px solid #ebeef5;
}

.stock-item:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.stock-header {
  padding: 12px 15px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stock-name {
  font-weight: 500;
  color: #303133;
}

.stock-code {
  color: #909399;
  font-size: 13px;
}

.stock-body {
  padding: 15px;
  background-color: #fff;
}

.signal-tag {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  margin-right: 10px;
  color: white;
}

.signal-tag.buy {
  background-color: #67c23a;
}

.signal-tag.sell {
  background-color: #f56c6c;
}

.strategy-name {
  display: inline-block;
  margin-bottom: 10px;
  color: #606266;
}

.signal-strength {
  color: #303133;
  font-size: 13px;
}

.empty-message {
  text-align: center;
  color: #909399;
  padding: 30px 0;
}
</style> 