import axios from 'axios'
import { ElMessage } from 'element-plus'

// 部署时通过 VITE_API_BASE 注入后端公网地址（如 Cloudflare 隧道 URL）；
// 未配置时回退到同源 /api（本地开发或后端同源部署场景）。
const API_BASE = import.meta.env.VITE_API_BASE || '/api'
// 前端 src/api/*.js 中的接口路径都不带 /api 前缀（如 /auth/login），
// 因此当 VITE_API_BASE 为完整后端域名时，需要自动补上 /api 路径前缀。
const baseURL = API_BASE === '/api' || API_BASE.endsWith('/api')
  ? API_BASE
  : API_BASE.replace(/\/$/, '') + '/api'

const service = axios.create({
  baseURL,
  timeout: 15000
})

// 请求拦截：注入 JWT
service.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截：统一错误处理
service.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res.code !== 0 && res.code !== undefined) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || 'Error'))
    }
    return res
  },
  (error) => {
    const status = error.response?.status
    if (status === 401) {
      ElMessage.error('登录已过期，请重新登录')
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    } else if (status === 403) {
      ElMessage.error('无权限执行该操作')
    } else {
      ElMessage.error(error.response?.data?.message || '网络错误')
    }
    return Promise.reject(error)
  }
)

export default service
