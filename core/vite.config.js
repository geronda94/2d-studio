import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    {
      name: 'sceneengine-static-cors',
      configureServer(server) {
        server.middlewares.use((req, res, next) => {
          if (req.url && /^\/(models|vendor|rive)\//.test(req.url)) {
            res.setHeader('Access-Control-Allow-Origin', '*')
          }
          next()
        })
      },
    },
  ],
  server: {
    allowedHosts: true,
    proxy: {
      '/api': {
        target: process.env.BACKEND_URL || 'http://127.0.0.1:8002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/uploads': {
        target: process.env.BACKEND_URL || 'http://127.0.0.1:8002',
        changeOrigin: true
      },
      '/media': {
        target: process.env.BACKEND_URL || 'http://127.0.0.1:8002',
        changeOrigin: true
      }
    }
  }
})
