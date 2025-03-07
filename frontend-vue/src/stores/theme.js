import { defineStore } from 'pinia'

export const useThemeStore = defineStore('theme', {
  state: () => ({
    isDark: false
  }),
  
  actions: {
    toggleTheme() {
      this.isDark = !this.isDark
      this.saveTheme()
    },
    
    setTheme(isDark) {
      this.isDark = isDark
      this.saveTheme()
    },
    
    saveTheme() {
      localStorage.setItem('theme', JSON.stringify({ isDark: this.isDark }))
      
      // 应用主题到文档
      if (this.isDark) {
        document.documentElement.classList.add('dark')
      } else {
        document.documentElement.classList.remove('dark')
      }
    },
    
    loadTheme() {
      try {
        const savedTheme = localStorage.getItem('theme')
        if (savedTheme) {
          const { isDark } = JSON.parse(savedTheme)
          this.isDark = isDark
          this.saveTheme()
        }
      } catch (error) {
        console.error('加载主题设置失败:', error)
      }
    }
  }
}) 