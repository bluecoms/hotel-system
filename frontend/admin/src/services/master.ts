// ============================================================================
// File      : src/services/master.ts
// Version   : 2.2 Final (2025-10-30 · HR 간소화 7차 Hotfix · SalaryGrade/통합옵션 보강)
// Purpose   : Hotel Admin — Master Data Service (HR/운영 공통 기준정보 API)
// ----------------------------------------------------------------------------
// 목적:
//   • HR/운영/기준정보 API 통합 관리 (httpEx 기반)
//   • HR 간소화 대응: 부서/직책/직급/급여등급/은행의 한글명 일원화
//   • 모든 함수의 반환형 통일 [{ code, name }] 또는 [{ title, value }]
//   • HR Form(DialogEmployeeForm.vue)과 완전 호환
// ----------------------------------------------------------------------------
// 변경 요약 (v2.2)
//   ✅ 급여등급(SalaryGrades) 추가 (annual_salary 포함)
//   ✅ listRanks → listSalaryGrades로 병합 경로 유지 (하위호환)
//   ✅ departmentOptions/titleOptions 등 HR Select 옵션 API 보강
//   ✅ loadHrMasterOptions()에서 SalaryGrades 포함
//   ✅ 주석 강화 및 구조 정돈
// ----------------------------------------------------------------------------
// 기술 사양:
//   • httpEx 기반 (Abort / Retry / Timeout 지원)
//   • timeout 15s, retry 2회 (지연시에도 안전)
//   • 반환 시 Null-safe 매핑
// ============================================================================

import { httpEx } from '@/services/http-extended'

// ─────────────────────────────────────────────
// 공통 타입 정의
// ─────────────────────────────────────────────
export type CodeNameItem = {
  id?: number | null
  code: string
  name: string
  alias?: string | null
  order_no?: number | null
  is_active?: boolean | number | null
  annual_salary?: number | null // 급여등급용 필드
}

const OPT = { timeoutMs: 15000, retry: { retries: 2 } }

// ============================================================================
// Departments (부서)
// ----------------------------------------------------------------------------
// • 부서코드(dept_code) + 부서명(dept_name) 한글화 일원화
// • 반환: [{ code, name }]
// ============================================================================
export async function listDepartments(): Promise<CodeNameItem[]> {
  const res = await httpEx.getJSON<any>('master/departments', OPT)
  const items = Array.isArray(res?.items) ? res.items : Array.isArray(res) ? res : []
  return items.map((d: any) => ({
    id: d.id ?? null,
    code: d.dept_code ?? d.code ?? '',
    name: d.dept_name ?? d.name ?? '',
    order_no: d.order_no ?? null,
    is_active: d.is_active ?? null,
  }))
}

// ============================================================================
// Titles (직책)
// ----------------------------------------------------------------------------
// • 반환: [{ code, name }]
// ============================================================================
export async function listTitles(): Promise<CodeNameItem[]> {
  const res = await httpEx.getJSON<any>('master/titles', OPT)
  const items = Array.isArray(res?.items) ? res.items : Array.isArray(res) ? res : []
  return items.map((t: any) => ({
    id: t.id ?? null,
    code: t.code ?? t.title_code ?? '',
    name: t.name ?? t.title_name ?? '',
    order_no: t.order_no ?? null,
    is_active: t.is_active ?? null,
  }))
}

// ============================================================================
// Salary Grades (급여등급)
// ----------------------------------------------------------------------------
// • HR 간소화: 연봉(annual_salary) → 월급 자동환산용으로 사용
// • 반환: [{ code, name, annual_salary }]
// ============================================================================
export async function listSalaryGrades(): Promise<CodeNameItem[]> {
  const res = await httpEx.getJSON<any>('master/salary-grades', OPT)
  const items = Array.isArray(res?.items) ? res.items : Array.isArray(res) ? res : []
  return items.map((r: any) => ({
    id: r.id ?? null,
    code: r.code ?? '',
    name: r.name ?? '',
    annual_salary: r.annual_salary ?? r.base_salary ?? null,
    order_no: r.order_no ?? null,
    is_active: r.is_active ?? null,
  }))
}

// ============================================================================
// (하위호환) Ranks (직급)
// ----------------------------------------------------------------------------
// • 기존 listRanks() → 내부적으로 listSalaryGrades() 호출
// ============================================================================
export async function listRanks(): Promise<CodeNameItem[]> {
  return await listSalaryGrades()
}

// ============================================================================
// Banks (은행코드)
// ----------------------------------------------------------------------------
// • 은행명(name) 기준 반환 [{ code, name }]
// • alias / order_no / country_code / meta 일부 보유
// ============================================================================
export async function listBanks(): Promise<CodeNameItem[]> {
  const res = await httpEx.getJSON<any>('master/banks', OPT)
  const arr = Array.isArray(res?.items) ? res.items : Array.isArray(res) ? res : []
  return arr.map((b: any) => ({
    id: b.id ?? null,
    code: b.code ?? '',
    name: b.name ?? '',
    alias: b.alias ?? null,
    order_no: b.order_no ?? null,
    is_active: b.is_active ?? null,
  }))
}

// ============================================================================
// 사번 정책 / EmpNoPolicy
// ----------------------------------------------------------------------------
// • 신규 직원 등록 시 사번 자동생성용(next_emp_no)
// ============================================================================
export async function getNextEmpNo() {
  return await httpEx.getJSON<{ ok: boolean; next_emp_no: string }>(
    'master/empno-policy/next',
    OPT
  )
}

// ============================================================================
// ✅ 옵션형 조회 (HR Select용) — [{ title, value }]
// ----------------------------------------------------------------------------
// • v-select용 표준 형식(title=value 표기)
// • 모두 httpEx 기반, HR 화면에서 직접 사용 가능
// ============================================================================
export async function departmentOptions() {
  return await httpEx.getJSON<any>('master/departments/options', OPT)
}

export async function titleOptions() {
  return await httpEx.getJSON<any>('master/titles/options', OPT)
}

export async function rankOptions() {
  return await httpEx.getJSON<any>('master/ranks/options', OPT)
}

export async function bankOptions() {
  return await httpEx.getJSON<any>('master/banks/options', OPT)
}

// ============================================================================
// ✅ HR 통합 로드 헬퍼 (DialogEmployeeForm / HR 페이지용)
// ----------------------------------------------------------------------------
// 목적:
//   • HR 다이얼로그 로딩 시 모든 기준정보 병렬 로드
//   • Promise.all 기반으로 성능 최적화
//   • 실패 시 빈 배열 반환으로 UI 오류 방지
// ============================================================================
export async function loadHrMasterOptions() {
  try {
    const [depts, titles, ranks, salaryGrades, banks] = await Promise.all([
      listDepartments(),
      listTitles(),
      listRanks(),
      listSalaryGrades(),
      listBanks(),
    ])
    return {
      departments: depts || [],
      titles: titles || [],
      ranks: ranks || [],
      salaryGrades: salaryGrades || [],
      banks: banks || [],
    }
  } catch (err) {
    console.error('[loadHrMasterOptions] failed:', err)
    return { departments: [], titles: [], ranks: [], salaryGrades: [], banks: [] }
  }
}

// ============================================================================
// ✅ EOF — v2.2 (HR 간소화 7차 / SalaryGrade 추가 / httpEx 기반 안정화)
// ============================================================================
