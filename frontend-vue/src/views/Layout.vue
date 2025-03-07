<!-- 
  主页面布局组件
  包含侧边栏导航菜单和主内容区域
-->
<template>
  <div class="layout-container">
    <!-- 侧边栏导航 -->
    <el-container class="main-container">
      <el-aside width="220px" class="sidebar">
        <div class="logo-container">
          <h2>SequoiaMQ</h2>
        </div>
        
        <!-- 导航菜单 -->
        <el-menu
          router
          :default-active="activeMenu"
          background-color="#001529"
          text-color="#ffffff"
          active-text-color="#409EFF">
          
          <!-- 仪表盘 -->
          <el-menu-item index="/dashboard">
            <el-icon><HomeFilled /></el-icon>
            <span>概览</span>
          </el-menu-item>
          
          <!-- 自选股管理 -->
          <el-menu-item index="/watchlist">
            <el-icon><Star /></el-icon>
            <span>自选股</span>
          </el-menu-item>
          
          <!-- 分析相关 -->
          <el-sub-menu index="analysis">
            <template #title>
              <el-icon><DataAnalysis /></el-icon>
              <span>分析预测</span>
            </template>
            
            <el-menu-item index="/multi-strategy">
              <el-icon><SetUp /></el-icon>
              <span>多策略分析</span>
            </el-menu-item>
            
            <el-menu-item index="/analysis-result">
              <el-icon><DataAnalysis /></el-icon>
              <span>分析结果</span>
            </el-menu-item>
          </el-sub-menu>
          
          <!-- 预测相关 -->
          <el-sub-menu index="predict">
            <template #title>
              <el-icon><TrendCharts /></el-icon>
              <span>人工智能预测</span>
            </template>
            
            <el-menu-item index="/lstm-predict">
              <el-icon><TrendCharts /></el-icon>
              <span>LSTM预测</span>
            </el-menu-item>
            
            <el-menu-item index="/llm-predict">
              <el-icon><ChatLineRound /></el-icon>
              <span>LLM预测</span>
            </el-menu-item>
          </el-sub-menu>
          
          <!-- 系统管理 -->
          <el-sub-menu index="system">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>系统管理</span>
            </template>
            
            <el-menu-item index="/users">
              <el-icon><User /></el-icon>
              <span>用户管理</span>
            </el-menu-item>
            
            <el-menu-item index="/settings">
              <el-icon><Tools /></el-icon>
              <span>系统设置</span>
            </el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-aside>
      
      <!-- 主内容区域 -->
      <el-container>
        <el-header class="header">
          <div class="header-left">
            <el-breadcrumb separator="/">
              <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
              <el-breadcrumb-item>{{ $route.meta.title }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          <div class="header-right">
            <el-dropdown>
              <span class="user-dropdown">
                <el-avatar :size="32" :src="userAvatar" />
                <span class="user-name">管理员</span>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item>个人中心</el-dropdown-item>
                  <el-dropdown-item>退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>
        
        <el-main>
          <!-- 路由视图 -->
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <keep-alive>
                <component :is="Component" />
              </keep-alive>
            </transition>
          </router-view>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { 
  HomeFilled, 
  Star, 
  DataAnalysis, 
  TrendCharts, 
  Setting, 
  ChatLineRound, 
  SetUp,
  User,
  Tools
} from '@element-plus/icons-vue'

const route = useRoute()
const activeMenu = computed(() => route.path)
const userAvatar = ref('https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png')
</script>

<style scoped>
.layout-container {
  height: 100vh;
  width: 100%;
}

.main-container {
  height: 100%;
}

.sidebar {
  background-color: #001529;
  color: #ffffff;
  height: 100%;
  overflow-y: auto;
}

.logo-container {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  background-color: #002140;
}

.header {
  background-color: #ffffff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-dropdown {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.user-name {
  margin-left: 10px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style> 