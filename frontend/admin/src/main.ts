// ============================================================================
// File      : src/main.ts
// Version   : 2025.10-22 Final Stable
// Purpose   : Hotel Admin — Main Entry (Light-only / Auth + Property Sync)
// ----------------------------------------------------------------------------
// 변경사항 (v2025.10-22)
//   ✅ 초기 부트 단계에서 토큰 미존재 시 .env 토큰(dev-admin-token) 자동 주입
//   ✅ getToken()이 false여도 bootstrap() 항상 실행 (401 방지)
//   ✅ usePropertyStore().init() 초기화 (지점 코드 전역 동기화)
//   ✅ 전체 스타일 SSOT 규격 주석 통일
// ----------------------------------------------------------------------------
// 구성:
//   • Pinia / Vuetify / i18n / Router 초기화
//   • PropertyStore 및 AuthStore 부트스트랩
//   • env 토큰 보정 + 개발 환경(dev-admin-token) 대응
// ============================================================================
import './styles/_index.scss'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import vuetify from '@/plugins/vuetify'
import { i18n } from '@/i18n'
import { useAuthStore } from '@/stores/auth'
import { usePropertyStore } from '@/stores/property'
import { setToken, getToken } from '@/services/http'
import '@/styles/overlay.scss'

// ─────────────────────────────────────────────
// 앱 생성 및 공통 플러그인 등록
// ─────────────────────────────────────────────
const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(vuetify)
app.use(i18n)

// ─────────────────────────────────────────────
// 부트스트랩: Property + Auth
// ─────────────────────────────────────────────
;(async () => {
  const property = usePropertyStore()
  const auth = useAuthStore()

  // ✅ Property 초기화 (localStorage → Pinia)
  property.init()
  console.info('[main] Property initialized →', property.current)

  // ✅ 토큰이 비어있으면 env 내부 토큰(dev-admin-token 등) 주입
  if (!getToken()) {
    const fallback = import.meta.env.VITE_INTERNAL_TOKEN || 'dev-admin-token'
    setToken(fallback)
    console.warn('[main] Token injected from .env →', fallback)
  }

  // ✅ 항상 Auth 부트스트랩 실행
  try {
    await auth.bootstrap()
  } catch (err) {
    console.warn('[main] Auth bootstrap failed:', err)
  }

  // ✅ 애플리케이션 마운트
  app.mount('#app')
})()
