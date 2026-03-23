import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  // 从环境变量读取允许的 hosts，多个用逗号分隔
  const allowedHosts = env.VITE_ALLOWED_HOSTS
    ? env.VITE_ALLOWED_HOSTS.split(',').map((h: string) => h.trim()).filter(Boolean)
    : []

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      port: 5173,
      allowedHosts: allowedHosts.length > 0 ? allowedHosts : undefined,
      proxy: {
        // 代理所有 /api/* 请求到后端
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          // 不重写路径，保持 /api/* 结构
          rewrite: (path) => path,
          configure: (proxy) => {
            // 禁用请求缓冲，实现流式上传
            proxy.on('proxyReq', (proxyReq, req, res) => {
              console.log('[Proxy]', req.method, req.url)
              // 对于大文件上传，确保流式传输
              if (req.method === 'POST' && req.url?.includes('/upload/')) {
                proxyReq.setHeader('Expect', '100-continue')
              }
            })
          },
        },
        '/ws': {
          target: 'ws://localhost:8000',
          ws: true,
        },
      },
    },
  }
})
