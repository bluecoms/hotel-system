// ============================================================================
// File    : src/services/auth.ts
// Version : 2025.11-05 · v3.9 (SSOT Unified · DeptAuto Fallback Fix)
// Purpose : Hotel Admin — 인증 / 권한 / 사용자 API (DeptAccess 기반 완성판)
// ----------------------------------------------------------------------------
// 목적:
//   • 프런트엔드 인증과 권한 로직을 httpEx(fetch 기반)으로 완전 일원화.
//   • DeptAccess 기반 권한 구조(SUPERADMIN 통합 / Fallback 자동화).
//   • ALL_EDIT / ALL_VIEW / 부서별 접근코드(FR, HK 등) 완전 대응.
// ----------------------------------------------------------------------------
// 주요 개선 (v3.9):
//   ✅ computeEffectiveDeptFromList() null-safe 개선
//   ✅ Fallback 시 dept 자동 추론 (MOP 하드코딩 제거)
//   ✅ SUPERADMIN 즉시 통과 로직 주석 명시
//   ✅ router/index.ts 의 canAccessRoute 완전 대응
// ----------------------------------------------------------------------------
// 연동 백엔드:
//   • POST /api/login                  → 로그인
//   • POST /api/password/change        → 비밀번호 변경
//   • POST /api/users/password/reset   → 관리자 비밀번호 초기화
//   • GET  /api/roles/access           → DeptAccess 목록 조회
//   • PUT  /api/roles/access           → DeptAccess Upsert
//   • GET  /api/roles/access/effective → 실효 접근권한
// ============================================================================

import { httpEx } from '@/services/http-extended'

// ─────────────────────────────────────────────
// 타입 정의
// ─────────────────────────────────────────────

export type User = {
  email: string
  name?: string
  roles: string[]
  dept?: string
}

export type LoginResp = {
  token: string
  user: User
}

export type DeptAccessRecord = {
  route_name: string
  access_scope: string[]
  created_at?: string
}

export type EffectiveDeptAccess = {
  dept?: string
  access: Record<string, string[]>
}

export type RoleAccessRecord = {
  role_code: string
  route_name: string
  access_level: 'none' | 'view' | 'edit' | 'admin'
}

// ─────────────────────────────────────────────
// 인증 관련 (로그인 / 비밀번호)
// ─────────────────────────────────────────────

export async function login(email: string, password: string): Promise<LoginResp> {
  return await httpEx.postJSON<LoginResp>('login', { email, password })
}

export async function changePassword(current_password: string, new_password: string) {
  return await httpEx.postJSON('password/change', { current_password, new_password })
}

export async function resetUserPassword(email: string, new_password?: string) {
  return await httpEx.postJSON('users/password/reset', { email, new_password })
}

// ─────────────────────────────────────────────
// DeptAccess 기반 권한 API
// ─────────────────────────────────────────────

export async function listDeptAccess(): Promise<DeptAccessRecord[]> {
  const res = await httpEx.getJSON<any>('roles/access')
  if (Array.isArray(res)) return res
  if (Array.isArray(res?.items)) return res.items
  return []
}

export async function upsertDeptAccess(route_name: string, access_scope: string[]) {
  return await httpEx.putJSON('roles/access', { route_name, access_scope })
}

/** 실효 DeptAccess (서버 우선 → Fallback 자동) */
export async function getEffectiveDeptAccess(): Promise<EffectiveDeptAccess> {
  try {
    const eff = await httpEx.getJSON<EffectiveDeptAccess>('roles/access/effective', {
      timeoutMs: 8000,
      retry: { retries: 2 },
    })
    return {
      dept: (eff as any)?.dept || 'MOP',
      access: (eff as any)?.access || {},
    }
  } catch {
    const list = await listDeptAccess()
    // fallback 시: 현재 로컬 저장 dept 또는 기본값
    const dept =
      localStorage.getItem('dept_code') ||
      import.meta.env.VITE_DEFAULT_DEPT_CODE ||
      'MOP'
    return computeEffectiveDeptFromList(list, dept)
  }
}

/** DeptAccess 폴백 계산 로직 (null-safe) */
function computeEffectiveDeptFromList(
  list: DeptAccessRecord[],
  userDept?: string
): EffectiveDeptAccess {
  const dept = (userDept || '').toUpperCase()
  const access: Record<string, string[]> = {}
  for (const row of list || []) {
    const scopes = (row.access_scope || []).map((s) => String(s).toUpperCase())
    if (row.route_name) access[row.route_name] = scopes
  }
  return { dept, access }
}

// ─────────────────────────────────────────────
// 권한 판정 유틸리티
// ─────────────────────────────────────────────

/**
 * 특정 routeName 접근 가능 여부
 * @param routeName 라우트 이름 (예: 'closing-calendar')
 * @param eff EffectiveDeptAccess or deptAccess map
 * @param roles SUPERADMIN 등 역할 배열(선택)
 */
export function canAccessRoute(
  routeName: string,
  eff: EffectiveDeptAccess | Record<string, string[]> | null | undefined,
  roles?: string[] | null
): boolean {
  if (!routeName || !eff) return false
  const rn = routeName.trim().toLowerCase()

  // ✅ SUPERADMIN 우선 통과
  if (roles?.map((r) => r.toUpperCase()).includes('SUPERADMIN')) return true

  // authStore.deptAccess (단순 맵)
  if (eff && typeof eff === 'object' && !('access' in eff)) {
    const map = eff as Record<string, string[]>
    const scopes = (map[rn] || map['*'] || []).map((x) => x.toUpperCase())
    return scopes.includes('ALL_EDIT') || scopes.includes('ALL_VIEW')
  }

  // 서버형 구조
  const dept = ((eff as EffectiveDeptAccess).dept || '').toUpperCase()
  const map = (eff as EffectiveDeptAccess).access || {}

  // ① 전역 와일드카드('*')
  const global = (map['*'] || []).map((x) => x.toUpperCase())
  if (global.includes('ALL_EDIT') || global.includes('ALL_VIEW')) return true
  if (dept && global.includes(dept)) return true

  // ② 개별 라우트
  const scopes = (map[rn] || []).map((x) => x.toUpperCase())
  if (scopes.includes('ALL_EDIT') || scopes.includes('ALL_VIEW')) return true
  if (dept && scopes.includes(dept)) return true

  // ③ 기본 거부
  return false
}

/** 수정 가능 여부 */
export function canEditRoute(
  routeName: string,
  eff: EffectiveDeptAccess | Record<string, string[]>
): boolean {
  if (!routeName || !eff) return false

  // authStore.deptAccess 형식
  if (eff && typeof eff === 'object' && !('access' in eff)) {
    const scopes = ((eff as any)[routeName] || []).map((s: string) => s.toUpperCase())
    return scopes.includes('ALL_EDIT')
  }

  // 서버형 구조
  const scopes = ((eff as EffectiveDeptAccess).access?.[routeName] || []).map(
    (s) => s.toUpperCase()
  )
  return scopes.includes('ALL_EDIT')
}

// ─────────────────────────────────────────────
// (레거시) RoleAccess API — 유지용
// ─────────────────────────────────────────────

export async function getEffectiveRoleAccess(): Promise<any> {
  try {
    return await httpEx.getJSON('user-roles/effective')
  } catch {
    return {}
  }
}

// ============================================================================
// End of File — src/services/auth.ts (v3.9 Final · SSOT 완성판)
// ============================================================================
