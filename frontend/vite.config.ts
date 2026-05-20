import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5174,
    proxy: {
      // 自动代理所有后端 API 路由至 FastAPI 端口
      '/api': {
        target: 'http://localhost:9091',
        changeOrigin: true
      }
    }
  }
})
