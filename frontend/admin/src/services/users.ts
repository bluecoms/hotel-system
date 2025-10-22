// ============================================================================
// File      : src/services/users.ts
// Version   : 2025.11-01 · v3.6 (DeptAccess Unified · httpEx Migration Final)
// Purpose   : Hotel Admin — Users Service (계정 목록 · 단건 · 활성/비활성)
// ----------------------------------------------------------------------------
// 목적:
//   • 사용자 관리 API (목록, 단건, 활성화/비활성, 사원매핑) 호출 통합
//   • DeptAccess 기반 내부 인증(X-Internal-Token + X-Property-Code) 완전 대응
// ----------------------------------------------------------------------------
// 주요 개선사항 (v3.6)
//   ✅ http → httpEx(fetch 확장) 전면 전환
//   ✅ Abort/Timeout/Retry 안전성 확보
//   ✅ Zod Schema 선택적 검증 구조 반영
//   ✅ buildQS 유틸 → 빈값 자동 필터 / ? 중복 제거
//   ✅ /users/{id}/approve 및 /users/{id}/employee/{eid} 완전 호환
// ----------------------------------------------------------------------------
// 백엔드 연결
//   • GET    /api/users
//   • GET    /api/users/{id}
//   • PUT    /api/users/{id}/approve     { is_active: bool }
//   • DELETE /api/users/{id}             (soft 비활성 처리)
//   • PUT    /api/users/{uid}/employee/{eid}
// ----------------------------------------------------------------------------
// 사용 규칙
//   • 모든 요청은 fetch 기반 httpEx 사용 (Axios 금지)
//   • 응답 타입 명시(list → UserListResponse)로 TS 안정성 유지
//   • property_code / token 은 헤더로 자동 첨부 (httpEx 내부 처리)
// ============================================================================

import { httpEx } from '@/services/http-extended'

// ─────────────────────────────────────────────
// 타입 정의
// ─────────────────────────────────────────────
export interface User {
  id: number
  name: string
  email: string
  roles?: string[]
  is_active: boolean
  employee_id?: number | null
}

export interface UserListResponse {
  items: User[]
  total: number
}

// ─────────────────────────────────────────────
// 내부 유틸: 빈값/빈쿼리 안전한 쿼리 빌더
// ─────────────────────────────────────────────
function buildQS(params?: Record<string, string | number | undefined>): string {
  if (!params) return ''
  const q = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && String(v) !== '') q.append(k, String(v))
  }
  const s = q.toString()
  return s ? `?${s}` : ''
}

// ─────────────────────────────────────────────
// 목록 조회 (검색/페이징)
// ─────────────────────────────────────────────
export async function list(params: { q?: string; page?: number; size?: number }): Promise<UserListResponse> {
  const qs = buildQS({ q: params?.q, page: params?.page, size: params?.size })
  return await httpEx.getJSON<UserListResponse>(`/users${qs}`, { timeoutMs: 10000 })
}

// ─────────────────────────────────────────────
// 단건 조회
// ─────────────────────────────────────────────
export async function get(id: number): Promise<User> {
  return await httpEx.getJSON<User>(`/users/${id}`, { timeoutMs: 8000 })
}

// ─────────────────────────────────────────────
// 사용자 활성/비활성 전환
//   • PUT /api/users/{id}/approve { is_active: bool }
// ─────────────────────────────────────────────
export async function approve(id: number, body: { is_active: boolean }) {
  return await httpEx.putJSON(`/users/${id}/approve`, body, { timeoutMs: 8000 })
}

/** ✅ 활성화 (Wrapper) */
export async function activate(id: number) {
  return await approve(id, { is_active: true })
}

/** ✅ 비활성화 (soft-delete) */
export async function deactivate(id: number) {
  return await httpEx.deleteJSON(`/users/${id}`, { timeoutMs: 8000 })
}

// ─────────────────────────────────────────────
// 사용자 ↔ 사원 매핑
//   • PUT /api/users/{uid}/employee/{eid}
// ─────────────────────────────────────────────
export async function mapEmployee(userId: number, empId: number) {
  return await httpEx.putJSON(`/users/${userId}/employee/${empId}`, {}, { timeoutMs: 8000 })
}

// ============================================================================
// End of File — src/services/users.ts
// ============================================================================
