// ============================================================================
//  File    : src/services/users.ts
//  Version : 2025.10 Final Stable
//  Purpose : Hotel Admin — Users Service (계정 목록 · 단건 · 활성/비활성)
//  ---------------------------------------------------------------------------
//  연결 백엔드:
//    • GET    /api/users               → 목록 조회
//    • GET    /api/users/{id}          → 단건 조회
//    • PUT    /api/users/{id}/approve  → 활성/비활성 전환(Body: { is_active })
//    • DELETE /api/users/{id}          → 비활성/삭제(서버 정책)
//  주요 개선사항:
//    ✅ approve() 추가(뷰에서 toggleActive에 정합)
//    ✅ 빈 쿼리 안전한 buildQS 유틸 도입
//    ✅ http.ts(baseURL='/api') 전제 하에 경로 중복 제거
//  규칙:
//    • 네트워킹은 fetch 기반 '@/services/http' 모듈 단일 사용 (Axios 금지)
//    • URLSearchParams로 쿼리 구성(빈 값 제외, 불필요한 '?' 금지)
//    • 반환 타입 명시(list → UserListResponse)로 TS 안정성 확보
// ============================================================================

import http from '@/services/http'

// ── 타입 정의 ────────────────────────────────────────────────────────────────
export interface User {
  id: number
  name: string
  email: string
  roles?: string[]
  is_active: boolean
}

export interface UserListResponse {
  items: User[]
  total: number
}

// ── 내부 유틸: 빈값/빈쿼리 안전한 쿼리 빌더 ───────────────────────────────────
function buildQS(params?: Record<string, string | number | undefined>): string {
  if (!params) return ''
  const q = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && String(v) !== '') q.append(k, String(v))
  }
  const s = q.toString()
  return s ? `?${s}` : ''
}

// ── 목록 조회 ────────────────────────────────────────────────────────────────
export async function list(params: { q?: string; page?: number; size?: number }): Promise<UserListResponse> {
  return await http.get<UserListResponse>(`/users${buildQS({
    q: params?.q,
    page: params?.page,
    size: params?.size,
  })}`)
}

// ── 단건 조회 ────────────────────────────────────────────────────────────────
export async function get(id: number): Promise<User> {
  return await http.get<User>(`/users/${id}`)
}

// ── 활성/비활성 전환 ────────────────────────────────────────────────────────
// 백엔드 규약: approve → 활성/비활성 전환(서버가 최종 판단)
export async function approve(id: number, body: { is_active: boolean }) {
  return await http.put(`/users/${id}/approve`, body)
}

// 편의 래퍼(호환): 활성화 / 비활성(서버 정책에 따라 delete는 soft 처리)
export async function activate(id: number) {
  return await approve(id, { is_active: true })
}

export async function deactivate(id: number) {
  return await http.delete(`/users/${id}`)
}

// ── 사용자-사원 매핑 ────────────────────────────────────────────────────────
// 백엔드: PUT /api/users/{uid}/employee/{eid}
export async function mapEmployee(userId: number, empId: number) {
  return await http.put(`/users/${userId}/employee/${empId}`)
}
