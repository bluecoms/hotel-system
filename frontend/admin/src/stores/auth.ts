// ============================================================================
// File      : src/stores/auth.ts
// Version   : 2025.10-23 · DeptAccess Ready + Full Legacy Compat
// Purpose   : Hotel Admin — 인증/부서권한(DeptAccess) 스토어
// ----------------------------------------------------------------------------
//  목적
//   • /api/me + /api/roles/access/effective 두 API 기반 사용자/권한 부트스트랩
//   • DeptAccess 권한 시스템(Phase3.5) 완전 대응
//   • 구버전 호환: can(), isInitialized, logout() 포함
// ----------------------------------------------------------------------------
// ️ API
//   GET  /api/me
//   GET  /api/roles/access/effective
// ----------------------------------------------------------------------------
//  주요 상태
//   user            : 로그인 사용자
//   deptCode        : 부서 코드 (MOP 등)
//   deptAccess      : route_name → scope[]
//   isInitialized   : 부트스트랩 완료 플래그
// ----------------------------------------------------------------------------
//  주요 함수
//   bootstrap()     : 사용자 및 권한맵 로드
//   hasDeptAccess() : DeptAccess 기반 권한 체크
//   can()           : 레거시 호환용 (RoleAccess 시절 API)
//   hasRole()       : 단순 역할 확인
//   logout()        : 상태 초기화
// ============================================================================

import { defineStore } from 'pinia'
import http from '@/services/http'

// ─────────────────────────────────────────────
// 타입 정의
// ─────────────────────────────────────────────

/** 사용자 정보 (/api/me 응답 기준) */
type Me = {
  email: string
  name?: string
  roles?: string[]
  dept?: string
}

/** /api/roles/access/effective 응답 구조 */
type EffectiveDeptAccess = {
  dept?: string
  access: Record<string, string[]>
}

// ─────────────────────────────────────────────
// 스토어 정의
// ─────────────────────────────────────────────

export const useAuthStore = defineStore('auth', {
  // ───────────────────────────────────────────
  // 상태 (State)
  // ───────────────────────────────────────────
  state: () => ({
    user: null as Me | null,                   // 사용자 객체
    deptCode: 'MOP' as string,                 // 기본 부서코드
    deptAccess: {} as Record<string, string[]>,// route_name → scopes[]
    _booting: null as Promise<void> | null,    // 중복 호출 방지용 Promise
    isInitialized: false as boolean,           // ✅ 부트스트랩 완료 여부 (라우터 가드용)
  }),

  // ───────────────────────────────────────────
  // 게터 (Getters)
  // ───────────────────────────────────────────
  getters: {
    /** 로그인 여부 */
    isAuthenticated: (s) => !!s.user,

    /** 표시용 이름 (없으면 이메일) */
    displayName: (s) => s.user?.name || s.user?.email || 'ADMIN',
  },

  // ───────────────────────────────────────────
  // 액션 (Actions)
  // ───────────────────────────────────────────
  actions: {
    /**
     * 초기 부트스트랩
     * - /api/me → 사용자 로드
     * - /api/roles/access/effective → DeptAccess 권한맵 로드
     */
    async bootstrap() {
      if (this._booting) return this._booting

      this._booting = (async () => {
        // 1️⃣ 사용자 정보 로드
        try {
          const r: any = await http.get('me')
          const u: Me = r?.user ?? r ?? {}
          this.user = {
            email: u?.email ?? '',
            name: u?.name ?? (u?.email ?? ''),
            roles: Array.isArray(u?.roles) ? u.roles : [],
            dept: u?.dept,
          }
          if (u?.dept) this.deptCode = u.dept
        } catch (e) {
          console.warn('[AuthStore] /api/me 실패 — 비로그인 처리', e)
          this.user = null
        }

        // 2️⃣ DeptAccess 실효 권한맵 로드
        try {
          const eff = await http.get<EffectiveDeptAccess>('roles/access/effective')
          if (eff && typeof eff.access === 'object') {
            this.deptAccess = eff.access
            if (eff.dept) this.deptCode = eff.dept
            console.log('[AuthStore] DeptAccess 권한맵 로딩 완료')
          } else {
            console.warn('[AuthStore] /roles/access/effective 응답 형식 불일치', eff)
            this.deptAccess = {}
          }
        } catch (e) {
          console.warn('[AuthStore] DeptAccess 로드 실패', e)
          this.deptAccess = {}
        }

        // ✅ 초기화 완료 플래그
        this.isInitialized = true
      })()

      try {
        await this._booting
      } finally {
        this._booting = null
      }
    },

    /**
     * DeptAccess 기반 권한검사
     * @param routeName - 예: 'closing-calendar'
     * @param required  - 기본 'ALL_VIEW', 필요 시 'ALL_EDIT'
     * @returns boolean - 접근 가능 여부
     */
    hasDeptAccess(routeName: string, required: string = 'ALL_VIEW'): boolean {
      const map = this.deptAccess || {}
      const scopes = map[normalizeRoute(routeName)] || map['*'] || []

      // 권한 규칙:
      // ① ALL_EDIT → 전면 허용
      // ② required 권한 포함 시 허용
      // ③ 현 부서코드 포함 시 허용
      if (scopes.includes('ALL_EDIT')) return true
      if (scopes.includes(required)) return true
      if (scopes.includes(this.deptCode)) return true
      return false
    },

    /**
     * 레거시 호환용 can()
     * - RoleAccess 시절 코드(auth.can(route, level)) 대응
     * - 내부적으로 hasDeptAccess() 호출
     * @param route - 예: 'users' 또는 'closing-calendar'
     * @param level - 예: 'view' | 'edit' | 'admin'
     * @returns boolean
     */
    can(route: string, level: string): boolean {
      const lvl = String(level || '').toLowerCase()
      const required =
        lvl === 'edit' || lvl === 'admin' ? 'ALL_EDIT' : 'ALL_VIEW'
      return this.hasDeptAccess(route, required)
    },

    /**
     * 역할(Role) 검사
     * - SUPERADMIN 등 단순 RoleAccess 남은 부분 호환용
     * @param role - 예: 'SUPERADMIN'
     */
    hasRole(role: string): boolean {
      return !!this.user?.roles?.includes(role)
    },

    /**
     * 로그아웃
     * - 상태 초기화
     * - localStorage / 메모리 토큰 제거 (http 모듈이 관리)
     * - router 리다이렉트는 호출측에서 수행
     */
    logout() {
      try {
        this.user = null
        this.deptAccess = {}
        this.deptCode = 'MOP'
        this.isInitialized = false
        console.log('[AuthStore] 로그아웃 — 상태 초기화 완료')
      } catch (e) {
        console.warn('[AuthStore] logout 처리 중 예외', e)
      }
    },
  },
})

// ─────────────────────────────────────────────
// 유틸 함수: route 정규화 (백엔드 규칙과 동일)
// ─────────────────────────────────────────────
function normalizeRoute(raw: string): string {
  if (!raw) return ''
  let s = raw.trim()
  if (s.toLowerCase().startsWith('/api/')) s = s.slice(5)
  if (s.startsWith('/')) s = s.slice(1)
  s = s.replace(/\//g, '-').replace(/\./g, '-')
  while (s.includes('--')) s = s.replace(/--/g, '-')
  return s.toLowerCase()
}
