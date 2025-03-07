/**
 * 路由配置文件
 * 定义应用的页面路由和导航
 */
import { createRouter, createWebHistory } from 'vue-router'

// 使用路由懒加载，提高首屏加载速度
const routes = [
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/views/Layout.vue'),
    redirect: '/dashboard',
    children: [
      // 仪表盘/概览页面
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '概览', icon: 'HomeFilled' }
      },
      // 自选股管理
      {
        path: '/watchlist',
        name: 'Watchlist',
        component: () => import('@/views/Watchlist.vue'),
        meta: { title: '自选股', icon: 'Star' }
      },
      // LSTM预测
      {
        path: '/lstm-predict',
        name: 'LstmPredict',
        component: () => import('@/views/LstmPredict.vue'),
        meta: { title: 'LSTM预测', icon: 'TrendCharts' }
      },
      // LLM预测
      {
        path: '/llm-predict',
        name: 'LlmPredict',
        component: () => import('@/views/LlmPredict.vue'),
        meta: { title: 'LLM预测', icon: 'ChatLineRound' }
      },
      // 多策略预测
      {
        path: '/multi-strategy',
        name: 'MultiStrategy',
        component: () => import('@/views/MultiStrategy.vue'),
        meta: { title: '多策略分析', icon: 'SetUp' }
      },
      // 用户管理
      {
        path: '/users',
        name: 'UserManagement',
        component: () => import('@/views/UserManagement.vue'),
        meta: { title: '用户管理', icon: 'User' }
      },
      // 分析结果
      {
        path: '/analysis-result',
        name: 'AnalysisResult',
        component: () => import('@/views/AnalysisResult.vue'),
        meta: { title: '分析结果', icon: 'DataAnalysis' }
      },
      // 设置页面
      {
        path: '/settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { title: '系统设置', icon: 'Setting' }
      }
    ]
  },
  // 404页面
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue')
  }
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(), // 使用HTML5 History模式
  routes
})

// 全局路由守卫 - 设置页面标题
router.beforeEach((to, from, next) => {
  // 设置文档标题
  document.title = to.meta.title ? `${to.meta.title} - 股票分析预测系统` : '股票分析预测系统'
  next()
})

export default router 