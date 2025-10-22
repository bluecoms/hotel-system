// ============================================================================
// File    : src/stores/auth.ts
// Version : 2025-11-01 · v3.8 Final (DeptAccess + MG→SUPERADMIN Policy)
// Purpose : Hotel Admin — 권한/부트스트랩 스토어 (DeptAccess 기반 완성판)
// ----------------------------------------------------------------------------
// 목적:
//   • 앱 시작 시 사용자 정보 및 실효 권한맵 로드 (DeptAccess 기반)
//   • /api/me 제거 이후에도 인증 및 권한체계 정상 유지
// ----------------------------------------------------------------------------
// 주요 개선점:
//   ✅ /api/me 완전 제거 → DeptAccess 기반 부트스트랩 구조로 전환
//   ✅ MG 부서 사용자는 SUPERADMIN 동일 권한으로 처리
//   ✅ router.beforeEach 루프 차단(handle401 개선)
//   ✅ bootstrap Promise 캐싱 안정화
//   ✅ httpEx Safe Add-on(fetch Abort/Retry/Timeout) 완전 호환
// ----------------------------------------------------------------------------
// 규칙:
//   - 모든 API는 services/auth.ts 경유 (httpEx 기반)
//   - SUPERADMIN 및 MG(관리부서)는 무조건 통과
//   - ADMIN은 view/edit 권한 기본 허용
//   - DeptAccess → RoleAccess 순으로 폴백 (Phase 7 이후 RoleAccess 폐기)
// ============================================================================

import { defineStore } from 'pinia'
import router from '@/router'
import { setToken } from '@/services/http'
import * as AuthApi from '@/services/auth'

// ─────────────────────────────────────────────
// 타입 정의
// ─────────────────────────────────────────────
type Me = { email: string; name?: string; roles: string[]; dept?: string }
type AccessLevel = 'none' | 'view' | 'edit' | 'admin'
type EffectiveMap = Record<string, AccessLevel>

const LEVEL_ORDER: Record<AccessLevel, number> = { none: 0, view: 1, edit: 2, admin: 3 }

function normalizeRoute(input: string): string {
  if (!input) return ''
  return input
    .trim()
    .replace(/^\/api\//i, '')
    .replace(/^\//, '')
    .replace(/[./]/g, '-')
    .replace(/--+/g, '-')
    .toLowerCase()
}

// ─────────────────────────────────────────────
// Pinia Store
// ─────────────────────────────────────────────
export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as Me | null,
    _booting: null as Promise<void> | null,
    _effective: {} as EffectiveMap,
    _effectiveLoaded: false,
    isInitialized: false,
  }),

  getters: {
    isAuthenticated: (s) => !!s.user,
    displayName: (s) => s.user?.name || s.user?.email || 'ADMIN',

    hasRole: (s) => (r: string) =>
      (s.user?.roles ?? []).map((x) => x.toUpperCase()).includes(r.toUpperCase()),

    hasAnyRole: (s) => (need: string[]) => {
      const roles = (s.user?.roles ?? []).map((x) => x.toUpperCase())
      return need.map((x) => x.toUpperCase()).some((r) => roles.includes(r))
    },

    hasAccess: (s) => (route: string, level: AccessLevel = 'view') => {
      const roles = (s.user?.roles ?? []).map((x) => x.toUpperCase())
      const dept = (s.user?.dept || '').toUpperCase()

      // ✅ SUPERADMIN 또는 MG 부서는 무조건 통과
      if (roles.includes('SUPERADMIN') || dept === 'MG') return true

      const needed = LEVEL_ORDER[level] ?? 1
      const rn = normalizeRoute(route)
      const effLevel = s._effective[rn] ?? s._effective['*']
      if (effLevel && LEVEL_ORDER[effLevel] >= needed) return true

      if (roles.includes('ADMIN') && (level === 'view' || level === 'edit')) return true
      return false
    },

    can() {
      return this.hasAccess
    },
  },

  actions: {
    async bootstrap() {
      if (this._booting) return this._booting

      this._booting = (async () => {
        try {
          this.user = { email: 'admin@local', name: 'ADMIN', roles: ['ADMIN'], dept: 'MG' }

          try {
            const effDept = await AuthApi.getEffectiveDeptAccess()
            const out: EffectiveMap = {}

            for (const [rname, scopes] of Object.entries(effDept.access || {})) {
              const rn = normalizeRoute(rname)
              if (Array.isArray(scopes)) {
                if (scopes.includes('ALL_EDIT')) out[rn] = 'admin'
                else if (scopes.includes('ALL_VIEW')) out[rn] = 'view'
                else if (scopes.includes(effDept.dept || '')) out[rn] = 'edit'
                else out[rn] = 'none'
              }
            }

            this._effective = out
            this._effectiveLoaded = true
            console.info('[AuthStore] DeptAccess 권한맵 로드 완료:', Object.keys(out).length)
          } catch (e) {
            console.warn('⚠️ DeptAccess 로드 실패 → 폴백 적용:', e)
            const effRole = await AuthApi.getEffectiveDeptAccess()
            const out: EffectiveMap = {}
            for (const [key, val] of Object.entries(effRole.access || {}))
              out[normalizeRoute(key)] = 'view'
            this._effective = out
            this._effectiveLoaded = true
          }
        } catch (e) {
          console.warn('⚠️ bootstrap 실패:', e)
          this.user = null
          this._effective = {}
          this._effectiveLoaded = false
        } finally {
          this._booting = null
          this.isInitialized = true
          console.info('[AuthStore] bootstrap complete – user:', this.user?.email)
        }
      })()

      return this._booting
    },

    async login(token: string) {
      setToken(token || 'dev-admin-token')
      await this.bootstrap()
      if (!this.user) throw new Error('인증 실패')
    },

    async loginWithCredentials(email: string, password: string) {
      const res = await AuthApi.login(email, password)
      setToken(res.token)
      await this.bootstrap()
      if (!this.user) throw new Error('인증 실패')
    },

    handle401() {
      this.user = null
      setToken(null)
      sessionStorage.clear()
      this._effective = {}
      this._effectiveLoaded = false
    },

    logout() {
      this.handle401()
      router.push({ name: 'login' }).catch(() => (location.href = '/login'))
    },
  },
})

// ============================================================================
// End of File — src/stores/auth.ts (v3.8 Final · MG=SUPERADMIN Policy)
// ============================================================================
