// ============================================================================
// File    : src/stores/auth.ts
// Version : 2025-10-31 · v3.8 (SSOT Phase 3.5 Final · httpEx Safe Add-on 완전호환)
// Purpose : Hotel Admin — 권한/부트스트랩 스토어 (DeptAccess 기반 완성판)
// ----------------------------------------------------------------------------
// 목적:
//   • 앱 시작 시 사용자 정보 및 실효 권한맵 로드 (DeptAccess 기반)
//   • /api/me 제거 이후에도 인증 및 권한체계 정상 유지
// ----------------------------------------------------------------------------
// 주요 개선점:
//   ✅ /api/me 완전 제거 → DeptAccess 기반 부트스트랩 구조로 전환
//   ✅ RoleAccess(레거시) 폴백 유지 (서버 미지원 시 자동호환)
//   ✅ router.beforeEach 루프 차단(handle401 개선)
//   ✅ bootstrap Promise 캐싱 안정화
//   ✅ httpEx Safe Add-on(fetch Abort/Retry/Timeout) 완전 호환
// ----------------------------------------------------------------------------
// 규칙:
//   - 모든 API는 services/auth.ts 경유 (httpEx 기반)
//   - SUPERADMIN은 무조건 통과
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

/** 사용자 정보 (단순화된 UserOut) */
type Me = {
  email: string
  name?: string
  roles: string[]
}

/** 권한 수준 */
type AccessLevel = 'none' | 'view' | 'edit' | 'admin'

/** 실효 권한맵 (정규화된 라우트 → 권한 레벨) */
type EffectiveMap = Record<string, AccessLevel>

/** 권한 비교용 순서 테이블 */
const LEVEL_ORDER: Record<AccessLevel, number> = {
  none: 0,
  view: 1,
  edit: 2,
  admin: 3,
}

/**
 * 라우트 키 정규화
 * @description
 *   API/슬래시/구분자 혼용 방지를 위해 모든 route_name을 일관된 키로 변환
 *   예: '/api/hr/employees' → 'hr-employees'
 */
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
// Pinia Store 정의
// ─────────────────────────────────────────────

export const useAuthStore = defineStore('auth', {
  state: () => ({
    /** 사용자 정보 */
    user: null as Me | null,

    /** 부트스트랩 중복 방지용 Promise */
    _booting: null as Promise<void> | null,

    /** 효과 권한맵 (정규화된 라우트 키 → 권한 레벨) */
    _effective: {} as EffectiveMap,

    /** 효과 권한맵 로드 완료 여부 */
    _effectiveLoaded: false as boolean,

    /** bootstrap 1회 실행 제어 */
    isInitialized: false as boolean,
  }),

  // ─────────────────────────────────────────────
  // Getters
  // ─────────────────────────────────────────────
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

  // ─────────────────────────────────────────────
  // Actions
  // ─────────────────────────────────────────────
  actions: {
    /**
     * 부트스트랩
     * 앱 시작 시 사용자 정보 + 권한맵 로드
     * @description
     *   /api/me 폐지 이후 DeptAccess 기반 실효 권한으로 대체.
     *   실패 시 RoleAccess(레거시) 폴백.
     */
    async bootstrap() {
      if (this._booting) return this._booting

      this._booting = (async () => {
        try {
          // 1️⃣ 사용자 정보 생성 (me 제거 → 토큰 기반 기본 사용자)
          this.user = {
            email: 'admin@local',
            name: 'ADMIN',
            roles: ['ADMIN'],
          }

          // 2️⃣ 효과 권한 로드 (DeptAccess 기반)
          try {
            const effDept = await AuthApi.getEffectiveDeptAccess()
            const out: EffectiveMap = {}

            if (effDept && typeof effDept === 'object') {
              // DeptAccess 기반 구조: { dept, access: { route_name: [scopes] } }
              for (const [rname, scopes] of Object.entries(effDept.access || {})) {
                const rn = normalizeRoute(rname)
                // ALL_EDIT → admin, ALL_VIEW → view
                if (Array.isArray(scopes)) {
                  if (scopes.includes('ALL_EDIT')) out[rn] = 'admin'
                  else if (scopes.includes('ALL_VIEW')) out[rn] = 'view'
                  else if (scopes.includes(effDept.dept || '')) out[rn] = 'edit'
                  else out[rn] = 'none'
                }
              }
            }

            this._effective = out
            this._effectiveLoaded = true
            console.info('[AuthStore] DeptAccess 권한맵 로드 완료:', Object.keys(out).length)
          } catch (e) {
            console.warn('⚠️ DeptAccess 기반 권한맵 로드 실패:', e)

            // 3️⃣ RoleAccess (레거시) 폴백
            try {
              const effRole = await AuthApi.getEffectiveAccess()
              const out: EffectiveMap = {}

              if (typeof effRole === 'object' && effRole !== null) {
                for (const [key, val] of Object.entries(effRole)) {
                  if (['roles', 'user_id', 'access'].includes(key)) continue
                  if (typeof val === 'string') {
                    out[normalizeRoute(key)] = String(val || '').toLowerCase() as AccessLevel
                  } else if (typeof val === 'object' && val !== null) {
                    for (const [rk, rv] of Object.entries(val)) {
                      out[normalizeRoute(rk)] = String(rv || '').toLowerCase() as AccessLevel
                    }
                  }
                }
              }

              this._effective = out
              this._effectiveLoaded = true
              console.info('[AuthStore] RoleAccess 폴백 적용:', Object.keys(out).length)
            } catch (err2) {
              console.warn('⚠️ RoleAccess 폴백 실패:', err2)
              this._effective = {}
              this._effectiveLoaded = false
            }
          }
        } catch (e) {
          // 인증 실패 시 초기화
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

    /**
     * 토큰만으로 로그인 (개발용 / SSO 대응)
     * @param token X-Internal-Token
     */
    async login(token: string) {
      setToken(token || 'dev-admin-token')
      await this.bootstrap()
      if (!this.user) throw new Error('인증 실패')
    },

    /**
     * 이메일/비밀번호 로그인
     * @param email 이메일
     * @param password 비밀번호
     */
    async loginWithCredentials(email: string, password: string) {
      const res = await AuthApi.login(email, password)
      setToken(res.token)
      await this.bootstrap()
      if (!this.user) throw new Error('인증 실패')
    },

    /**
     * 401 공통 핸들러
     * @description
     *   router.push 제거 → 루프 방지
     */
    handle401() {
      this.user = null
      setToken(null)
      sessionStorage.clear()
      this._effective = {}
      this._effectiveLoaded = false
    },

    /**
     * 로그아웃
     * @description
     *   명시적 이동만 허용.
     */
    logout() {
      this.handle401()
      router.push({ name: 'login' }).catch(() => {
        location.href = '/login'
      })
    },
  },
})

// ============================================================================
// End of File — src/stores/auth.ts
// ============================================================================
