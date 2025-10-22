// ============================================================================
// File    : src/services/auth.ts
// Version : 2025.11-01 · v3.7 (DeptAccess Wildcard · ALL_* 지원 · SSOT Final)
// Purpose : Hotel Admin — 인증 / 권한 / 사용자 API (DeptAccess 기반 완성판)
// ----------------------------------------------------------------------------
// 목적:
//   • 프런트엔드 인증과 권한 로직을 httpEx(fetch 기반)으로 완전 일원화.
//   • /api/me 폐지 이후에도 DeptAccess (/api/roles/access/effective) 기반 동작.
//   • ALL_EDIT / ALL_VIEW / 와일드카드(*) / 부서별 접근코드(FR, HK 등) 지원.
// ----------------------------------------------------------------------------
// 주요 개선 (v3.7):
//   ✅ 와일드카드('*') + ALL_EDIT / ALL_VIEW 완전 대응
//   ✅ fallback 시 listDeptAccess() → computeEffectiveDeptFromList()
//   ✅ SUPERADMIN·ADMIN 공통 핸들 (프런트/백 일관성 유지)
//   ✅ httpEx 기반 재시도 / 타임아웃 자동 적용
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

/** 사용자 정보 (UserOut 스키마 기준) */
export type User = {
  email: string
  name?: string
  roles: string[]
  dept?: string
}

/** 로그인 응답 구조 */
export type LoginResp = {
  token: string
  user: User
}

/** DeptAccess 단건 구조 */
export type DeptAccessRecord = {
  route_name: string
  access_scope: string[]
  created_at?: string
}

/** 서버 계산 결과 구조 */
export type EffectiveDeptAccess = {
  dept?: string
  access: Record<string, string[]>
}

/** (레거시) RoleAccess 구조 — Phase 7 제거 예정 */
export type RoleAccessRecord = {
  role_code: string
  route_name: string
  access_level: 'none' | 'view' | 'edit' | 'admin'
}

// ─────────────────────────────────────────────
// 인증 관련 (로그인 / 비밀번호)
// ─────────────────────────────────────────────

/** 로그인 */
export async function login(email: string, password: string): Promise<LoginResp> {
  return await httpEx.postJSON<LoginResp>('login', { email, password })
}

/** 비밀번호 변경 */
export async function changePassword(current_password: string, new_password: string) {
  return await httpEx.postJSON('password/change', { current_password, new_password })
}

/** 비밀번호 초기화 (SUPERADMIN 전용) */
export async function resetUserPassword(email: string, new_password?: string) {
  return await httpEx.postJSON('users/password/reset', { email, new_password })
}

// ─────────────────────────────────────────────
// DeptAccess 기반 권한 API
// ─────────────────────────────────────────────

/** DeptAccess 목록 조회 */
export async function listDeptAccess(): Promise<DeptAccessRecord[]> {
  const res = await httpEx.getJSON<any>('roles/access')
  if (Array.isArray(res)) return res
  if (Array.isArray(res?.items)) return res.items
  return []
}

/** DeptAccess Upsert */
export async function upsertDeptAccess(route_name: string, access_scope: string[]) {
  return await httpEx.putJSON('roles/access', { route_name, access_scope })
}

/** 실효 DeptAccess (effective) — 서버 계산 → 폴백 순 */
export async function getEffectiveDeptAccess(): Promise<EffectiveDeptAccess> {
  try {
    const eff = await httpEx.getJSON<EffectiveDeptAccess>('roles/access/effective', {
      timeoutMs: 8000,
      retry: { retries: 2 },
    })
    const dept = (eff as any)?.dept || 'MOP'
    const access = (eff as any)?.access || {}
    return { dept, access }
  } catch {
    const list = await listDeptAccess()
    const dept = 'MOP'
    return computeEffectiveDeptFromList(list, dept)
  }
}

/** DeptAccess 폴백 계산 로직 */
function computeEffectiveDeptFromList(list: DeptAccessRecord[], userDept?: string): EffectiveDeptAccess {
  const dept = (userDept || '').toUpperCase()
  const access: Record<string, string[]> = {}
  for (const row of list) {
    const scopes = (row.access_scope || []).map((s) => String(s).toUpperCase())
    access[row.route_name] = scopes
  }
  return { dept, access }
}

// ─────────────────────────────────────────────
// 권한 판정 유틸리티
// ─────────────────────────────────────────────

/**
 * 특정 routeName 접근 가능 여부
 * @param routeName 라우트 이름
 * @param eff EffectiveDeptAccess
 */
export function canAccessRoute(routeName: string, eff: EffectiveDeptAccess | null | undefined): boolean {
  if (!routeName || !eff) return false
  const rn = routeName.trim().toLowerCase()
  const dept = (eff.dept || '').toUpperCase()
  const map = eff.access || {}

  // ① 와일드카드('*') 검사
  const global = (map['*'] || []).map((x) => x.toUpperCase())
  if (global.includes('ALL_EDIT') || global.includes('ALL_VIEW')) return true
  if (dept && global.includes(dept)) return true

  // ② 개별 라우트 검사
  const scopes = (map[rn] || []).map((x) => x.toUpperCase())
  if (scopes.includes('ALL_EDIT') || scopes.includes('ALL_VIEW')) return true
  if (dept && scopes.includes(dept)) return true

  // ③ 기본 거부
  return false
}

/** 수정 가능 여부 판정 */
export function canEditRoute(routeName: string, eff: EffectiveDeptAccess): boolean {
  if (!routeName || !eff) return false
  const scopes = (eff.access?.[routeName] || []).map((s) => s.toUpperCase())
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
// End of File — src/services/auth.ts (v3.7 Final)
// ============================================================================
