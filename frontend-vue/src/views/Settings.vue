<template>
  <div class="settings-container">
    <h1>系统设置</h1>
    
    <div class="settings-wrapper">
      <div class="settings-section">
        <h2>基本设置</h2>
        <div class="setting-item">
          <span class="setting-label">深色模式</span>
          <div class="setting-control">
            <input type="checkbox" id="dark-mode" v-model="settings.darkMode" @change="saveSettings">
            <label for="dark-mode">启用深色模式</label>
          </div>
        </div>
        
        <div class="setting-item">
          <span class="setting-label">数据刷新间隔</span>
          <div class="setting-control">
            <select v-model="settings.refreshInterval" @change="saveSettings">
              <option :value="30000">30秒</option>
              <option :value="60000">1分钟</option>
              <option :value="300000">5分钟</option>
              <option :value="600000">10分钟</option>
              <option :value="1800000">30分钟</option>
            </select>
          </div>
        </div>
        
        <div class="setting-item">
          <span class="setting-label">自选股最大数量</span>
          <div class="setting-control">
            <input 
              type="number" 
              v-model.number="settings.maxStocksInWatchlist" 
              min="10" 
              max="100" 
              @change="saveSettings"
            >
          </div>
        </div>
      </div>
      
      <div class="settings-section">
        <h2>分析设置</h2>
        <div class="setting-item">
          <span class="setting-label">默认分析截止日期</span>
          <div class="setting-control">
            <input type="date" v-model="settings.defaultEndDate" @change="saveSettings">
            <div class="setting-hint">留空表示使用当前日期</div>
          </div>
        </div>
      </div>
      
      <div class="settings-section">
        <h2>接口设置</h2>
        <div class="setting-item">
          <span class="setting-label">API服务地址</span>
          <div class="setting-control">
            <input type="text" v-model="settings.apiBaseUrl" @change="saveSettings">
            <div class="setting-hint">例如: http://localhost:8001</div>
          </div>
        </div>
        
        <div class="setting-item">
          <span class="setting-label">API状态</span>
          <div class="setting-control">
            <span class="api-status" :class="{ 'connected': isApiConnected }">
              {{ isApiConnected ? '已连接' : '未连接' }}
            </span>
            <button class="check-api-btn" @click="checkApiConnection">检查连接</button>
          </div>
        </div>
      </div>
      
      <div class="settings-section">
        <h2>操作</h2>
        <div class="setting-item button-group">
          <button class="primary-btn" @click="saveSettings">保存设置</button>
          <button class="secondary-btn" @click="resetSettings">重置默认设置</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Settings',
  data() {
    return {
      settings: {
        darkMode: false,
        refreshInterval: 60000,
        maxStocksInWatchlist: 50,
        defaultEndDate: '',
        apiBaseUrl: 'http://localhost:8001'
      },
      isApiConnected: false
    };
  },
  mounted() {
    // 初始化设置
    this.loadSettings();
  },
  methods: {
    saveSettings() {
      localStorage.setItem('sequoia-settings', JSON.stringify(this.settings));
    },
    loadSettings() {
      const savedSettings = localStorage.getItem('sequoia-settings');
      if (savedSettings) {
        this.settings = { ...this.settings, ...JSON.parse(savedSettings) };
      }
    },
    resetSettings() {
      if (confirm('确定要重置所有设置为默认值吗？')) {
        this.settings = {
          darkMode: false,
          refreshInterval: 60000,
          maxStocksInWatchlist: 50,
          defaultEndDate: '',
          apiBaseUrl: 'http://localhost:8001'
        };
        this.saveSettings();
      }
    },
    checkApiConnection() {
      // 模拟API连接检查
      this.isApiConnected = true;
    }
  }
}
</script>

<style scoped>
.settings-container {
  padding: 20px;
}

h1 {
  margin-bottom: 20px;
  color: #303133;
}

.settings-wrapper {
  max-width: 800px;
}

.settings-section {
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  padding: 20px;
  margin-bottom: 20px;
}

h2 {
  font-size: 18px;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
  color: #303133;
}

.setting-item {
  display: flex;
  margin-bottom: 20px;
}

.setting-item:last-child {
  margin-bottom: 0;
}

.setting-label {
  width: 150px;
  padding-top: 6px;
  color: #606266;
  font-weight: 500;
}

.setting-control {
  flex: 1;
}

input[type="text"],
input[type="number"],
input[type="date"],
select {
  width: 100%;
  max-width: 350px;
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  transition: border-color 0.3s;
}

input[type="text"]:focus,
input[type="number"]:focus,
input[type="date"]:focus,
select:focus {
  outline: none;
  border-color: #409eff;
}

.setting-hint {
  margin-top: 5px;
  font-size: 12px;
  color: #909399;
}

.api-status {
  display: inline-block;
  padding: 6px 10px;
  border-radius: 4px;
  background-color: #f56c6c;
  color: white;
  margin-right: 10px;
}

.api-status.connected {
  background-color: #67c23a;
}

.check-api-btn {
  padding: 6px 10px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background-color: white;
  cursor: pointer;
  transition: all 0.3s;
}

.check-api-btn:hover {
  border-color: #409eff;
  color: #409eff;
}

.button-group {
  display: flex;
  gap: 15px;
}

.primary-btn, .secondary-btn {
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  font-weight: 500;
}

.primary-btn {
  background-color: #409eff;
  color: white;
  border: none;
}

.primary-btn:hover {
  background-color: #66b1ff;
}

.secondary-btn {
  background-color: white;
  color: #606266;
  border: 1px solid #dcdfe6;
}

.secondary-btn:hover {
  border-color: #409eff;
  color: #409eff;
}
</style> 