/**
 * Vue3应用入口文件
 * 用于初始化应用程序，注册全局组件和插件
 */
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'
import './assets/styles/global.scss'
import './assets/styles/index.css'
import './assets/styles/modern-theme.css' // 导入新的现代主题样式
import * as ElementPlusIcons from '@element-plus/icons-vue'

// 创建Vue实例
const app = createApp(App)

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIcons)) {
  app.component(key, component)
}

// 注册Pinia状态管理
const pinia = createPinia()
app.use(pinia)

// 注册Element Plus
app.use(ElementPlus, {
  locale: zhCn, // 使用中文语言包
  size: 'default', // 设置组件默认尺寸
})

// 注册Vue Router
app.use(router)

// 全局错误处理
app.config.errorHandler = (err, vm, info) => {
  console.error('全局错误:', err)
  console.error('组件:', vm)
  console.error('错误信息:', info)
}

// 挂载应用
app.mount('#app')

// 开发环境日志
if (process.env.NODE_ENV === 'development') {
  console.log('应用已启动，运行在开发模式')
  console.log('路由配置:', router.getRoutes())
} 