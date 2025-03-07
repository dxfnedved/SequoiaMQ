<template>
  <div class="theme-switch" @click="toggleTheme">
    <el-icon v-if="themeStore.isDark"><Moon /></el-icon>
    <el-icon v-else><Sunny /></el-icon>
  </div>
</template>

<script>
import { Moon, Sunny } from '@element-plus/icons-vue'
import { useThemeStore } from '@/stores/theme'
import { onMounted } from 'vue'

export default {
  name: 'ThemeSwitch',
  components: {
    Moon,
    Sunny
  },
  setup() {
    const themeStore = useThemeStore()
    
    onMounted(() => {
      themeStore.loadTheme()
    })
    
    const toggleTheme = () => {
      themeStore.toggleTheme()
    }
    
    return {
      themeStore,
      toggleTheme
    }
  }
}
</script>

<style scoped>
.theme-switch {
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  transition: background-color 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.theme-switch:hover {
  background-color: var(--el-fill-color-light);
}

.dark .theme-switch:hover {
  background-color: var(--el-fill-color-darker);
}
</style> 