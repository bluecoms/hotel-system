// ============================================================================
// Hotel Admin — src/stores/auth.ts  (권한/부트스트랩 스토어 · 2025-10-17 final)
// ----------------------------------------------------------------------------
// 목적:
//   - 앱 시작 시 사용자 정보/권한(효과 권한맵) 로드
//   - 라우팅 전 hasAccess(권한 검사) 제공
//
// 주요 개선점:
//   ✅ router.beforeEach 루프 차단 (handle401 → router.push 제거)
//   ✅ bootstrap Promise 캐싱 안정화
//   ✅ /user-roles/effective 구조 안전 처리
//
// 규칙:
//   - 모든 API는 services/auth.ts 를 통해 호출 (404 → 자동 폴백)
//   - http.ts 의 buildUrl 은 상대경로 기반 (예: 'me', 'user-roles/effective')
//   - SUPERADMIN 은 무조건 통과
// ============================================================================

import { defineStore } from 'pinia'
import router from '@/router'
import { setToken } from '@/services/http'
import * as AuthApi from '@/services/auth'

// ─────────────────────────────────────────────
// 타입 정의
// ─────────────────────────────────────────────
type Me = { email: string; name?: string; roles: string[] }
type AccessLevel = 'none' | 'view' | 'edit' | 'admin'
type EffectiveMap = Record<string, AccessLevel>

const LEVEL_ORDER: Record<AccessLevel, number> = {
  none: 0,
  view: 1,
  edit: 2,
  admin: 3,
}

/** 라우트 키 정규화: API/슬래시/구분자 혼용 방지 */
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

    // 부트스트랩 중복 방지용 Promise
    _booting: null as Promise<void> | null,

    // 효과 권한맵 (정규화된 라우트 키 → 권한 레벨)
    _effective: {} as EffectiveMap,
    _effectiveLoaded: false as boolean,

    // bootstrap 1회 실행 제어
    isInitialized: false as boolean,
  }),

  getters: {
    /** 로그인 여부 */
    isAuthenticated: (s) => !!s.user,

    /** 표시용 이름 */
    displayName: (s) => s.user?.name || s.user?.email || 'ADMIN',

    /** 특정 역할 보유 여부 */
    hasRole: (s) => (r: string) =>
      (s.user?.roles ?? []).map((x) => x.toUpperCase()).includes(r.toUpperCase()),

    /** 여러 역할 중 하나라도 있는지 */
    hasAnyRole: (s) => (need: string[]) => {
      const roles = (s.user?.roles ?? []).map((x) => x.toUpperCase())
      return need.map((x) => x.toUpperCase()).some((r) => roles.includes(r))
    },

    /**
     * 권한 체크
     * @param route 라우트/리소스 키 (예: 'hr/employees', '/api/hr/employees')
     * @param level 필요 권한 수준 (기본 view)
     */
    hasAccess: (s) => (route: string, level: AccessLevel = 'view') => {
      const roles = (s.user?.roles ?? []).map((x) => x.toUpperCase())
      if (roles.includes('SUPERADMIN')) return true

      const needed = LEVEL_ORDER[level] ?? 1
      const rn = normalizeRoute(route)

      // 1️⃣ 효과 권한맵
      const effLevel = s._effective[rn] ?? s._effective['*']
      if (effLevel && LEVEL_ORDER[effLevel] >= needed) return true

      // 2️⃣ ADMIN 기본 정책: view/edit 허용
      if (roles.includes('ADMIN') && (level === 'view' || level === 'edit')) return true

      return false
    },

    /** sugar alias */
    can() {
      return this.hasAccess
    },
  },

  actions: {
    /** 앱 시작 시 사용자/권한 로드 */
    async bootstrap() {
      if (this._booting) return this._booting

      this._booting = (async () => {
        try {
          // 1️⃣ 사용자 정보 로드
          const me = await AuthApi.getMe()
          const u = (me as any)?.user ?? me
          this.user = {
            email: u?.email ?? '',
            name: u?.name ?? (u?.email ?? ''),
            roles: Array.isArray(u?.roles) ? u.roles : [],
          }

          // 2️⃣ 효과 권한 로드
          try {
            const eff = await AuthApi.getEffectiveAccess()
            const out: EffectiveMap = {}

            if ((eff as any)?.access && typeof (eff as any).access === 'object') {
              for (const [rname, lvl] of Object.entries((eff as any).access)) {
                out[normalizeRoute(rname)] = String(lvl || '').toLowerCase() as AccessLevel
              }
            } else if (typeof eff === 'object' && eff !== null) {
              for (const [key, val] of Object.entries(eff as Record<string, any>)) {
                if (['roles', 'user_id', 'access'].includes(key)) continue
                if (typeof val === 'string') {
                  out[normalizeRoute(key)] = val.toLowerCase() as AccessLevel
                } else if (typeof val === 'object' && val !== null) {
                  for (const [rk, rv] of Object.entries(val)) {
                    out[normalizeRoute(rk)] = String(rv || '').toLowerCase() as AccessLevel
                  }
                }
              }
            }

            this._effective = out
            this._effectiveLoaded = true
          } catch (e) {
            console.warn('⚠️ 효과 권한맵 로드 실패:', e)
            this._effective = {}
            this._effectiveLoaded = false
          }
        } catch (e) {
          // 인증 실패 또는 /me 실패
          this.user = null
          this._effective = {}
          this._effectiveLoaded = false
        } finally {
          this._booting = null
        }
      })()

      return this._booting
    },

    /** 토큰만으로 로그인 (SSO/개발용) */
    async login(token: string) {
      setToken(token || 'dev-admin-token')
      await this.bootstrap()
      if (!this.user) throw new Error('인증 실패')
    },

    /** 이메일/비밀번호 로그인 */
    async loginWithCredentials(email: string, password: string) {
      const res = await AuthApi.login(email, password)
      setToken(res.token)
      await this.bootstrap()
      if (!this.user) throw new Error('인증 실패')
    },

    /** 401 공통 핸들러 (router.push 제거) */
    handle401() {
      this.user = null
      setToken(null)
      sessionStorage.clear()
      this._effective = {}
      this._effectiveLoaded = false
    },

    /** 로그아웃 (명시적 이동만 허용) */
    logout() {
      this.handle401()
      router.push({ name: 'login' }).catch(() => {
        location.href = '/login'
      })
    },
  },
})
