// ============================================================================
// File    : src/services/auth.ts
// Version : 2025-10-31 · v3.5 (SSOT Phase 3.5 Stable · me Removed)
// Purpose : Hotel Admin — 인증/유저/권한 API 래퍼 (httpEx 기반 완성판)
// ----------------------------------------------------------------------------
// 목적:
//   • 프런트엔드에서 사용하는 모든 인증/권한 관련 API 호출을 httpEx로 일원화.
//   • /api/me 라우터 완전 폐지 이후에도 동일한 구조로 동작하도록 설계.
//   • DeptAccess 기반 접근제어(roles/access) 구조를 기준으로 실효 권한 계산.
//   • RoleAccess 기반(레거시) API는 완전 호환 유지하되 Phase 7에서 폐기 예정.
// ----------------------------------------------------------------------------
// 특징:
//   ✅ httpEx 통합 → fetch 기반, Abort/Timeout/Retry 자동 처리
//   ✅ X-Internal-Token 헤더 자동 첨부
//   ✅ /api/me 제거 → 폴백 dept='MOP' 적용
//   ✅ DeptAccess/RoleAccess 구조 완전 SSOT 정합
//   ✅ Pydantic v2 및 FastAPI SSOT 스키마와 동기화
// ----------------------------------------------------------------------------
// 사용 예시:
//   import { login, getEffectiveDeptAccess, canAccessRoute } from '@/services/auth'
//   const { token, user } = await login('admin', '1234')
//   const eff = await getEffectiveDeptAccess()
//   if (canAccessRoute('contracts', eff)) { ... }
// ============================================================================

import { httpEx } from '@/services/http-extended'

// ─────────────────────────────────────────────
// 타입 정의
// ─────────────────────────────────────────────

/** 사용자 기본 정보 스키마 (백엔드 UserOut과 일치) */
export type User = {
  email: string
  name?: string
  roles: string[]          // SUPERADMIN / ADMIN / HRADMIN / USER 등
  dept?: string            // 부서 코드 (예: FR/HK/AD 등)
}

/** 로그인 응답 */
export type LoginResp = {
  token: string
  user: User
}

/** DeptAccess(부서 기반 접근권한) 레코드 */
export type DeptAccessRecord = {
  route_name: string
  access_scope: string[]   // 예: ["ALL_VIEW","FR","HK"] / ["ALL_EDIT"] 등
  created_at?: string
}

/** 서버 계산 기준 실효 접근권한 (DeptAccess 기반) */
export type EffectiveDeptAccess = {
  dept?: string
  access: Record<string, string[]>
}

/** (레거시) RoleAccess 레코드 — 점진 폐기 예정 */
export type RoleAccessRecord = {
  role_code: string
  route_name: string
  access_level: 'none' | 'view' | 'edit' | 'admin' | 'view-only'
}

/** (레거시) 실효 권한맵 — RoleAccess 기반 */
export type EffectiveMap = Record<
  string,
  Record<'none' | 'view' | 'edit' | 'admin', string>
>

// ─────────────────────────────────────────────
// 인증 관련 API (로그인 / 비밀번호)
// ─────────────────────────────────────────────

/**
 * 로그인
 * @param email 사용자 이메일
 * @param password 비밀번호
 * @returns LoginResp { token, user }
 */
export async function login(email: string, password: string): Promise<LoginResp> {
  return await httpEx.postJSON('login', { email, password })
}

/**
 * 비밀번호 변경
 * @param current_password 현재 비밀번호
 * @param new_password 새 비밀번호
 */
export async function changePassword(current_password: string, new_password: string) {
  return await httpEx.postJSON('password/change', { current_password, new_password })
}

/**
 * 관리자 비밀번호 초기화
 * @param email 사용자 이메일
 * @param new_password 새 비밀번호 (옵션)
 */
export async function resetUserPassword(email: string, new_password?: string) {
  return await httpEx.postJSON('users/password/reset', { email, new_password })
}

// ─────────────────────────────────────────────
// DeptAccess (부서 기반 권한 API) — Phase 6 표준
// ─────────────────────────────────────────────

/**
 * DeptAccess 목록 조회
 * @returns DeptAccessRecord[]
 */
export async function listDeptAccess(): Promise<DeptAccessRecord[]> {
  const res = await httpEx.getJSON<any>('roles/access')
  if (Array.isArray(res)) return res
  if (Array.isArray(res?.items)) return res.items
  return []
}

/**
 * DeptAccess Upsert
 * @param route_name 라우트 이름
 * @param access_scope 접근 범위 배열
 */
export async function upsertDeptAccess(route_name: string, access_scope: string[]) {
  return await httpEx.putJSON('roles/access', { route_name, access_scope })
}

/**
 * 실효 접근권한 조회 (서버 우선 → 폴백 dept='MOP')
 * @description
 *   1. 서버에서 계산된 roles/access/effective 우선 사용.
 *   2. 실패 시 DeptAccess 목록 기반으로 폴백 계산.
 *   3. /api/me 제거 이후에는 기본 지점코드('MOP')로 dept 대체.
 */
export async function getEffectiveDeptAccess(): Promise<EffectiveDeptAccess> {
  try {
    // ① 서버 계산 결과 사용
    const eff = await httpEx.getJSON<EffectiveDeptAccess>('roles/access/effective')
    const dept = (eff as any)?.dept
    const access = (eff as any)?.access || {}
    return { dept, access }
  } catch {
    // ② 폴백 계산: /api/me 삭제로 기본 지점 MOP 사용
    const list = await listDeptAccess()
    const dept = 'MOP'
    return computeEffectiveDeptFromList(list, dept)
  }
}

/**
 * 특정 라우트 접근 가능 여부 판별
 * @param routeName 라우트 이름
 * @param effective EffectiveDeptAccess
 */
export function canAccessRoute(routeName: string, effective: EffectiveDeptAccess): boolean {
  if (!routeName) return false
  const scopes = effective?.access?.[routeName] || []
  const dept = (effective?.dept || '').toUpperCase()
  return (
    scopes.includes('ALL_EDIT') ||
    scopes.includes('ALL_VIEW') ||
    (!!dept && scopes.includes(dept))
  )
}

/**
 * 수정 가능 여부만 판별
 * @param routeName 라우트 이름
 * @param effective EffectiveDeptAccess
 */
export function canEditRoute(routeName: string, effective: EffectiveDeptAccess): boolean {
  const scopes = effective?.access?.[routeName] || []
  return scopes.includes('ALL_EDIT')
}

/**
 * DeptAccess 목록 + 부서코드 기반 폴백 계산
 * @param list DeptAccessRecord[]
 * @param userDept 사용자 부서 코드 (옵션)
 * @returns EffectiveDeptAccess
 */
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
// (레거시) RoleAccess 기반 API — Phase 7 삭제 예정
// ─────────────────────────────────────────────

/**
 * (레거시) 실효 권한 조회
 * @returns EffectiveMap
 */
export async function getEffectiveRoleAccess(): Promise<EffectiveMap> {
  try {
    return await httpEx.getJSON('user-roles/effective')
  } catch (e: any) {
    if (e?.status === 404) {
      const list = await fetchRoleListCompat()
      return computeEffectiveFrom(list)
    }
    throw e
  }
}

/**
 * (레거시) RoleAccess 목록 조회
 * @returns RoleAccessRecord[]
 */
export async function listRoleAccess(): Promise<RoleAccessRecord[]> {
  try {
    return await httpEx.getJSON('users/roles/access')
  } catch (e: any) {
    if (e?.status === 404) {
      const list = await fetchRoleListCompat()
      return normalizeToRoleAccess(list)
    }
    throw e
  }
}

/**
 * (레거시) RoleAccess Upsert
 * @param data RoleAccessRecord
 */
export async function upsertRoleAccess(data: RoleAccessRecord) {
  try {
    return await httpEx.putJSON('users/roles/access', data)
  } catch (e: any) {
    if (e?.status === 404) {
      throw new Error('권한 저장 엔드포인트가 없습니다. (PUT /api/users/roles/access 미제공)')
    }
    throw e
  }
}

/**
 * (레거시) 실효 권한 조회 (단축 별칭)
 * @returns EffectiveMap
 */
export async function getEffectiveAccess(): Promise<EffectiveMap> {
  return await getEffectiveRoleAccess()
}

// ─────────────────────────────────────────────
// 내부 유틸 — RoleAccess 호환 변환 및 계산
// ─────────────────────────────────────────────

/**
 * /api/user-roles 응답을 정규화 (배열 또는 {items:[]} 형태 허용)
 * @returns any[]
 */
async function fetchRoleListCompat(): Promise<any[]> {
  const res: any = await httpEx.getJSON<any>('user-roles')
  if (Array.isArray(res)) return res
  if (Array.isArray(res?.items)) return res.items
  return []
}

/**
 * RoleAccessRecord 스키마 정규화
 * @param rows any[]
 * @returns RoleAccessRecord[]
 */
function normalizeToRoleAccess(rows: any[]): RoleAccessRecord[] {
  return rows
    .map((r) => {
      const role_code = (r.role_code ?? r.role ?? '').toString()
      const route_name = (r.route_name ?? r.route ?? r.path ?? '').toString()
      const raw = (r.access_level ?? r.level ?? 'none').toString().toLowerCase()
      const level = raw === 'view-only' ? 'view' : raw
      return { role_code, route_name, access_level: (level as any) || 'none' }
    })
    .filter((x) => x.role_code && x.route_name)
}

/**
 * RoleAccessRecord[] → EffectiveMap 계산
 * @param rows RoleAccessRecord[]
 * @returns EffectiveMap
 */
function computeEffectiveFrom(rows: RoleAccessRecord[]): EffectiveMap {
  const LEVEL_ORDER: Record<string, number> = {
    none: 0,
    view: 1,
    edit: 2,
    admin: 3,
    'view-only': 1,
  }
  const eff: EffectiveMap = {}
  for (const r of rows) {
    const role = String(r.role_code || '').toUpperCase()
    const route = String(r.route_name || '')
    if (!role || !route) continue
    const lvRaw = (r.access_level || 'none').toString().toLowerCase()
    const lv = (lvRaw === 'view-only' ? 'view' : lvRaw) as 'none' | 'view' | 'edit' | 'admin'
    if (!eff[role]) eff[role] = {} as Record<'none' | 'view' | 'edit' | 'admin', string>
    const current = eff[role][route]
    if (!current || LEVEL_ORDER[lv] > LEVEL_ORDER[current]) eff[role][route] = lv
  }
  return eff
}

// ============================================================================
// End of File — src/services/auth.ts
// ============================================================================
