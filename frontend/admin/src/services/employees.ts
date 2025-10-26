// ============================================================================
// File      : src/services/employees.ts
// Version   : 2.3.0 (2025-11-05 · SSOT Final · Safe Fallback / Prefix Auto)
// Purpose   : Hotel Admin — Employees Service (직원 관리 + 계약정보 통합)
// ----------------------------------------------------------------------------
// 목적:
//   • /api/employees 계열 API 호출 래퍼(fetch 기반).
//   • 직원 기본정보 + 계약정보(start/end/salary 등) 통합 관리.
// ----------------------------------------------------------------------------
// 주요 개선 (v2.3):
//   ✅ list() : 빈 응답 / total 누락 대응 (fallback)
//   ✅ createEmployee / updateEmployee : try-catch + console 보강
//   ✅ API prefix 자동 보정 (/api/ 생략 시에도 안전 호출)
//   ✅ 주석·타입 SSOT 통일 (auth/bank/master 스타일과 일치)
// ----------------------------------------------------------------------------
// 연동 백엔드 (최신 기준):
//   • GET    /api/employees?property_code=MOP
//   • POST   /api/employees
//   • GET    /api/employees/{id}
//   • PUT    /api/employees/{id}
//   • DELETE /api/employees/{id}
//   • PUT    /api/users/{userId}/employee/{empId}
//   • GET    /api/employees/{id}/contract-context
//   • GET    /api/templates/employees.csv
// ============================================================================

import http from '@/services/http'

// ----------------------------------------------------------------------------
//  내부 유틸 — property_code 자동 획득
// ----------------------------------------------------------------------------
function getPropertyCode(): string {
  return (
    localStorage.getItem('property_code') ||
    import.meta.env.VITE_DEFAULT_PROPERTY_CODE ||
    'MOP'
  )
}

// ----------------------------------------------------------------------------
//  타입 정의
// ----------------------------------------------------------------------------
export interface Employee {
  id: number
  property_code?: string
  emp_no: string
  name: string
  dept?: string
  dept_name?: string
  title?: string
  title_name?: string
  position?: string
  rank?: string
  phone?: string
  email?: string
  address?: string
  hire_date?: string
  leave_date?: string
  rrn_mask?: string
  bank_name?: string
  account_mask?: string
  account_last4?: string
  memo?: string
  contract_status?: 'active' | 'terminated' | 'none'
  contract_start?: string | null
  contract_end?: string | null
  salary?: number | null
}

export type EmployeeListResp = {
  ok?: boolean
  items: Employee[]
  total: number
  page?: number
  size?: number
}

// ============================================================================
// 1️⃣ 직원 목록 조회 (검색·필터·정렬)
// ============================================================================
export async function list(params?: Record<string, any>) {
  const qs = new URLSearchParams()
  qs.append('property_code', getPropertyCode())

  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && String(v).trim() !== '') {
        qs.append(k, String(v))
      }
    }
  }

  const query = qs.toString() ? `?${qs.toString()}` : ''
  try {
    const res = await http.get<EmployeeListResp>(`/employees${query}`)
    return {
      items: Array.isArray(res?.items) ? res.items : [],
      total: Number(res?.total ?? res?.items?.length ?? 0),
    }
  } catch (err) {
    console.error('[employees.list] failed:', err)
    return { items: [], total: 0 }
  }
}

// ============================================================================
// 2️⃣ 전체 목록 (셀렉터/캐시용)
// ============================================================================
export async function listAll(): Promise<EmployeeListResp['items']> {
  const res = await list()
  return res.items || []
}

// ============================================================================
// 3️⃣ 단건 조회
// ============================================================================
export async function getEmployee(id: number) {
  return await http.get<Employee>(`/employees/${id}`)
}

// ============================================================================
// 4️⃣ 신규 생성 (계약정보 포함)
// ============================================================================
export async function createEmployee(data: Record<string, any>) {
  const payload = { property_code: getPropertyCode(), ...data }
  try {
    return await http.post<{ ok: boolean; id: number; emp_no?: string }>(
      '/employees',
      payload
    )
  } catch (err) {
    console.error('[employees.createEmployee] failed:', err)
    throw err
  }
}

// ============================================================================
// 5️⃣ 수정
// ============================================================================
export async function updateEmployee(id: number, patch: Partial<Employee>) {
  try {
    return await http.put<{ ok: boolean; id: number }>(`/employees/${id}`, patch)
  } catch (err) {
    console.error('[employees.updateEmployee] failed:', err)
    throw err
  }
}

// ============================================================================
// 6️⃣ 삭제 (Soft Delete)
// ============================================================================
export async function deleteEmployee(id: number) {
  try {
    return await http.delete<{ ok: boolean }>(`/employees/${id}`)
  } catch (err) {
    console.error('[employees.deleteEmployee] failed:', err)
    throw err
  }
}

// ============================================================================
// 7️⃣ 사용자-사원 매핑
// ============================================================================
export async function mapUserEmployee(userId: number, empId: number) {
  return await http.put<{ ok: boolean }>(`/users/${userId}/employee/${empId}`)
}

// ============================================================================
// 8️⃣ 계약 컨텍스트 조회
// ============================================================================
export async function getContractContext(id: number) {
  return await http.get<Record<string, any>>(`/employees/${id}/contract-context`)
}

// ============================================================================
// 9️⃣ 템플릿 다운로드
// ============================================================================
export async function downloadTemplate(): Promise<Blob> {
  return await http.getBlob('/templates/employees.csv')
}

// ============================================================================
// ✅ EOF — src/services/employees.ts (v2.3 Final · SSOT 안정판)
// ============================================================================
