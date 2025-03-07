/* eslint-disable no-undef */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import { useWatchlistStore } from '@/stores/watchlist'
import { useThemeStore } from '@/stores/theme'

// 导入API模块
import * as watchlistApi from '@/api/watchlist';
import * as stockApi from '@/api/stock';

// 导入组件
import Watchlist from '@/components/Watchlist.vue';
import LstmPredict from '@/views/LstmPredict.vue';
import Settings from '@/views/Settings.vue';
import ThemeSwitch from '@/components/ThemeSwitch.vue'

// 导入store
import { useSystemStore } from '@/store/system';

// 设置Pinia
setActivePinia(createPinia())

describe('核心功能测试', () => {
  describe('自选股功能', () => {
    beforeEach(() => {
      // 创建一个新的 Pinia 实例并使其处于激活状态
      setActivePinia(createPinia())
      
      // 重置所有模拟
      vi.resetAllMocks()
      
      // 模拟localStorage
      vi.spyOn(localStorage, 'getItem').mockImplementation((key) => {
        if (key === 'watchlist') return JSON.stringify([])
        return null
      })
      
      vi.spyOn(localStorage, 'setItem').mockImplementation(() => {})
    })
    
    it('可以添加股票到自选股', () => {
      const watchlistStore = useWatchlistStore()
      const stockInfo = { code: '000001', name: '平安银行' }
      
      watchlistStore.addStock(stockInfo)
      
      expect(watchlistStore.stocks).toContainEqual(stockInfo)
      expect(localStorage.setItem).toHaveBeenCalledWith('watchlist', JSON.stringify([stockInfo]))
    })
    
    it('可以从自选股中移除股票', () => {
      const watchlistStore = useWatchlistStore()
      const stockInfo = { code: '000001', name: '平安银行' }
      
      watchlistStore.addStock(stockInfo)
      watchlistStore.removeStock('000001')
      
      expect(watchlistStore.stocks).toEqual([])
    })
    
    it('自选股组件应该正确渲染', () => {
      const wrapper = shallowMount(Watchlist, {
        global: {
          plugins: [createPinia()],
          stubs: {
            'el-table': true,
            'el-table-column': true,
            'el-button': true,
            'el-empty': true,
            'el-dialog': true,
            'el-icon': true
          }
        }
      })
      expect(wrapper.exists()).toBe(true)
    })
  })
  
  describe('深色模式功能', () => {
    beforeEach(() => {
      // 创建一个新的 Pinia 实例并使其处于激活状态
      setActivePinia(createPinia())
      
      // 重置所有模拟
      vi.resetAllMocks()
      
      // 模拟localStorage
      vi.spyOn(localStorage, 'getItem').mockImplementation((key) => {
        if (key === 'theme') return JSON.stringify({ isDark: false })
        return null
      })
      
      vi.spyOn(localStorage, 'setItem').mockImplementation(() => {})
      
      // 模拟document.documentElement.classList
      document.documentElement.classList = {
        add: vi.fn(),
        remove: vi.fn(),
        contains: vi.fn()
      }
    })
    
    it('可以切换主题', () => {
      const themeStore = useThemeStore()
      
      // 模拟classList.add方法
      const addSpy = vi.spyOn(document.documentElement.classList, 'add')
      
      themeStore.toggleTheme()
      
      expect(themeStore.isDark).toBe(true)
      expect(localStorage.setItem).toHaveBeenCalledWith('theme', JSON.stringify({ isDark: true }))
      expect(addSpy).toHaveBeenCalledWith('dark')
    })
    
    it('主题切换组件应该正确渲染', () => {
      const wrapper = shallowMount(ThemeSwitch, {
        global: {
          plugins: [createPinia()],
          stubs: {
            'el-icon': true
          }
        }
      })
      expect(wrapper.exists()).toBe(true)
    })
  })
})

// 删除股票搜索功能测试，因为相关API尚未实现
// describe('股票搜索功能测试', () => {
//   it('股票搜索功能应该支持模糊搜索', async () => {
//     // 此测试将在API实现后添加
//   })
// }) 