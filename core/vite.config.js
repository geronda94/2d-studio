import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    allowedHosts: true,
    proxy: {
      '/api': {
        target: process.env.BACKEND_URL || 'http://127.0.0.1:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/uploads': {
        target: process.env.BACKEND_URL || 'http://127.0.0.1:8001',
        changeOrigin: true
      },
      '/media': {
        target: process.env.BACKEND_URL || 'http://127.0.0.1:8001',
        changeOrigin: true
      }
    }
  }
})
