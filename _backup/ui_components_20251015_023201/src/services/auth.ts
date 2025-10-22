// src/services/auth.ts
import http from '@/services/http'

export type User = { email: string; name: string; roles: string[] }
export type LoginResp = { token: string; user: User }

export async function login(email: string, password: string): Promise<LoginResp> {
  return await http.post('/login', { email, password })
}

export async function getMe(): Promise<{ user: User } | User> {
  return await http.get('/me')
}

export async function changePassword(current_password: string, new_password: string) {
  return await http.post('/password/change', { current_password, new_password })
}

export async function resetUserPassword(email: string, new_password?: string) {
  return await http.post('/users/password/reset', { email, new_password })
}

// ──────────────────────────────────────────────────────────────
// Role Access (권한 관리)
// ──────────────────────────────────────────────────────────────

export type RoleAccessRecord = {
  role_code: string
  route_name: string
  access_level: 'view' | 'edit' | 'admin'
}

// 내 유효 권한 조회 (백엔드 /api/users/roles/access/effective)
export async function getEffectiveRoleAccess(): Promise<Record<string, string>> {
  return await http.get('/users/roles/access/effective')
}

// 역할별 접근권한 목록 (관리자용)
export async function listRoleAccess(): Promise<RoleAccessRecord[]> {
  return await http.get('/users/roles/access')
}

// 권한 업서트(생성/수정)
export async function upsertRoleAccess(data: RoleAccessRecord) {
  return await http.put('/users/roles/access', data)
}
// ─────────────────────────────────────────────
// 권한 effective 맵을 서버/클라 폴백으로 얻기
// ─────────────────────────────────────────────
export type AccessRec = { role_code: string; route_name: string; access_level: 'none'|'view'|'edit'|'admin' }
export type EffectiveMap = Record<string, Record<string, 'none'|'view'|'edit'|'admin'>>

export async function getEffectiveAccess(): Promise<EffectiveMap> {
  try {
    // 1) 서버에 /effective 있으면 그대로 사용
    return await http.get('/users/roles/access/effective')
  } catch (e: any) {
    // 2) 404면 목록으로 받아서 클라에서 변환
    if (e?.status === 404) {
      const list: any = await http.get('/users/roles/access')
      const rows: AccessRec[] = Array.isArray(list) ? list : (list.items ?? [])
      const LEVEL_ORDER: Record<string, number> = { none:0, view:1, edit:2, admin:3 }
      const eff: EffectiveMap = {}

      for (const r of rows) {
        const role = String(r.role_code).toUpperCase()
        const route = String(r.route_name)
        const lv = r.access_level as 'none'|'view'|'edit'|'admin'
        if (!eff[role]) eff[role] = {}
        const cur = eff[role][route]
        if (!cur || LEVEL_ORDER[lv] > LEVEL_ORDER[cur]) {
          eff[role][route] = lv
        }
      }
      // 규칙: SUPERADMIN은 와일드카드가 있으면 전체 admin으로 취급 (선택)
      if (eff.SUPERADMIN?.['*'] === 'admin') {
        // 필요 시 서버에 실제 라우트 목록을 넣고 펼칠 수도 있지만,
        // 클라이언트 검증 시에는 hasAccess에서 SUPERADMIN을 무조건 패스 처리하므로 생략해도 OK.
      }
      return eff
    }
    throw e
  }
}
