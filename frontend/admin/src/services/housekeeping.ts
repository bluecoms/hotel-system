// ============================================================================
// File      : src/services/housekeeping.ts
// Version   : 2025.11-04 · v1.1 (fetch 기반 타입 보정)
// Purpose   : Hotel Admin — 하우스키핑 API 서비스 (fetch 기반, QueryString 지원)
// ----------------------------------------------------------------------------
// 수정사항:
//   ✅ axios-style { params } 제거
//   ✅ URLSearchParams 로 쿼리 구성
//   ✅ http.get<T>() 제너릭 지정으로 타입 추론 보강
// ============================================================================

import http from '@/services/http'

export async function getHousekeepingTasks(params: {
  business_date: string
  property_code?: string
}) {
  const query = new URLSearchParams(params as Record<string, string>).toString()
  return await http.get<any[]>(`/housekeeping/tasks?${query}`)
}

export async function createHousekeepingTask(payload: any) {
  return await http.post('/housekeeping/task', payload)
}

export async function completeHousekeepingTask(id: number) {
  return await http.post(`/housekeeping/task/${id}/complete`)
}

export async function getHousekeepingStats(params: {
  business_date: string
  property_code?: string
}) {
  const query = new URLSearchParams(params as Record<string, string>).toString()
  return await http.get<{ by_staff: any[] }>(`/housekeeping/stats/units?${query}`)
}
