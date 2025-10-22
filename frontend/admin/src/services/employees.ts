// ============================================================================
// File      : src/services/employees.ts
// Version   : 2025.10 Final Stable (v3.6 · SSOT / Property Sync)
// Purpose   : Hotel Admin — Employees Service (직원 관리 API 래퍼)
// ----------------------------------------------------------------------------
// 목적
//   • 직원(Employees) 도메인 API 호출 일원화
//   • property_code 기반 지점 단위 조회/생성/수정/삭제
//   • fetch 기반 http.ts 통합 (axios 불사용 정책 유지)
//
// 주요 특징
//   ✅ property_code 자동 주입 (localStorage or .env 기본값)
//   ✅ list() → 서버 페이징 응답 그대로 반환
//   ✅ listAll() → items만 평탄화
//   ✅ 타입 안정성 확보 및 주석 규격 통일
//
// 백엔드 엔드포인트 (v3.6 기준)
//   • GET    /api/employees?property_code=MOP
//   • POST   /api/employees
//   • GET    /api/employees/{id}
//   • PUT    /api/employees/{id}
//   • DELETE /api/employees/{id}
//   • PUT    /api/users/{userId}/employee/{empId}
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
  contract_start?: string
  contract_end?: string
}

export type EmployeeListResp = {
  items: Employee[]
  total: number
  page?: number
  size?: number
}

// ─────────────────────────────────────────────
// 1️⃣ 직원 목록 조회
// ----------------------------------------------------------------------------
// 목적 : HR 화면에서 직원 목록 로드
// 경로 : GET /api/employees?property_code=MOP
// ============================================================================
export async function list(params?: Record<string, any>) {
  const qs = new URLSearchParams()

  // ✅ property_code 자동 추가
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

// ─────────────────────────────────────────────
// 2️⃣ 전체 조회 (셀렉터/캐시용)
// ----------------------------------------------------------------------------
// 목적 : 직원 선택용 셀렉터 구성 시 전체 목록 로드
// ============================================================================
export async function listAll(): Promise<EmployeeListResp['items']> {
  const res = await list()
  return res.items || []
}

// ─────────────────────────────────────────────
// 3️⃣ 단건 조회
// ----------------------------------------------------------------------------
// 목적 : 특정 직원 상세 정보 조회
// 경로 : GET /api/employees/{id}
// ============================================================================
export async function getEmployee(id: number) {
  return await http.get<Employee>(`employees/${id}`)
}

// ─────────────────────────────────────────────
// 4️⃣ 신규 생성
// ----------------------------------------------------------------------------
// 목적 : 직원 신규 등록 (property_code 자동 주입)
// ============================================================================
export async function createEmployee(data: Record<string, any>) {
  const payload = { property_code: getPropertyCode(), ...data }
  return await http.post<{ ok: boolean; id: number; emp_no?: string }>(
    'employees',
    payload
  )
}

// ─────────────────────────────────────────────
// 5️⃣ 수정
// ----------------------------------------------------------------------------
// 목적 : 직원 정보 수정 (부분 갱신 허용)
// ============================================================================
export async function updateEmployee(id: number, patch: Partial<Employee>) {
  return await http.put<{ ok: boolean; id: number }>(`employees/${id}`, patch)
}

// ─────────────────────────────────────────────
// 6️⃣ 삭제
// ----------------------------------------------------------------------------
// 목적 : 직원 삭제 (Soft Delete)
// ============================================================================
export async function deleteEmployee(id: number) {
  return await http.delete<{ ok: boolean }>(`employees/${id}`)
}

// ─────────────────────────────────────────────
// 7️⃣ 사용자-사원 매핑
// ----------------------------------------------------------------------------
// 목적 : 사용자(User)와 직원(Employee) 연결
// 경로 : PUT /api/users/{userId}/employee/{empId}
// ============================================================================
export async function mapUserEmployee(userId: number, empId: number) {
  return await http.put<{ ok: boolean }>(`users/${userId}/employee/${empId}`)
}

// ─────────────────────────────────────────────
// 8️⃣ 템플릿 다운로드
// ----------------------------------------------------------------------------
// 목적 : 직원 CSV 업로드용 템플릿 파일 다운로드
// ============================================================================
export async function downloadTemplate(): Promise<Blob> {
  return await http.getBlob('templates/employees.csv')
}

// ============================================================================
// ✅ EOF — Version 2025.10-22 (Stable / Property-Safe / SSOT)
// ============================================================================
