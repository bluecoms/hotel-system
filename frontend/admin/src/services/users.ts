// ============================================================================
// File      : src/services/users.ts
// Version   : 2025.11-05 · v3.7 Final (SSOT Stable · DeptAccess Safe)
// Purpose   : Hotel Admin — Users Service (계정 목록 · 단건 · 활성/비활성/사원매핑)
// ----------------------------------------------------------------------------
// 목적:
//   • 사용자 관리 API (목록 · 단건 · 활성화/비활성 · 사원매핑) 통합.
//   • DeptAccess + X-Internal-Token 헤더 자동 호환.
// ----------------------------------------------------------------------------
// 주요 개선 (v3.7):
//   ✅ try/catch 안전화 · 빈 배열/기본값 폴백
//   ✅ 반환형 명시 → TS 추론 정확성 향상
//   ✅ httpEx(fetch 확장) 기반으로 Timeout/Retry 보장
//   ✅ SSOT 주석 포맷(auth/master와 통일)
// ============================================================================

import { httpEx } from '@/services/http-extended'

// ----------------------------------------------------------------------------
//  타입 정의
// ----------------------------------------------------------------------------
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

// ----------------------------------------------------------------------------
//  내부 유틸 — 빈값 필터 쿼리 빌더
// ----------------------------------------------------------------------------
function buildQS(params?: Record<string, string | number | undefined>): string {
  if (!params) return ''
  const q = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && String(v).trim() !== '') q.append(k, String(v))
  }
  const s = q.toString()
  return s ? `?${s}` : ''
}

// ============================================================================
// 1️⃣ 사용자 목록 조회 (검색 / 페이징)
// ============================================================================
export async function list(params?: { q?: string; page?: number; size?: number }): Promise<UserListResponse> {
  try {
    const qs = buildQS(params)
    const res = await httpEx.getJSON<UserListResponse>(`users${qs}`, { timeoutMs: 10000 })
    if (res && Array.isArray(res.items)) return res
    return { items: [], total: 0 }
  } catch (err) {
    console.error('[Users.list] failed:', err)
    return { items: [], total: 0 }
  }
}

// ============================================================================
// 2️⃣ 단건 조회
// ============================================================================
export async function get(id: number): Promise<User | null> {
  try {
    return await httpEx.getJSON<User>(`users/${id}`, { timeoutMs: 8000 })
  } catch (err) {
    console.error('[Users.get] failed:', err)
    return null
  }
}

// ============================================================================
// 3️⃣ 사용자 활성/비활성 전환
// ----------------------------------------------------------------------------
// • PUT /api/users/{id}/approve { is_active : bool }
// ============================================================================
export async function approve(id: number, body: { is_active: boolean }): Promise<{ ok?: boolean }> {
  try {
    return await httpEx.putJSON<{ ok?: boolean }>(`users/${id}/approve`, body, { timeoutMs: 8000 })
  } catch (err) {
    console.error('[Users.approve] failed:', err)
    throw err
  }
}

/** ✅ 활성화 (Wrapper) */
export async function activate(id: number): Promise<{ ok?: boolean }> {
  return await approve(id, { is_active: true })
}

/** ✅ 비활성화 (Soft Delete) */
export async function deactivate(id: number): Promise<{ ok?: boolean }> {
  try {
    return await httpEx.deleteJSON<{ ok?: boolean }>(`users/${id}`, { timeoutMs: 8000 })
  } catch (err) {
    console.error('[Users.deactivate] failed:', err)
    throw err
  }
}

// ============================================================================
// 4️⃣ 사용자 ↔ 사원 매핑
// ----------------------------------------------------------------------------
// • PUT /api/users/{uid}/employee/{eid}
// ============================================================================
export async function mapEmployee(userId: number, empId: number): Promise<{ ok?: boolean }> {
  try {
    return await httpEx.putJSON<{ ok?: boolean }>(
      `users/${userId}/employee/${empId}`,
      {},
      { timeoutMs: 8000 }
    )
  } catch (err) {
    console.error('[Users.mapEmployee] failed:', err)
    throw err
  }
}

// ============================================================================
// ✅ EOF — src/services/users.ts (v3.7 Final Stable · SSOT 안정판)
// ============================================================================
