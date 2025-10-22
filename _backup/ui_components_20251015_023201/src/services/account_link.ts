// src/services/hr_dashboard.ts
import http from '@/services/http'

// 직원 ↔ 사용자 계정 매핑 목록
export async function list(params?: Record<string, any>) {
  const qs = params ? '?' + new URLSearchParams(params).toString() : ''
  return http.get('/api/user-roles' + qs)
}

// 직원으로부터 계정 생성
export async function createFromEmployee(data: Record<string, any>) {
  return http.post('/api/users/from-employee', data)
}

// 매핑 삭제
export async function unlink(data: Record<string, any>) {
  return http.delete('/api/user-roles', {
    body: JSON.stringify(data),
  })
}