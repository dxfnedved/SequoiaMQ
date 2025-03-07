import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { systemApi } from '../api/system';

/**
 * 系统状态和设置管理
 */
export const useSystemStore = defineStore('system', () => {
  // 状态
  const settings = ref({
    darkMode: false,
    sidebarCollapsed: false,
    apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001',
    refreshInterval: 60000, // 数据刷新间隔，默认60秒
    maxStocksInWatchlist: 50, // 自选股最大数量
    defaultEndDate: '', // 默认分析截止日期，空表示当前日期
  });

  const systemStatus = ref({
    apiConnected: false,
    lastUpdated: null,
    serverTime: null,
    version: null,
    isInitialized: false,
    isLoading: false,
    error: null,
  });

  // 计算属性
  const isApiConnected = computed(() => systemStatus.value.apiConnected);
  const isDarkMode = computed(() => settings.value.darkMode);
  const isSidebarCollapsed = computed(() => settings.value.sidebarCollapsed);

  // 方法
  /**
   * 初始化系统设置，从服务器或本地存储加载
   */
  async function initialize() {
    try {
      systemStatus.value.isLoading = true;
      
      // 从本地存储加载设置
      loadSettingsFromStorage();
      
      // 获取系统状态
      await checkApiConnection();
      
      systemStatus.value.isInitialized = true;
      return true;
    } catch (error) {
      systemStatus.value.error = error.message || '初始化系统设置失败';
      console.error('初始化系统出错:', error);
      return false;
    } finally {
      systemStatus.value.isLoading = false;
    }
  }

  /**
   * 检查API连接状态
   */
  async function checkApiConnection() {
    try {
      const response = await systemApi.getSystemStatus();
      if (response && response.status === 'ok') {
        systemStatus.value.apiConnected = true;
        systemStatus.value.serverTime = response.server_time;
        systemStatus.value.version = response.version;
        systemStatus.value.lastUpdated = new Date().toISOString();
        return true;
      } else {
        systemStatus.value.apiConnected = false;
        return false;
      }
    } catch (error) {
      systemStatus.value.apiConnected = false;
      systemStatus.value.error = '无法连接到API服务器';
      console.error('API连接检查失败:', error);
      return false;
    }
  }

  /**
   * 切换深色/浅色模式
   */
  function toggleDarkMode() {
    settings.value.darkMode = !settings.value.darkMode;
    saveSettingsToStorage();
    // 添加DOM类以实现深色模式
    if (settings.value.darkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
  }

  /**
   * 切换侧边栏折叠状态
   */
  function toggleSidebar() {
    settings.value.sidebarCollapsed = !settings.value.sidebarCollapsed;
    saveSettingsToStorage();
  }

  /**
   * 保存设置到本地存储
   */
  function saveSettingsToStorage() {
    localStorage.setItem('sequoia-settings', JSON.stringify(settings.value));
  }

  /**
   * 从本地存储加载设置
   */
  function loadSettingsFromStorage() {
    try {
      const savedSettings = localStorage.getItem('sequoia-settings');
      if (savedSettings) {
        const parsedSettings = JSON.parse(savedSettings);
        settings.value = { ...settings.value, ...parsedSettings };
        
        // 应用深色模式设置
        if (settings.value.darkMode) {
          document.body.classList.add('dark-mode');
        } else {
          document.body.classList.remove('dark-mode');
        }
      }
    } catch (error) {
      console.error('加载设置失败:', error);
    }
  }

  /**
   * 更新系统设置
   */
  async function updateSettings(newSettings) {
    try {
      settings.value = { ...settings.value, ...newSettings };
      saveSettingsToStorage();
      
      // 如果有需要服务器端保存的设置，可以在这里添加API调用
      // await systemApi.updateSettings(newSettings);
      
      return true;
    } catch (error) {
      systemStatus.value.error = '更新设置失败';
      console.error('更新设置失败:', error);
      return false;
    }
  }

  /**
   * 重置系统设置为默认值
   */
  function resetSettings() {
    settings.value = {
      darkMode: false,
      sidebarCollapsed: false,
      apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001',
      refreshInterval: 60000,
      maxStocksInWatchlist: 50,
      defaultEndDate: '',
    };
    saveSettingsToStorage();
  }

  return {
    // 状态
    settings,
    systemStatus,
    // 计算属性
    isApiConnected,
    isDarkMode,
    isSidebarCollapsed,
    // 方法
    initialize,
    checkApiConnection,
    toggleDarkMode,
    toggleSidebar,
    updateSettings,
    resetSettings,
  };
}); 