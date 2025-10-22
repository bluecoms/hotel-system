// src/services/employees.ts
import http from '@/services/http'

export type EmployeeListResp = {
  items: any[]
  total: number
}

/** 직원 목록 조회 */
export async function list(params?: Record<string, any>) {
  return await http.get<EmployeeListResp>('/hr/employees', params)
}

/** 특정 직원 상세 조회 */
export async function getEmployee(id: number) {
  return await http.get(`/hr/employees/${id}`)
}

/** 직원 정보 수정/저장 */
export async function saveEmployee(id: number, patch: any) {
  return await http.put(`/hr/employees/${id}`, patch)
}

/** 사용자-직원 매핑 */
export async function mapUserEmployee(userId: number, empId: number) {
  return await http.put(`/hr/users/${userId}/employee/${empId}`)
}

/** ✅ 직원 템플릿 다운로드 (표준 fetch 사용) */
export async function downloadTemplate(): Promise<Blob> {
  const res = await fetch('/api/templates/employees.csv', {
    headers: { 'X-Internal-Token': localStorage.getItem('internalToken') || '' },
  })
  if (!res.ok) throw new Error('템플릿 다운로드 실패')
  return await res.blob()
}
