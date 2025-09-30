// vite.config.ts
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const host = env.VITE_DEV_HOST || '0.0.0.0'
  const port = Number(env.VITE_DEV_PORT || 5317)            // ← 기본 5317
  const https = env.VITE_HTTPS === 'true'
  const proxyTarget = env.VITE_DEV_PROXY_TARGET || 'http://127.0.0.1:8000' // ← 백엔드 8000

  return {
    plugins: [
      vue({ template: { transformAssetUrls } }),
      vuetify(),
    ],
    resolve: {
      alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
    },
    server: {
      host,
      port,
      https,
      strictPort: true,
      proxy: {
        '/api': { target: proxyTarget, changeOrigin: true, secure: false },
      },
    },
    preview: {
      host,
      port,
      https,
    },
  }
})
