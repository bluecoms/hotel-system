// ============================================================================
// File      : src/services/hr_dashboard.ts
// Version   : 2025.11-10 · v1.2 (Fixed user-roles → users)
// Purpose   : Hotel Admin — HR 대시보드 / 계정 매핑 서비스
// ----------------------------------------------------------------------------
// 목적:
//   • 직원(Employee) ↔ 사용자(User) 계정 매핑 관리용 API 래퍼
//   • 백엔드 /api/users 라우터 기반으로 통신 (user-roles 제거)
// ----------------------------------------------------------------------------
// 주요 수정사항 (v1.2)
//   ✅ 기존 잘못된 경로 '/user-roles' → '/users' 로 수정
//   ✅ DELETE 요청 시 body 전송 → JSON.stringify 로 안전 처리 유지
//   ✅ 모든 함수에 상세 주석 추가
// ----------------------------------------------------------------------------
// 연결 백엔드 (app/routers/users.py):
//   • GET    /api/users              → 사용자 목록 조회 (페이징/검색 지원)
//   • POST   /api/users/from-employee → 직원으로부터 사용자 생성
//   • DELETE /api/users               → 매핑 해제 (unlink)
// ============================================================================

import http from '@/services/http'

/**
 *  사용자 목록 조회 (직원 ↔ 사용자 매핑 현황)
 * @param params - { page, size, q, status 등 }
 * @returns Promise<{ items: any[], total: number }>
 * 
 * 예시:
 *   list({ page: 1, size: 20, q: '홍길동' })
 *   → GET /api/users?page=1&size=20&q=홍길동
 */
export async function list(params?: Record<string, any>) {
  const qs = params ? '?' + new URLSearchParams(params).toString() : ''
  return http.get('users' + qs) // ✅ '/user-roles' → '/users' 로 변경
}

/**
 *  직원으로부터 사용자 계정 생성
 * @param data - { employee_id, email, name, roles[] 등 }
 * @returns Promise<any>
 * 
 * 예시:
 *   createFromEmployee({ employee_id: 3 })
 *   → POST /api/users/from-employee
 */
export async function createFromEmployee(data: Record<string, any>) {
  return http.post('users/from-employee', data)
}

/**
 *  계정 매핑 해제 (사용자 ↔ 직원 연결 끊기)
 * @param data - { user_id, employee_id }
 * @returns Promise<any>
 * 
 * 예시:
 *   unlink({ user_id: 5, employee_id: 3 })
 *   → DELETE /api/users
 */
export async function unlink(data: Record<string, any>) {
  return http.delete('users', {
    body: JSON.stringify(data),
  })
}
