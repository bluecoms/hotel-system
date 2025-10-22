// ============================================================================
// File      : vite.config.ts
// Version   : 2025.10-22 Final Stable
// Purpose   : Hotel Admin — Vite Development Config (Proxy + Vuetify)
// ----------------------------------------------------------------------------
// 목적:
//   • 개발 모드에서 프런트엔드 → FastAPI 백엔드 API 프록시 설정
//   • 헤더(X-Internal-Token) 손실 방지 및 dev 인증 헤더 자동 전달
//   • Vuetify / Vue3 기반 빌드 설정 및 정적 에셋 경로 변환(transformAssetUrls)
//
// 주요 개선 (v2025.10-22)
//   ✅ Vite 프록시가 X-Internal-Token 헤더를 FastAPI로 안전 전달
//   ✅ HTTPS / HOST / PORT 환경 변수 기반 설정 자동화
//   ✅ Vuetify plugin 및 transformAssetUrls 일원화
// ----------------------------------------------------------------------------
// 환경변수(.env):
//   • VITE_DEV_HOST=0.0.0.0
//   • VITE_DEV_PORT=5173
//   • VITE_DEV_PROXY_TARGET=http://192.168.0.6:8001
//   • VITE_API_BASE_URL=/api
//   • VITE_INTERNAL_TOKEN=dev-admin-token
// ----------------------------------------------------------------------------
// 참고:
//   • 개발 중: `npm run dev` 실행 시 /api → FastAPI 자동 프록시
//   • 운영 빌드: 프록시 비활성, Nginx 등에서 리버스 프록시 처리
// ============================================================================
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig(({ mode }) => {
  // ─────────────────────────────────────────────
  // ▣ 환경 변수 로드
  // ─────────────────────────────────────────────
  const env = loadEnv(mode, process.cwd(), '')
  const host = env.VITE_DEV_HOST || '0.0.0.0'
  const port = Number(env.VITE_DEV_PORT || 5173)
  const https = String(env.VITE_HTTPS || '').toLowerCase() === 'true'
  const proxyTarget = env.VITE_DEV_PROXY_TARGET || 'http://127.0.0.1:8001'

  return {
    // ─────────────────────────────────────────────
    // ▣ 플러그인 설정 (Vue + Vuetify)
    // ─────────────────────────────────────────────
    plugins: [
      vue({ template: { transformAssetUrls } }),
      vuetify(),
    ],

    // ─────────────────────────────────────────────
    // ▣ 경로 alias 설정
    // ─────────────────────────────────────────────
    resolve: {
      alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
    },

    // ─────────────────────────────────────────────
    // ▣ 개발 서버 설정 (Dev Server)
    // ─────────────────────────────────────────────
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

          // ✅ 추가: 내부 토큰 헤더(X-Internal-Token) 유지용 설정
          configure: (proxy) => {
            proxy.on('proxyReq', (proxyReq, req) => {
              const token = req.headers['x-internal-token']
              if (token) {
                proxyReq.setHeader('X-Internal-Token', token)
              }
            })
          },
        },
      },
    },

    // ─────────────────────────────────────────────
    // ▣ Preview 모드 설정
    // ─────────────────────────────────────────────
    preview: {
      host,
      port,
      https,
    },
  }
})
