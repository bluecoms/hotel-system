// ============================================================================
// File      : src/services/master.ts
// Version   : 2025-10-28 · v2.0 (httpEx 기반 · Positions 추가 · Banks 업그레이드)
// Purpose   : Hotel Admin — Master Data Service (HR/운영 공통 기준정보 API)
// ----------------------------------------------------------------------------
// 목적
//   • HR / 운영 / 업무 모듈에서 공통으로 사용하는 "기준정보(Master Data)" API 모듈
//   • http-extended(httpEx) 기반으로 안정성(Abort/Retry/Timeout) 확보
//   • http.ts 의 baseURL이 이미 '/api'이므로 여기서는 절대 '/api'를 붙이지 않는다. (⚠ 중요)
// ----------------------------------------------------------------------------
// 포함 도메인 (총 9개):
//   1️⃣ Departments (부서)            : master/departments
//   2️⃣ Ranks       (직급)            : master/ranks
//   3️⃣ Titles      (직책)            : master/titles
//   4️⃣ Positions   (직위)    ✅ 신규 : master/positions
//   5️⃣ SalaryGrades(급여등급)        : master/salary-grades
//   6️⃣ EmpNoPolicy (사번정책)        : master/empno-policy
//   7️⃣ Properties  (지점/호텔)       : properties           (*기존 규격 유지)
//   8️⃣ Banks       (은행코드) ✅ 확장 : master/banks (+ options, order_no/meta/country_code)
//   9️⃣ (기타) options 엔드포인트 통일 : /options → [{ value, title }]
// ----------------------------------------------------------------------------
// 변경이력
//   - 2025-10-16 : DeptOut/TitleOut → order_no 필드 추가 (드래그 정렬용)
//   - 2025-10-17 : Titles(직책)에 salary 필드 확장, EmpNoPolicy 조회/저장 추가
//   - 2025-10-18 : Ranks/SalaryGrades 추가 (5대 마스터 완성)
//   - 2025-10-24 : Properties, Banks 추가 (7대 마스터)
//   - 2025-10-28 : httpEx 적용 · Positions(직위) 추가 · Banks 업그레이드 (v2.0)
// ============================================================================

import { httpEx } from '@/services/http-extended'

// ─────────────────────────────────────────────
// 공통 타입
// ─────────────────────────────────────────────
export type CodeNameItem = {
  id?: number | null
  code: string
  name: string
  // 선택 필드 (도메인별로 일부 사용)
  salary?: number | null
  base_salary?: number | null
  alias?: string | null
  order_no?: number | null
  is_active?: boolean | number | null
  country_code?: string | null
  meta?: Record<string, any> | null
}

// ─────────────────────────────────────────────
// httpEx 기본 옵션(안정성): timeout 15s / retry 2회
// ─────────────────────────────────────────────
const OPT = { timeoutMs: 15000, retry: { retries: 2 } }

// ============================================================================
// Departments (부서)
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

export async function createDepartment(item: { code: string; name: string }) {
  const payload = { property_code: 'MOP', dept_code: item.code, dept_name: item.name }
  return await httpEx.postJSON<any>('master/departments', payload, OPT)
}

export async function updateDepartment(
  id: number,
  patch: Partial<{ dept_name: string; parent_code: string | null; is_active: boolean | number; remarks: string | null }>
) {
  return await httpEx.putJSON<any>(`master/departments/${id}`, patch, OPT)
}

export async function deleteDepartment(id: number) {
  return await httpEx.deleteJSON<any>(`master/departments/${id}`, OPT)
}

export async function reorderDepartments(items: Array<{ id: number; order_no: number }>) {
  return await httpEx.putJSON<any>('master/departments/reorder', { items }, OPT)
}

/** ✅ 부서 옵션 목록 조회 */
export async function departmentOptions(params: { property_code?: string }) {
  const query = new URLSearchParams(params as any).toString()
  return await httpEx.getJSON<any>(`master/departments/options?${query}`, OPT)
}

// ============================================================================
// Ranks (직급)
// ============================================================================
export async function listRanks(): Promise<CodeNameItem[]> {
  const res = await httpEx.getJSON<any>('master/ranks', OPT)
  const items = Array.isArray(res?.items) ? res.items : Array.isArray(res) ? res : []
  return items.map((r: any) => ({
    id: r.id ?? null,
    code: r.code ?? '',
    name: r.name ?? '',
    base_salary: r.base_salary ?? null,
    order_no: r.order_no ?? null,
    is_active: r.is_active ?? null,
  }))
}

export async function createRank(item: { code: string; name: string; base_salary?: number }) {
  const payload: any = { code: item.code, name: item.name }
  if (item.base_salary != null) payload.base_salary = item.base_salary
  return await httpEx.postJSON<any>('master/ranks', payload, OPT)
}

export async function updateRank(
  id: number,
  patch: Partial<{ name: string; is_active: boolean | number; base_salary: number; order_no: number }>
) {
  return await httpEx.putJSON<any>(`master/ranks/${id}`, patch, OPT)
}

export async function deleteRank(id: number) {
  return await httpEx.deleteJSON<any>(`master/ranks/${id}`, OPT)
}

export async function reorderRanks(items: Array<{ id: number; order_no: number }>) {
  return await httpEx.putJSON<any>('master/ranks/reorder', { items }, OPT)
}

/** (선택) 직급 옵션 */
export async function rankOptions() {
  return await httpEx.getJSON<any>('master/ranks/options', OPT)
}

// ============================================================================
// Titles (직책)
// ============================================================================
export async function listTitles(): Promise<CodeNameItem[]> {
  const res = await httpEx.getJSON<any>('master/titles', OPT)
  const items = Array.isArray(res?.items) ? res.items : Array.isArray(res) ? res : []
  return items.map((t: any) => ({
    id: t.id ?? null,
    code: t.code ?? t.title_code ?? '',
    name: t.name ?? t.title_name ?? '',
    salary: t.salary ?? null,
    order_no: t.order_no ?? null,
    is_active: t.is_active ?? null,
  }))
}

export async function createTitle(item: { name: string; code?: string; salary?: number }) {
  const payload: any = { name: item.name }
  if (item.code) payload.code = item.code
  if (item.salary != null) payload.salary = item.salary
  return await httpEx.postJSON<any>('master/titles', payload, OPT)
}

export async function updateTitle(
  id: number,
  patch: Partial<{ name: string; is_active: boolean | number; salary: number; order_no: number }>
) {
  return await httpEx.putJSON<any>(`master/titles/${id}`, patch, OPT)
}

export async function deleteTitle(id: number) {
  return await httpEx.deleteJSON<any>(`master/titles/${id}`, OPT)
}

export async function reorderTitles(items: Array<{ id: number; order_no: number }>) {
  return await httpEx.putJSON<any>('master/titles/reorder', { items }, OPT)
}

/** (선택) 직책 옵션 */
export async function titleOptions() {
  return await httpEx.getJSON<any>('master/titles/options', OPT)
}

// ============================================================================
// ✅ Positions (직위) — 신규 추가
// ============================================================================
export async function listPositions(): Promise<CodeNameItem[]> {
  const res = await httpEx.getJSON<any>('master/positions', OPT)
  const items = Array.isArray(res?.items) ? res.items : Array.isArray(res) ? res : []
  return items.map((p: any) => ({
    id: p.id ?? null,
    code: p.code ?? '',
    name: p.name ?? '',
    order_no: p.order_no ?? null,
    is_active: p.is_active ?? null,
  }))
}

export async function createPosition(item: { code: string; name: string; order_no?: number; is_active?: boolean }) {
  const payload: any = { code: item.code, name: item.name }
  if (item.order_no != null) payload.order_no = item.order_no
  if (typeof item.is_active === 'boolean') payload.is_active = item.is_active
  return await httpEx.postJSON<any>('master/positions', payload, OPT)
}

export async function updatePosition(
  id: number,
  patch: Partial<{ code: string; name: string; order_no: number; is_active: boolean }>
) {
  return await httpEx.putJSON<any>(`master/positions/${id}`, patch, OPT)
}

export async function deletePosition(id: number) {
  return await httpEx.deleteJSON<any>(`master/positions/${id}`, OPT)
}

export async function reorderPositions(items: Array<{ id: number; order_no: number }>) {
  return await httpEx.putJSON<any>('master/positions/reorder', { items }, OPT)
}

/** ✅ 직위 옵션 */
export async function positionOptions() {
  return await httpEx.getJSON<any>('master/positions/options', OPT)
}

// ============================================================================
// Salary Grades (급여등급)
// ============================================================================
export async function listSalaryGrades(): Promise<CodeNameItem[]> {
  const res = await httpEx.getJSON<any>('master/salary-grades', OPT)
  const items = Array.isArray(res?.items) ? res.items : Array.isArray(res) ? res : []
  return items.map((g: any) => ({
    id: g.id ?? null,
    code: g.code ?? '',
    name: g.name ?? '',
    base_salary: g.annual_salary ?? g.base_salary ?? null,
    order_no: g.order_no ?? null,
    is_active: g.is_active ?? null,
  }))
}

export async function createSalaryGrade(item: { code: string; name: string; annual_salary?: number }) {
  const payload: any = { code: item.code, name: item.name }
  if (item.annual_salary != null) payload.annual_salary = item.annual_salary
  return await httpEx.postJSON<any>('master/salary-grades', payload, OPT)
}

export async function updateSalaryGrade(
  id: number,
  patch: Partial<{ name: string; is_active: boolean | number; annual_salary: number; order_no: number }>
) {
  return await httpEx.putJSON<any>(`master/salary-grades/${id}`, patch, OPT)
}

export async function deleteSalaryGrade(id: number) {
  return await httpEx.deleteJSON<any>(`master/salary-grades/${id}`, OPT)
}

export async function reorderSalaryGrades(items: Array<{ id: number; order_no: number }>) {
  return await httpEx.putJSON<any>('master/salary-grades/reorder', { items }, OPT)
}

// ============================================================================
// Emp No Policy (사번 정책)
// ============================================================================
export async function getEmpnoPolicy() {
  return await httpEx.getJSON<any>('master/empno-policy', OPT)
}

export async function saveEmpnoPolicy(data: {
  prefix: string
  start_no: number
  auto_increment?: boolean
  memo?: string
}) {
  return await httpEx.putJSON<any>('master/empno-policy', data, OPT)
}

export async function getNextEmpNo() {
  return await httpEx.getJSON<{ ok: boolean; next_emp_no: string }>('master/empno-policy/next', OPT)
}

// ============================================================================
// Properties (지점/호텔) — 기존 규격 유지 (prefix: 'properties')
// ============================================================================
export async function listProperties(): Promise<CodeNameItem[]> {
  const res = await httpEx.getJSON<any>('properties', OPT)
  const arr = Array.isArray(res?.items) ? res.items : Array.isArray(res) ? res : []
  return arr.map((r: any) => ({
    id: r.id ?? null,
    code: r.code ?? '',
    name: r.name ?? '',
  }))
}

export async function createProperty(item: { code: string; name: string }) {
  return await httpEx.postJSON<any>('properties', item, OPT)
}

// ============================================================================
// Banks (은행코드) — 업그레이드: alias / order_no / country_code / meta / options
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
    country_code: b.country_code ?? 'KR',
    meta: b.meta ?? null,
  }))
}

export async function createBank(item: {
  code: string
  name: string
  alias?: string
  order_no?: number
  is_active?: boolean
  country_code?: string
  meta?: Record<string, any>
}) {
  const payload: any = { code: item.code, name: item.name }
  if (item.alias) payload.alias = item.alias
  if (item.order_no != null) payload.order_no = item.order_no
  if (typeof item.is_active === 'boolean') payload.is_active = item.is_active
  if (item.country_code) payload.country_code = item.country_code
  if (item.meta) payload.meta = item.meta
  return await httpEx.postJSON<any>('master/banks', payload, OPT)
}

export async function updateBank(
  id: number,
  patch: Partial<{
    code: string
    name: string
    alias: string
    order_no: number
    is_active: boolean
    country_code: string
    meta: Record<string, any>
  }>
) {
  return await httpEx.putJSON<any>(`master/banks/${id}`, patch, OPT)
}

export async function deleteBank(id: number) {
  return await httpEx.deleteJSON<any>(`master/banks/${id}`, OPT)
}

/** ✅ 은행 옵션 (v-select) — [{value: code, title: name}] */
export async function bankOptions() {
  return await httpEx.getJSON<any>('master/banks/options', OPT)
}

/** (선택) 은행 정렬 저장 */
export async function reorderBanks(items: Array<{ id: number; order_no: number }>) {
  return await httpEx.putJSON<any>('master/banks/reorder', { items }, OPT)
}

// ============================================================================
// EOF — v2.0 (httpEx 기반 / Positions 추가 / Banks 업그레이드 / SSOT 규격)
// ============================================================================
