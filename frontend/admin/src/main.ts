// ============================================================================
// File      : src/main.ts
// Version   : 2025.11-01 · v3.7 (Login Redirect Safe · DevToken Guarded)
// Purpose   : Hotel Admin — Main Entry (Light-only / Auth + Property Sync)
// ----------------------------------------------------------------------------
// 목적:
//   • DeptAccess 기반 Auth 구조에 완전 호환 (me 제거 후 bootstrap 직결)
//   • 개발환경(dev-admin-token) 자동 주입, 운영환경에서는 /login 리다이렉트
//   • usePropertyStore().init() 통해 지점코드(X-Property-Code) 전역 동기화
//   • http.ts 와 동일한 인증정책(X-Internal-Token) 유지
// ----------------------------------------------------------------------------
// 개선사항 (v3.7)
//   ✅ APP_ENV=dev 일 때만 dev-admin-token 자동 주입
//   ✅ 운영환경(APP_ENV=prod)에서는 토큰 없으면 로그인 페이지로 이동
//   ✅ Auth bootstrap 실패 시도 1회 후 graceful fallback
//   ✅ 로그 구조 단일화 (console.info / warn / error 통일)
// ----------------------------------------------------------------------------
// 구성요소:
//   • Pinia / Vuetify / i18n / Router 초기화
//   • PropertyStore 및 AuthStore 부트스트랩
//   • Router mount 이전에 인증상태/지점코드 동기화
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
// 순서:
//   ① property.init()        → localStorage → Pinia 동기화
//   ② 토큰 확인 및 개발환경 토큰 주입 (prod는 /login 이동)
//   ③ auth.bootstrap() 실행  → DeptAccess 기반 권한 초기화
//   ④ mount()
// ─────────────────────────────────────────────
;(async () => {
  const property = usePropertyStore()
  const auth = useAuthStore()

  // ① Property 초기화
  property.init()
  console.info('[main] Property initialized →', property.current)

  // ② 토큰 체크
  const token = getToken()
  const appEnv = import.meta.env.VITE_APP_ENV?.trim()?.toLowerCase() || 'dev'

  if (!token) {
    if (appEnv === 'dev') {
      // ✅ 개발환경일 때만 dev-admin-token 자동 주입
      const fallback = import.meta.env.VITE_INTERNAL_TOKEN?.trim() || 'dev-admin-token'
      setToken(fallback)
      console.warn('[main] Dev mode token injected →', fallback)
    } else {
      // ✅ 운영환경일 때는 로그인 페이지로 이동
      console.warn('[main] No token → redirecting to login page')
      await router.push({ name: 'login' })
      return
    }
  }

  // ③ 인증부트스트랩
  try {
    await auth.bootstrap()
    console.info('[main] Auth bootstrap complete ✅ user:', auth.user?.email || 'unknown')
  } catch (err) {
    console.error('[main] Auth bootstrap failed ❌', err)
  }

  // ④ 애플리케이션 마운트
  app.mount('#app')
})()

// ============================================================================
// End of File — src/main.ts (v3.7)
// ============================================================================
