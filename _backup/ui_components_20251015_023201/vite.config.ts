// vite.config.ts
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const host = env.VITE_DEV_HOST || '0.0.0.0'
  const port = Number(env.VITE_DEV_PORT || 5173)
  const https = String(env.VITE_HTTPS || '').toLowerCase() === 'true'
  const proxyTarget = env.VITE_DEV_PROXY_TARGET || 'http://192.168.0.6:8001'

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
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
          secure: false,
          ws: false,
          headers: { 'X-Dev-Proxy': 'vite' },
        },
      },
    },
    preview: {
      host,
      port,
      https,
    },
  }
})
