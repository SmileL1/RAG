import axios, { AxiosError } from 'axios'

const TOKEN_KEY = 'rag_token'

export const http = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// 请求拦截：自动带上 JWT
http.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 响应拦截：统一错误处理，401 自动跳转登录
http.interceptors.response.use(
  (resp) => resp,
  (err: AxiosError<{ detail?: string }>) => {
    if (err.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      window.location.href = '/login'
      return Promise.reject(new Error('未登录'))
    }
    const detail = err.response?.data?.detail || err.message
    return Promise.reject(new Error(detail))
  },
)
