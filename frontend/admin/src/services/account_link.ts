// ============================================================================
// File      : src/services/account_link.ts
// Version   : 2025.11-10 · v1.0 (SSOT Stable)
// Purpose   : Hotel Admin — 직원 ↔ 사용자 계정 매핑 서비스
// ----------------------------------------------------------------------------
// 목적:
//   • HR 모듈의 "계정 매핑(직원-사용자 연결)" 기능 전용 API 서비스
//   • 백엔드 /api/users 엔드포인트 기반 통신
// ----------------------------------------------------------------------------
// 연결 백엔드 (app/routers/users.py):
//   • GET    /api/users                     → 사용자 목록 조회
//   • PUT    /api/users/{uid}/employee/{eid} → 사용자 ↔ 직원 매핑
//   • DELETE /api/users/{uid}/employee       → 매핑 해제
// ----------------------------------------------------------------------------
// 특징:
//   ✅ fetch 기반 http.ts 래퍼 사용 (axios 금지)
//   ✅ 인증 헤더 자동 주입 (X-Internal-Token)
//   ✅ HR, 시스템 관리 메뉴에서 공용 사용 가능
// ============================================================================

import http from '@/services/http'

/**
 *  사용자 목록 조회
 * @param params - { q?: string, page?: number, size?: number, status?: string }
 * @returns Promise<{ items: any[], total: number }>
 * 
 * 예시:
 *   await list({ q: '홍길동', page: 1, size: 20 })
 *   → GET /api/users?q=홍길동&page=1&size=20
 */
export async function list(params?: Record<string, any>) {
  const qs = params ? '?' + new URLSearchParams(params).toString() : ''
  return http.get('users' + qs)
}

/**
 *  사용자 ↔ 직원 매핑 (사원 연결)
 * @param userId - 사용자 ID
 * @param employeeId - 직원 ID
 * @returns Promise<{ ok: boolean }>
 * 
 * 예시:
 *   await mapEmployee(5, 3)
 *   → PUT /api/users/5/employee/3
 */
export async function mapEmployee(userId: number, employeeId: number) {
  return http.put(`users/${userId}/employee/${employeeId}`)
}

/**
 *  매핑 해제 (사용자 ↔ 직원 연결 해제)
 * @param userId - 사용자 ID
 * @returns Promise<{ ok: boolean }>
 * 
 * 예시:
 *   await unlinkEmployee(5)
 *   → DELETE /api/users/5/employee
 */
export async function unlinkEmployee(userId: number) {
  return http.delete(`users/${userId}/employee`)
}
