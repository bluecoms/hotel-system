// ============================================================================
// File      : src/stores/auth.ts
// Version   : 2025.11-04 · v3.9 (DeptAccess Reactive Store Full)
// Purpose   : Hotel Admin — 인증 / 부서권한(DeptAccess) / 실효맵 스토어
// ----------------------------------------------------------------------------
// 목적:
//   • /api/me + /api/roles/access/effective 기반 사용자 및 권한맵 부트스트랩
//   • DeptAccess Phase3.9 구조 반영 (deptAccess + effectiveDeptAccess 병행 유지)
//   • 라우터 가드(src/router/index.ts)와 완전 호환 (reactive 접근)
// ----------------------------------------------------------------------------
// 주요 상태(State)
//   user                : 로그인 사용자
//   deptCode            : 부서 코드 (MOP 등)
//   deptAccess          : route_name → scopes[] (간소 map)
//   effectiveDeptAccess : { dept, access } (서버 실효맵 전체)
//   isInitialized       : 부트스트랩 완료 플래그
// ----------------------------------------------------------------------------
// 주요 함수(Actions)
//   bootstrap()         : 사용자 및 권한맵 로드
//   hasDeptAccess()     : DeptAccess 기반 권한 체크
//   can()               : 레거시 호환 (RoleAccess)
//   hasRole()           : 단순 Role 검사
//   logout()            : 상태 초기화
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
export type EffectiveDeptAccess = {
  dept?: string
  access: Record<string, string[]>
}

// ─────────────────────────────────────────────
// 스토어 정의
// ─────────────────────────────────────────────
export const useAuthStore = defineStore('auth', {
  // --------------------------------------------------------------------------
  // 상태(State)
  // --------------------------------------------------------------------------
  state: () => ({
    user: null as Me | null,                        // 사용자 객체
    deptCode: 'MOP' as string,                      // 기본 부서코드
    deptAccess: {} as Record<string, string[]>,     // 단순 맵(route_name→scopes)
    effectiveDeptAccess: null as EffectiveDeptAccess | null, // ✅ 서버 실효 권한맵
    _booting: null as Promise<void> | null,         // 중복호출 방지용 Promise
    isInitialized: false as boolean,                // 부트스트랩 완료 플래그
  }),

  // --------------------------------------------------------------------------
  // 게터(Getters)
  // --------------------------------------------------------------------------
  getters: {
    /** 로그인 여부 */
    isAuthenticated: (s) => !!s.user,
    /** 표시용 이름 (없으면 이메일) */
    displayName: (s) => s.user?.name || s.user?.email || 'ADMIN',
  },

  // --------------------------------------------------------------------------
  // 액션(Actions)
  // --------------------------------------------------------------------------
  actions: {
    /**
     * 초기 부트스트랩
     * - /api/me → 사용자 로드
     * - /api/roles/access/effective → DeptAccess 권한맵 로드
     * - effectiveDeptAccess 필드까지 reactive 상태로 유지
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
            // 단순 맵/전체맵 모두 저장
            this.effectiveDeptAccess = eff
            this.deptAccess = eff.access || {}
            if (eff.dept) this.deptCode = eff.dept
            console.log('[AuthStore] DeptAccess 권한맵 로딩 완료')
          } else {
            console.warn('[AuthStore] /roles/access/effective 응답 형식 불일치', eff)
            this.effectiveDeptAccess = { dept: this.deptCode, access: {} }
            this.deptAccess = {}
          }
        } catch (e) {
          console.warn('[AuthStore] DeptAccess 로드 실패', e)
          this.effectiveDeptAccess = { dept: this.deptCode, access: {} }
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
     */
    can(route: string, level: string): boolean {
      const lvl = String(level || '').toLowerCase()
      const required =
        lvl === 'edit' || lvl === 'admin' ? 'ALL_EDIT' : 'ALL_VIEW'
      return this.hasDeptAccess(route, required)
    },

    /**
     * 역할(Role) 검사 (SUPERADMIN 등)
     */
    hasRole(role: string): boolean {
      return !!this.user?.roles?.map(r => r.toUpperCase()).includes(role.toUpperCase())
    },

    /**
     * 로그아웃 — 상태 전체 초기화
     */
    logout() {
      try {
        this.user = null
        this.deptAccess = {}
        this.effectiveDeptAccess = null
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
// 유틸 함수: route 정규화 (백엔드 DeptAccess 키 규칙과 동일)
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
