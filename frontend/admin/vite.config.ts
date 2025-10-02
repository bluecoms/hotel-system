// vite.config.ts (수정본)
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const host = env.VITE_DEV_HOST || '0.0.0.0'
  const port = Number(env.VITE_DEV_PORT || 5317)          // dev 기본 포트
  const https = env.VITE_HTTPS === 'true'
  const proxyTarget = env.VITE_DEV_PROXY_TARGET || 'http://127.0.0.1:8000' // BE 8000

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
        // ✅ /api → 백엔드 /api 로 그대로 포워드 (rewrite 금지)
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
          secure: false,
          ws: false,
          // ✋ rewrite 사용 금지: 백엔드가 /api/* 라우팅을 그대로 받음
          // rewrite: (p) => p, // (주석 유지: 실수 방지용)
          // 편의 헤더(선택)
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
