// src/services/hr_dashboard.ts
import http from '@/services/http'

// HR KPI 대시보드 요약
export async function getSummary(params?: Record<string, any>) {
  return await http.get('/hr/dashboard/summary', params)
}

// 향후 추가 대비용 빈 함수 (Dashboard.vue 참조)
export async function getTrend(params?: Record<string, any>) {
  return await http.get('/hr/dashboard/trend', params)
}