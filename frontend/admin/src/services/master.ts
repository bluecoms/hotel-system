// ============================================================================
// File      : src/services/master.ts
// Version   : 2.5 Final (2025-11-09 · SSOT Phase 4 Final · RoomType/HKUnitRule Added)
// Purpose   : Hotel Admin — Master Data Service (HR/운영/기준정보 통합)
// ----------------------------------------------------------------------------
// 목적:
//   • HR/운영/기준정보 API 통합 관리 (httpEx 기반).
//   • 부서/직책/직급/급여등급/은행 + 지점(Property) + 객실타입/단위규칙 일원화.
//   • DialogEmployeeForm / HR 모듈 / Reports / Master 관리화면 등과 완전 호환.
// ----------------------------------------------------------------------------
// 주요 개선 (v2.5):
//   ✅ 객실 타입(RoomType) 기준정보 추가 (/api/master/room-types)
//   ✅ 하우스키핑 단위규칙(UnitRule) 기준정보 추가 (/api/master/hk-unit-rules)
//   ✅ Property/Bank/HR Master 구조와 동일한 httpEx 패턴 유지
// ----------------------------------------------------------------------------
// 기술 사양:
//   • httpEx 기반 (Abort / Retry / Timeout 지원)
//   • timeout 15s, retry 2회 (지연시에도 안전)
//   • 반환 시 Null-safe 매핑 (map/?? 적용)
// ============================================================================

import { httpEx } from '@/services/http-extended'

// ----------------------------------------------------------------------------
//  공통 타입 정의
// ----------------------------------------------------------------------------
export type CodeNameItem = {
  id?: number | null
  code: string
  name: string
  alias?: string | null
  order_no?: number | null
  is_active?: boolean | number | null
  annual_salary?: number | null
  unit_value?: number | null
  description?: string | null
}

const OPT = { timeoutMs: 15000, retry: { retries: 2 } }

// ============================================================================
// 0) Properties (지점 기준정보 · SSOT 구조)
// ----------------------------------------------------------------------------
export async function listMasterProperties(): Promise<CodeNameItem[]> {
  try {
    const res = await httpEx.getJSON<any>('master/properties', OPT)
    const items = Array.isArray(res?.items) ? res.items : Array.isArray(res) ? res : []
    return items.map((p: any) => ({
      code: p.code ?? '',
      name: p.name ?? '',
      is_active: p.is_active ?? true,
    }))
  } catch (err) {
    console.warn('[listMasterProperties] failed:', err)
    return []
  }
}

export async function createMasterProperty(data: {
  code: string
  name: string
  is_active?: boolean
}) {
  try {
    return await httpEx.postJSON('master/properties', data, OPT)
  } catch (err) {
    console.error('[createMasterProperty] failed:', err)
    throw err
  }
}

export async function updateMasterProperty(
  code: string,
  patch: { name?: string; is_active?: boolean }
) {
  try {
    return await httpEx.putJSON(`master/properties/${code}`, patch, OPT)
  } catch (err) {
    console.error('[updateMasterProperty] failed:', err)
    throw err
  }
}

export async function deleteMasterProperty(code: string) {
  try {
    return await httpEx.deleteJSON(`master/properties/${code}`, OPT)
  } catch (err) {
    console.error('[deleteMasterProperty] failed:', err)
    throw err
  }
}

// ============================================================================
// 1) Departments (부서)
// ----------------------------------------------------------------------------
export async function listDepartments(): Promise<CodeNameItem[]> {
  try {
    const res = await httpEx.getJSON<any>('master/departments', OPT)
    const items = Array.isArray(res?.items) ? res.items : Array.isArray(res) ? res : []
    return items.map((d: any) => ({
      id: d.id ?? null,
      code: d.dept_code ?? d.code ?? '',
      name: d.dept_name ?? d.name ?? '',
      order_no: d.order_no ?? null,
      is_active: d.is_active ?? null,
    }))
  } catch (err) {
    console.warn('[listDepartments] failed:', err)
    return []
  }
}

// ============================================================================
// 2) Titles (직책)
// ----------------------------------------------------------------------------
export async function listTitles(): Promise<CodeNameItem[]> {
  try {
    const res = await httpEx.getJSON<any>('master/titles', OPT)
    const items = Array.isArray(res?.items) ? res.items : Array.isArray(res) ? res : []
    return items.map((t: any) => ({
      id: t.id ?? null,
      code: t.code ?? t.title_code ?? '',
      name: t.name ?? t.title_name ?? '',
      order_no: t.order_no ?? null,
      is_active: t.is_active ?? null,
    }))
  } catch (err) {
    console.warn('[listTitles] failed:', err)
    return []
  }
}

// ============================================================================
// 3) Salary Grades (급여등급)
// ----------------------------------------------------------------------------
export async function listSalaryGrades(): Promise<CodeNameItem[]> {
  try {
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
  } catch (err) {
    console.warn('[listSalaryGrades] failed:', err)
    return []
  }
}

// ============================================================================
// 4) (하위호환) Ranks (직급)
// ----------------------------------------------------------------------------
export async function listRanks(): Promise<CodeNameItem[]> {
  return await listSalaryGrades()
}

// ============================================================================
// 5) Banks (은행코드)
// ----------------------------------------------------------------------------
export async function listBanks(): Promise<CodeNameItem[]> {
  try {
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
  } catch (err) {
    console.warn('[listBanks] failed:', err)
    return []
  }
}

// ============================================================================
// 6) 사번 정책 / EmpNoPolicy
// ----------------------------------------------------------------------------
export async function getNextEmpNo() {
  return await httpEx.getJSON<{ ok: boolean; next_emp_no: string }>(
    'master/empno-policy/next',
    OPT
  )
}

// ============================================================================
// 7) 옵션형 조회 (v-select용)
// ----------------------------------------------------------------------------
async function safeGetJSON(url: string, fallback: () => Promise<any>) {
  try {
    return await httpEx.getJSON<any>(url, OPT)
  } catch (err: any) {
    if (String(err).includes('405')) {
      console.warn(`[${url}] → fallback list() 호출`)
      return await fallback()
    }
    console.warn(`[${url}] failed:`, err)
    return []
  }
}

/** 부서 옵션 [{ title, value }] */
export async function departmentOptions() {
  return await safeGetJSON('master/departments/options', listDepartments)
}

/** 직책 옵션 [{ title, value }] */
export async function titleOptions() {
  return await safeGetJSON('master/titles/options', listTitles)
}

/** 직급(급여등급) 옵션 [{ title, value }] */
export async function rankOptions() {
  return await safeGetJSON('master/salary-grades/options', listSalaryGrades)
}

/** 은행 옵션 [{ title, value }] */
export async function bankOptions() {
  return await safeGetJSON('master/banks/options', listBanks)
}

// ============================================================================
// 8) HR 통합 로드 (DialogEmployeeForm / HR 페이지 공통)
// ----------------------------------------------------------------------------
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
// ️⃣9) 객실 타입 (RoomType · /api/master/room-types)
// ----------------------------------------------------------------------------
export async function listRoomTypes(): Promise<CodeNameItem[]> {
  try {
    const res = await httpEx.getJSON<any>('master/room-types', OPT)
    const arr = Array.isArray(res?.items) ? res.items : Array.isArray(res) ? res : []
    return arr.map((r: any) => ({
      id: r.id ?? null,
      code: r.code ?? '',
      name: r.name ?? '',
      unit_value: r.unit_value ?? 1.0,
      description: r.description ?? '',
      is_active: r.is_active ?? 1,
    }))
  } catch (err) {
    console.warn('[listRoomTypes] failed:', err)
    return []
  }
}

// ============================================================================
// 10) 하우스키핑 단위규칙 (HK Unit Rule · /api/master/hk-unit-rules)
// ----------------------------------------------------------------------------
export async function listHkUnitRules(): Promise<CodeNameItem[]> {
  try {
    const res = await httpEx.getJSON<any>('master/hk-unit-rules', OPT)
    const arr = Array.isArray(res?.items) ? res.items : Array.isArray(res) ? res : []
    return arr.map((r: any) => ({
      id: r.id ?? null,
      code: r.condition_code ?? '',
      name: r.description ?? '',
      unit_value: r.unit_value ?? 1.0,
      is_active: r.is_active ?? 1,
    }))
  } catch (err) {
    console.warn('[listHkUnitRules] failed:', err)
    return []
  }
}

// ============================================================================
// ✅ EOF — src/services/master.ts (v2.5 Final · SSOT Phase 4 완전판)
// ============================================================================
