// src/services/records.ts
import http from '@/services/http'

/**
 * 근태 기록 조회
 */
export async function list(params: any) {
  const query = new URLSearchParams(params).toString()
  return await http.get(`/records?${query}`)
}

/**
 * 근태 기록 수정
 */
export async function update(id: number, patch: any) {
  return await http.put(`/records/${id}`, patch)
}

/**
 * 근태 기록 삭제
 */
export async function remove(id: number) {
  return await http.delete(`/records/${id}`)
}
