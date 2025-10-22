// ============================================================================
// File    : src/services/auth.ts
// Version : 2025-10-22 · v3.1 (DeptAccess Migration · SSOT)
// Purpose : Hotel Admin — 인증/유저/권한 API 래퍼 (http.ts 기반)
// ----------------------------------------------------------------------------
// 목적:
//   • 로그인/내정보/비밀번호 변경 등 인증 관련 API 래퍼
//   • ✅ DeptAccess(부서 기반 접근권한) 관리/조회 지원
//   • 레거시 RoleAccess 하드코딩 제거, 서버 DB 기반 동적 권한으로 전환
// ----------------------------------------------------------------------------
// 설계 원칙:
//   • 모든 경로는 상대경로로 전달 (http.ts가 /api prefix 자동 부착)
//   • 인증 헤더(X-Internal-Token)는 http.ts가 자동 처리
//   • 권한 판단은 서버 응답(DeptAccess effective)을 우선 사용
// ----------------------------------------------------------------------------
// 백엔드 계약(최신):
//   • POST  /api/login
//   • GET   /api/me
//   • POST  /api/password/change
//   • POST  /api/users/password/reset
//   • GET   /api/roles/access                → DeptAccess 목록 (route_name, access_scope[])
//   • PUT   /api/roles/access                → DeptAccess upsert
//   • GET   /api/roles/access/effective      → 로그인 사용자 기준 실효 접근권한
// ----------------------------------------------------------------------------
// 호환(레거시) — 필요 시 폴백만 제공(내부 미사용):
//   • GET /api/user-roles, GET /api/user-roles/effective
//   • GET/PUT /api/users/roles/access (미제공이면 에러 반환)
// ============================================================================

import http from '@/services/http'

// ─────────────────────────────────────────────
// 타입 정의
// ─────────────────────────────────────────────

export type User = {
  email: string
  name?: string
  roles: string[]      // SUPERADMIN/ADMIN/HRADMIN/USER 등
  dept?: string        // 사용자의 소속 부서코드(예: FR/HK/AD…) — 서버가 제공하면 사용
}

export type LoginResp = {
  token: string
  user: User
}

/** DeptAccess 레코드 (신규: 역할 무관, 부서 기반) */
export type DeptAccessRecord = {
  route_name: string
  access_scope: string[] // 예: ["ALL_VIEW","FR","HK"] / ["ALL_EDIT"] …
  created_at?: string
}

/** 실효 접근권한 (서버 기준) */
export type EffectiveDeptAccess = {
  dept?: string
  access: Record<string, string[]> // route_name → 허용 scope 리스트
}

/** (레거시) RoleAccess 호환 타입 — 내부 계산/변환용 래퍼 */
export type RoleAccessRecord = {
  role_code: string
  route_name: string
  access_level: 'none' | 'view' | 'edit' | 'admin' | 'view-only'
}

/** (레거시) 효과 권한 맵 — 더 이상 사용 권장 안 함 */
export type EffectiveMap = Record<
  string,
  Record<'none' | 'view' | 'edit' | 'admin', string>
>

// ─────────────────────────────────────────────
// 인증 (로그인 / 내 정보 / 비밀번호)
// ─────────────────────────────────────────────

/** 로그인 */
export async function login(email: string, password: string): Promise<LoginResp> {
  return await http.post('login', { email, password })
}

/** 내 정보 조회 */
export async function getMe(): Promise<{ user: User } | User> {
  return await http.get('me')
}

/** 내 비밀번호 변경 */
export async function changePassword(current_password: string, new_password: string) {
  return await http.post('password/change', { current_password, new_password })
}

/** 특정 사용자 비밀번호 초기화 (관리자용) */
export async function resetUserPassword(email: string, new_password?: string) {
  return await http.post('users/password/reset', { email, new_password })
}

// ─────────────────────────────────────────────
// DeptAccess (부서 기반 접근권한) — 최신 권장 API
// ─────────────────────────────────────────────

/** DeptAccess 목록 조회 (route_name별 access_scope[]) */
export async function listDeptAccess(): Promise<DeptAccessRecord[]> {
  const res = await http.get<any>('roles/access')
  if (Array.isArray(res)) return res
  if (Array.isArray(res?.items)) return res.items
  return []
}

/** DeptAccess Upsert */
export async function upsertDeptAccess(route_name: string, access_scope: string[]) {
  return await http.put('roles/access', { route_name, access_scope })
}

/** 실효 접근권한 조회(서버 계산) — 우선 사용 */
export async function getEffectiveDeptAccess(): Promise<EffectiveDeptAccess> {
  // 서버가 계산한 실효 접근권한 우선
  try {
    const eff = await http.get<EffectiveDeptAccess>('roles/access/effective')
    // shape 보정(안전)
    const dept = (eff as any)?.dept
    const access = (eff as any)?.access || {}
    return { dept, access }
  } catch (e: any) {
    // 404 등일 때는 목록+내부 계산 폴백
    const [me, list] = await Promise.all([getMe(), listDeptAccess()])
    const user: User = (me as any)?.user || (me as any)
    return computeEffectiveDeptFromList(list, user?.dept)
  }
}

/** 프런트에서 간단히 사용할 수 있는 접근 헬퍼 */
export function canAccessRoute(routeName: string, effective: EffectiveDeptAccess): boolean {
  if (!routeName) return false
  const scopes = effective?.access?.[routeName] || []
  const dept = (effective?.dept || '').toUpperCase()
  // ALL_EDIT(모두 수정/권한) 또는 ALL_VIEW(모두 보기) 또는 본인 부서 포함 시 true
  return scopes.includes('ALL_EDIT') || scopes.includes('ALL_VIEW') || (!!dept && scopes.includes(dept))
}

/** (옵션) 수정 권한 여부만 별도로 체크하고 싶을 때 */
export function canEditRoute(routeName: string, effective: EffectiveDeptAccess): boolean {
  if (!routeName) return false
  const scopes = effective?.access?.[routeName] || []
  // 수정 권한은 ALL_EDIT(전역 수정)만 허용 — 부서 지정을 수정 권한까지로 확대하려면 규칙 확장
  return scopes.includes('ALL_EDIT')
}

// ─────────────────────────────────────────────
// 내부 유틸 — DeptAccess 폴백 계산 (서버 effective 미제공 시)
// ─────────────────────────────────────────────

/** DeptAccess 목록 + 사용자 부서 코드로 실효 접근 계산 */
function computeEffectiveDeptFromList(list: DeptAccessRecord[], userDept?: string): EffectiveDeptAccess {
  const dept = (userDept || '').toUpperCase()
  const access: Record<string, string[]> = {}
  for (const row of list) {
    const scopes = (row.access_scope || []).map(s => String(s).toUpperCase())
    // 사용자가 볼 수 있을 때만 포함시켜도 되고, 전체 매핑을 유지해도 됨 — 여기선 전체 유지
    access[row.route_name] = scopes
  }
  return { dept, access }
}

// ─────────────────────────────────────────────
// (레거시 호환) RoleAccess — 더 이상 사용하지 않음
//  * 외부 코드가 호출 중이면 에러/폴백 안내 용도로만 유지
// ─────────────────────────────────────────────

/**
 * 효과 권한 조회 (레거시 RoleAccess 폴백)
 * - 권장: getEffectiveDeptAccess() 사용
 */
export async function getEffectiveRoleAccess(): Promise<EffectiveMap> {
  try {
    return await http.get('user-roles/effective')
  } catch (e: any) {
    // 레거시 폴백: /user-roles → RoleAccessRecord[] 정규화
    if (e?.status === 404) {
      const list = await fetchRoleListCompat()
      return computeEffectiveFrom(list)
    }
    throw e
  }
}

/** (레거시) 권한 목록 조회 — 서버에 없으면 user-roles로 대체 */
export async function listRoleAccess(): Promise<RoleAccessRecord[]> {
  try {
    return await http.get('users/roles/access')
  } catch (e: any) {
    if (e?.status === 404) {
      const list = await fetchRoleListCompat()
      return normalizeToRoleAccess(list)
    }
    throw e
  }
}

/** (레거시) 권한 레코드 Upsert — 서버 미제공 시 에러 */
export async function upsertRoleAccess(data: RoleAccessRecord) {
  try {
    return await http.put('users/roles/access', data)
  } catch (e: any) {
    if (e?.status === 404) {
      throw new Error('권한 저장 엔드포인트가 서버에 없습니다. (PUT /api/users/roles/access 미제공)')
    }
    throw e
  }
}

/** (레거시) 효과 권한 조회 — 외부 호환용 */
export async function getEffectiveAccess(): Promise<EffectiveMap> {
  return await getEffectiveRoleAccess()
}

// ─────────────────────────────────────────────
// 내부 유틸 — /user-roles 호환 처리 & RoleAccess 계산 (레거시)
// ─────────────────────────────────────────────

/** /api/user-roles 응답을 통일 스키마로 변환 (배열 또는 { items: [] } 허용) */
async function fetchRoleListCompat(): Promise<any[]> {
  const res: any = await http.get<any>('user-roles')
  if (Array.isArray(res)) return res
  if (Array.isArray(res?.items)) return res.items
  return []
}

/** 다양한 서버 스키마를 RoleAccessRecord[]로 정규화 (레거시) */
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

/** RoleAccessRecord[] → EffectiveMap 계산 (레거시) */
function computeEffectiveFrom(rows: RoleAccessRecord[]): EffectiveMap {
  const LEVEL_ORDER: Record<string, number> = { none: 0, view: 1, edit: 2, admin: 3, 'view-only': 1 }
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
