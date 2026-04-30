import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'

const TOKEN_KEY = 'rag_token'

function parseJwt(token: string): Record<string, unknown> {
  try {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    return JSON.parse(atob(base64))
  } catch {
    return {}
  }
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => {
    if (!token.value) return false
    return !!parseJwt(token.value).is_admin
  })
  const username = computed(() => {
    if (!token.value) return ''
    return String(parseJwt(token.value).sub ?? '')
  })

  async function login(u: string, password: string) {
    const resp = await authApi.login(u, password)
    token.value = resp.access_token
    localStorage.setItem(TOKEN_KEY, resp.access_token)
  }

  function logout() {
    token.value = null
    localStorage.removeItem(TOKEN_KEY)
  }

  return { token, isLoggedIn, isAdmin, username, login, logout }
})
