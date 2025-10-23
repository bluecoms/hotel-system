// ============================================================================
// File      : src/services/employees.ts
// Version   : 2.2.0 (2025-10-23 Final Stable · HR 간소화 4차)
// Purpose   : Hotel Admin — Employees Service (직원 관리 API 래퍼 · 계약정보 통합)
// ----------------------------------------------------------------------------
// 변경 요약 (v2.2)
//   ✅ createEmployee() : 계약정보(start/end/salary 등) 통합 입력 대응
//   ✅ getContractContext() : /api/employees/{id}/contract-context 표준화
//   ✅ axios 불사용 정책 유지(fetch 기반 http.ts)
//   ✅ property_code 자동 주입 (localStorage or .env 기본값)
//   ✅ 타입/주석 일관화 (HR 간소화 통합 버전)
// ----------------------------------------------------------------------------
// 백엔드 엔드포인트 (최신 기준)
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

// ─────────────────────────────────────────────
// 내부 유틸 — property_code 자동 획득
// ─────────────────────────────────────────────
function getPropertyCode(): string {
  return (
    localStorage.getItem('property_code') ||
    import.meta.env.VITE_DEFAULT_PROPERTY_CODE ||
    'MOP'
  )
}

// ─────────────────────────────────────────────
// 타입 정의
// ─────────────────────────────────────────────
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

  // 계약 관련 필드
  contract_status?: 'active' | 'terminated' | 'none'
  contract_start?: string | null
  contract_end?: string | null
  salary?: number | null
}

export type EmployeeListResp = {
  items: Employee[]
  total: number
  page?: number
  size?: number
}

// ============================================================================
// 1️⃣ 직원 목록 조회
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
  return await http.get<EmployeeListResp>(`employees${query}`)
}

// ============================================================================
// 2️⃣ 전체 조회 (셀렉터/캐시용)
// ============================================================================
export async function listAll(): Promise<EmployeeListResp['items']> {
  const res = await list()
  return res.items || []
}

// ============================================================================
// 3️⃣ 단건 조회
// ============================================================================
export async function getEmployee(id: number) {
  return await http.get<Employee>(`employees/${id}`)
}

// ============================================================================
// 4️⃣ 신규 생성 (계약정보 통합 입력)
// ----------------------------------------------------------------------------
// 목적 : 직원 등록 시 계약 필드(start_date, end_date, salary 등) 동시 전달
// ============================================================================
export async function createEmployee(data: Record<string, any>) {
  const payload = { property_code: getPropertyCode(), ...data }
  return await http.post<{ ok: boolean; id: number; emp_no?: string }>(
    'employees',
    payload
  )
}

// ============================================================================
// 5️⃣ 수정
// ============================================================================
export async function updateEmployee(id: number, patch: Partial<Employee>) {
  return await http.put<{ ok: boolean; id: number }>(`employees/${id}`, patch)
}

// ============================================================================
// 6️⃣ 삭제 (Soft Delete)
// ============================================================================
export async function deleteEmployee(id: number) {
  return await http.delete<{ ok: boolean }>(`employees/${id}`)
}

// ============================================================================
// 7️⃣ 사용자-사원 매핑
// ============================================================================
export async function mapUserEmployee(userId: number, empId: number) {
  return await http.put<{ ok: boolean }>(`users/${userId}/employee/${empId}`)
}

// ============================================================================
// 8️⃣ 계약 컨텍스트 조회
// ----------------------------------------------------------------------------
// 목적 : 계약서 작성 시 자동 입력 데이터 조회
// 경로 : GET /api/employees/{id}/contract-context
// ============================================================================
export async function getContractContext(id: number) {
  return await http.get<Record<string, any>>(`employees/${id}/contract-context`)
}

// ============================================================================
// 9️⃣ 템플릿 다운로드
// ============================================================================
export async function downloadTemplate(): Promise<Blob> {
  return await http.getBlob('templates/employees.csv')
}

// ============================================================================
// ✅ EOF — Version 2.2.0 (2025-10-23 Final Stable / HR 간소화 4차)
// ============================================================================
