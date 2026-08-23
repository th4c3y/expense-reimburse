import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 部署说明：
// - 本地开发：npm run dev，/api 由 dev server 代理到 Flask 后端(5000)
// - GitHub Pages 部署：请将下方 base 改为你的仓库名，例如 '/expense-reimbursement/'
//   并设置环境变量 VITE_API_BASE 指向后端地址（如 https://your-backend.com）
//   构建：npm run build -> 产物在 dist/，由 ci.yml 自动发布到 GitHub Pages

const PAGES_BASE = process.env.VITE_PAGES_BASE || '/'

export default defineConfig({
  plugins: [vue()],
  base: PAGES_BASE,
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true
      }
    }
  }
})
