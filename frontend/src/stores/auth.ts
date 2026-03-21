import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { hashPassword } from '@/utils/crypto'

export interface User {
  id: string
  username: string
  email: string
  is_active: boolean
  is_admin: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)
  const initialized = ref(false)

  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)
  const isAdmin = computed(() => user.value?.is_admin ?? false)

  async function login(username: string, password: string) {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password: hashPassword(password) }),
    })

    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || '登录失败')
    }

    const data = await response.json()

    user.value = data.user
    accessToken.value = data.access_token
    refreshToken.value = data.refresh_token

    localStorage.setItem('auth_tokens', JSON.stringify({
      access: data.access_token,
      refresh: data.refresh_token,
    }))
  }

  async function logout() {
    user.value = null
    accessToken.value = null
    refreshToken.value = null
    localStorage.removeItem('auth_tokens')
  }

  async function restoreSession() {
    if (initialized.value) return

    const stored = localStorage.getItem('auth_tokens')
    if (stored) {
      try {
        const tokens = JSON.parse(stored)
        accessToken.value = tokens.access
        refreshToken.value = tokens.refresh

        // 获取用户信息
        const response = await fetch('/api/auth/me', {
          headers: { Authorization: `Bearer ${tokens.access}` },
        })
        if (response.ok) {
          user.value = await response.json()
        } else {
          // Token 无效，清除
          localStorage.removeItem('auth_tokens')
          accessToken.value = null
          refreshToken.value = null
        }
      } catch {
        localStorage.removeItem('auth_tokens')
        accessToken.value = null
        refreshToken.value = null
      }
    }
    initialized.value = true
  }

  return {
    user,
    accessToken,
    refreshToken,
    initialized,
    isAuthenticated,
    isAdmin,
    login,
    logout,
    restoreSession,
  }
})
