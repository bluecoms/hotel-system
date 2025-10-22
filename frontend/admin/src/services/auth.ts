// ============================================================================
// File    : src/services/auth.ts
// Version : 2025-10-31 · v3.3 (httpEx Migration · Safe/Retry/Timeout Added)
// Purpose : Hotel Admin — 인증/유저/권한 API 래퍼 (httpEx 기반 강화판)
// ----------------------------------------------------------------------------
// 변경 요약:
//   ✅ http → httpEx 로 전환 (Abort/Timeout/Retry 지원, 완전 호환)
//   ✅ DeptAccess (부서 기반 접근권한) 완전 대응
//   ✅ 레거시 RoleAccess(/user-roles) 폴백 경로 유지
//   ✅ 코드 및 주석 전체 정비 — Phase6 SSOT 완성판
// ----------------------------------------------------------------------------
// 설계 원칙:
//   • 모든 경로는 상대경로로 전달 (httpEx 내부에서 /api prefix 자동 부착)
//   • 인증 헤더(X-Internal-Token)는 http.ts/httpEx가 자동 추가
//   • Abort/Timeout/Retry 정책은 httpEx 기본값으로 제어 가능
//   • Zod safeParse 등 schema 검증도 선택적으로 사용 가능
//   • Phase6 이후: DeptAccess 기반으로 RoleAccess는 점진 폐기 예정
// ============================================================================

import { httpEx } from '@/services/http-extended'

// ─────────────────────────────────────────────
// 타입 정의
// ─────────────────────────────────────────────

/** 사용자 정보 스키마 */
export type User = {
  email: string
  name?: string
  roles: string[]          // SUPERADMIN/ADMIN/HRADMIN/USER 등
  dept?: string            // 부서 코드 (예: FR/HK/AD 등)
}

/** 로그인 응답 */
export type LoginResp = {
  token: string
  user: User
}

/** DeptAccess(부서 기반 권한) 레코드 */
export type DeptAccessRecord = {
  route_name: string
  access_scope: string[]   // 예: ["ALL_VIEW","FR","HK"] / ["ALL_EDIT"] …
  created_at?: string
}

/** 서버 계산 기준 실효 접근권한 */
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
// 인증 (로그인 / 내정보 / 비밀번호 관련 API)
// ─────────────────────────────────────────────

/** 로그인 */
export async function login(email: string, password: string): Promise<LoginResp> {
  return await httpEx.postJSON('login', { email, password })
}

/** 내 정보 조회 */
export async function getMe(): Promise<{ user: User } | User> {
  return await httpEx.getJSON('me')
}

/** 내 비밀번호 변경 */
export async function changePassword(current_password: string, new_password: string) {
  return await httpEx.postJSON('password/change', { current_password, new_password })
}

/** 관리자용 비밀번호 초기화 */
export async function resetUserPassword(email: string, new_password?: string) {
  return await httpEx.postJSON('users/password/reset', { email, new_password })
}

// ─────────────────────────────────────────────
// DeptAccess (부서 기반 접근권한 API)
//   → Phase6 권장 구조 (roles/access)
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

/** 실효 접근권한 조회(서버 계산 우선) */
export async function getEffectiveDeptAccess(): Promise<EffectiveDeptAccess> {
  try {
    // 서버에서 계산된 실효 권한 가져오기
    const eff = await httpEx.getJSON<EffectiveDeptAccess>('roles/access/effective')
    const dept = (eff as any)?.dept
    const access = (eff as any)?.access || {}
    return { dept, access }
  } catch {
    // 서버 제공 안될 시 폴백 계산
    const [me, list] = await Promise.all([getMe(), listDeptAccess()])
    const user: User = (me as any)?.user || (me as any)
    return computeEffectiveDeptFromList(list, user?.dept)
  }
}

/** 라우트 접근 여부 판별 */
export function canAccessRoute(routeName: string, effective: EffectiveDeptAccess): boolean {
  if (!routeName) return false
  const scopes = effective?.access?.[routeName] || []
  const dept = (effective?.dept || '').toUpperCase()
  return scopes.includes('ALL_EDIT') || scopes.includes('ALL_VIEW') || (!!dept && scopes.includes(dept))
}

/** 수정 가능 여부만 별도 판단 */
export function canEditRoute(routeName: string, effective: EffectiveDeptAccess): boolean {
  const scopes = effective?.access?.[routeName] || []
  return scopes.includes('ALL_EDIT')
}

/** DeptAccess 목록 + 부서코드 기반 실효 권한 폴백 계산 */
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
// (레거시) RoleAccess 기반 API (점진 폐기 예정)
//   • 기존 /api/user-roles*, /api/users/roles/access 경로 호환용
//   • Phase7 이후 삭제 예정
// ─────────────────────────────────────────────

/** (레거시) 실효 권한 조회 */
export async function getEffectiveRoleAccess(): Promise<EffectiveMap> {
  try {
    return await httpEx.getJSON('user-roles/effective')
  } catch (e: any) {
    // 서버 404 시 호환 폴백
    if (e?.status === 404) {
      const list = await fetchRoleListCompat()
      return computeEffectiveFrom(list)
    }
    throw e
  }
}

/** (레거시) RoleAccess 목록 조회 */
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

/** (레거시) RoleAccess Upsert (서버 없으면 오류) */
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

/** (레거시) 실효 권한 조회 (외부호환용 단축) */
export async function getEffectiveAccess(): Promise<EffectiveMap> {
  return await getEffectiveRoleAccess()
}

// ─────────────────────────────────────────────
// 내부 유틸 — RoleAccess 호환 변환 및 계산
// ─────────────────────────────────────────────

/** /api/user-roles 응답을 정규화 (배열 또는 {items:[]} 형태 허용) */
async function fetchRoleListCompat(): Promise<any[]> {
  const res: any = await httpEx.getJSON<any>('user-roles')
  if (Array.isArray(res)) return res
  if (Array.isArray(res?.items)) return res.items
  return []
}

/** RoleAccessRecord 스키마 정규화 */
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

/** RoleAccessRecord[] → EffectiveMap 계산 */
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
