import { describe, it, expect, beforeEach, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ThemeSwitch from '@/components/ThemeSwitch.vue'
import { useThemeStore } from '@/stores/theme'

describe('主题切换功能', () => {
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
  
  it('默认应该使用浅色主题', () => {
    const themeStore = useThemeStore()
    expect(themeStore.isDark).toBe(false)
  })
  
  it('可以切换到深色主题', () => {
    const themeStore = useThemeStore()
    themeStore.toggleTheme()
    expect(themeStore.isDark).toBe(true)
    expect(localStorage.setItem).toHaveBeenCalledWith('theme', JSON.stringify({ isDark: true }))
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
  
  it('点击主题切换按钮应该切换主题', async () => {
    const wrapper = shallowMount(ThemeSwitch, {
      global: {
        plugins: [createPinia()],
        stubs: {
          'el-icon': true
        }
      }
    })
    const themeStore = useThemeStore()
    
    // 模拟点击事件
    await wrapper.find('.theme-switch').trigger('click')
    
    expect(themeStore.isDark).toBe(true)
  })
  
  it('应该从localStorage加载主题设置', () => {
    // 先重置模拟
    vi.spyOn(localStorage, 'getItem').mockReset()
    
    // 模拟localStorage中存储的深色主题
    vi.spyOn(localStorage, 'getItem').mockImplementation((key) => {
      if (key === 'theme') return JSON.stringify({ isDark: true })
      return null
    })
    
    // 重新创建store以触发初始化
    setActivePinia(createPinia())
    const themeStore = useThemeStore()
    
    // 手动调用加载方法
    themeStore.loadTheme()
    
    expect(themeStore.isDark).toBe(true)
  })
}) 