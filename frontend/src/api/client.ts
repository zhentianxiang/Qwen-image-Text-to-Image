import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { storage } from '@/utils/storage'

const BASE_URL = import.meta.env.VITE_API_URL || '/api'

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 600000, // 10 minutes for long tasks
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 - 添加 Token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = storage.getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器 - 处理错误
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail: string }>) => {
    if (error.response?.status === 401) {
      // Token 过期或无效，清除存储并跳转登录
      storage.clear()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient
