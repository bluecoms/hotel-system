// ============================================================================
// File      : src/main.ts
// Version   : 2025.10-31 · v3.6 (DeptAccess Migration · Auth/Property Unified)
// Purpose   : Hotel Admin — Main Entry (Light-only / Auth + Property Sync)
// ----------------------------------------------------------------------------
// 변경사항 (v2025.10-31)
//   ✅ DeptAccess 기반 Auth 구조에 완전 호환
//   ✅ /api/me 제거 후에도 bootstrap() 항상 실행
//   ✅ dev-admin-token 자동 주입 (개발 환경 대응)
//   ✅ usePropertyStore().init() 호출 시 지점 코드 전역 반영
//   ✅ http.ts 의 X-Property-Code / X-Internal-Token 정책과 정합 유지
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
// ----------------------------------------------------------------------------
// - property.init() : localStorage → Pinia 동기화
// - 토큰 비어있으면 .env 또는 dev-admin-token 주입
// - auth.bootstrap() : DeptAccess 기반 권한 초기화
// - 이후 mount()
// ─────────────────────────────────────────────
;(async () => {
  const property = usePropertyStore()
  const auth = useAuthStore()

  // ✅ Property 초기화 (localStorage → Pinia)
  property.init()
  console.info('[main] Property initialized →', property.current)

  // ✅ 토큰이 비어있으면 env 내부 토큰(dev-admin-token 등) 자동 주입
  if (!getToken()) {
    const fallback = import.meta.env.VITE_INTERNAL_TOKEN?.trim() || 'dev-admin-token'
    setToken(fallback)
    console.warn('[main] Token injected from .env →', fallback)
  }

  // ✅ 항상 Auth 부트스트랩 실행 (DeptAccess 기반)
  try {
    await auth.bootstrap()
    console.info('[main] Auth bootstrap complete ✅')
  } catch (err) {
    console.warn('[main] Auth bootstrap failed ❌', err)
  }

  // ✅ 애플리케이션 마운트
  app.mount('#app')
})()
