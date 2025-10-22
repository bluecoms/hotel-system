// src/services/contracts.ts
import http from '@/services/http'

// 계약 목록 조회
export async function list(params?: Record<string, any>) {
  const qs = params ? '?' + new URLSearchParams(params).toString() : ''
  return http.get('/contracts' + qs)
}

// 계약 신규 생성 (append-only)
export async function create(data: Record<string, any>) {
  return http.post('/contracts', data)
}

// 계약 이력 조회
export async function history(employeeId: number) {
  return http.get(`/contracts/history/${employeeId}`)
}

// 계약 종료 처리
export async function terminate(contractId: number) {
  return http.post(`/contracts/terminate/${contractId}`)
}
