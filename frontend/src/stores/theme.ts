import { defineStore } from 'pinia'
import { ref, watch, onMounted, onUnmounted } from 'vue'
import type { ThemeMode } from '@/types/theme'

const STORAGE_KEY = 'theme-preference'

export const useThemeStore = defineStore('theme', () => {
  const STORAGE_KEY = 'theme-preference'

  // 从本地存储加载主题偏好
  const savedTheme = localStorage.getItem(STORAGE_KEY) as ThemeMode | null
  const mode = ref<ThemeMode>(savedTheme || 'system')

  const systemTheme = ref<'light' | 'dark'>('light')

  // 获取系统主题偏好
  const getSystemTheme = (): 'light' | 'dark' => {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark'
    }
    return 'light'
  }

  // 获取当前实际主题
  const getActualTheme = (): 'light' | 'dark' => {
    if (mode.value === 'system') {
      return getSystemTheme()
    }
    return mode.value
  }

  // 设置主题
  const setTheme = (newMode: ThemeMode) => {
    mode.value = newMode
    localStorage.setItem(STORAGE_KEY, newMode)

    const actualTheme = newMode === 'system' ? getSystemTheme() : newMode
    applyTheme(actualTheme)
  }

  // 应用主题
  const applyTheme = (theme: 'light' | 'dark') => {
    const html = document.documentElement
    if (theme === 'dark') {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }
  }

  // 初始化主题
  const initTheme = () => {
    const actualTheme = getActualTheme()
    applyTheme(actualTheme)

    // 监听系统主题变化
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (mode.value === 'system') {
          applyTheme(e.matches ? 'dark' : 'light')
        }
      })
    }
  }

  // 监听模式变化
  watch(mode, (newMode) => {
    const actualTheme = newMode === 'system' ? getSystemTheme() : newMode
    applyTheme(actualTheme)
  })

  return {
    mode,
    setTheme,
    initTheme,
    getActualTheme,
    systemTheme,
  }
})
