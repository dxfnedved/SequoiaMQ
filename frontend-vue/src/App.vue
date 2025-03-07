<template>
  <div id="app">
    <!-- 使用路由视图展示当前路由组件 -->
    <router-view v-slot="{ Component }">
      <!-- 添加过渡动画 -->
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<script>
/**
 * 应用程序根组件
 * 作为整个应用的容器，包含全局的应用结构和布局
 */
export default {
  name: 'App',
}
</script>

<style lang="scss">
@import "@/assets/styles/variables.scss";
@import 'element-plus/dist/index.css';
@import '@/assets/styles/global.scss';
@import '@/assets/styles/theme.css';

/* 确保所有页面有一致的基础布局 */
#app {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--text-primary, $text-primary);
  background-color: var(--bg-primary, $background-color-base);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 修复首页与其他页面的样式一致性 */
.el-main {
  padding: $spacing-medium;
  background-color: var(--bg-primary, $background-color-base);
}

/* 确保输入框和搜索组件样式一致 */
.stock-search-container {
  width: 100%;
  position: relative;
  z-index: 100;
  
  .search-input-wrapper {
    position: relative;
    width: 100%;
  }
  
  .search-input {
    width: 100%;
    height: 40px;
    padding: 8px 16px 8px 40px;
    border-radius: $border-radius-base;
    border: 1px solid $border-color-base;
    transition: all 0.3s;
    background-color: #fff;
    
    &:focus {
      border-color: $primary-color;
      box-shadow: 0 0 0 2px rgba($primary-color, 0.2);
      outline: none;
    }
  }
  
  .search-icon {
    position: absolute;
    left: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: $text-color-secondary;
  }
  
  .search-results {
    position: absolute;
    width: 100%;
    max-height: 300px;
    overflow-y: auto;
    background-color: #fff;
    border-radius: $border-radius-base;
    box-shadow: $box-shadow-base;
    margin-top: 4px;
    z-index: 10;
  }
}
</style> 