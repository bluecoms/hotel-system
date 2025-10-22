// ============================================================================
// File      : src/services/contracts.ts
// Version   : 1.7.0 (2025-10-28 FINAL · httpEx 기반 업그레이드)
// Purpose   : 계약(Contract) API 래퍼 (Hotel Admin HR 모듈)
// ----------------------------------------------------------------------------
// 목적
//   • 계약(Contract) 도메인 API 호출 일원화
//   • httpEx 기반 확장(fetch)으로 안정성/재시도/타임아웃 지원
//   • property_code 자동 반영 (localStorage or .env 기본값)
//   • axios 불사용 정책 유지 + SSOT 주석 규격 통일
//
// 주요 특징
//   ✅ property_code 자동 포함 (기본값 MOP)
//   ✅ 모든 호출은 /api/contracts 하위 엔드포인트를 사용
//   ✅ fetch 기반 http-extended.ts 적용 (Abort / Retry / Timeout 지원)
//   ✅ 타입 안정화 및 주석 규격 통일
// ----------------------------------------------------------------------------
// 백엔드 엔드포인트(최신 기준):
//   • GET    /api/contracts?property_code=MOP
//   • POST   /api/contracts
//   • GET    /api/contracts/history/{employee_id}
//   • POST   /api/contracts/terminate/{contract_id}
//   • PATCH  /api/contracts/{id}/end?date=YYYY-MM-DD
//   • PATCH  /api/contracts/{id}/activate
//   • POST   /api/contracts/{id}/upload (스캔본 업로드 + 자동 확정)
// ============================================================================
import { httpEx } from '@/services/http-extended'

// ─────────────────────────────────────────────
// 내부 유틸 — property_code 자동 주입
// ─────────────────────────────────────────────
function getPropertyCode(): string {
  return (
    localStorage.getItem('property_code') ||
    import.meta.env.VITE_DEFAULT_PROPERTY_CODE ||
    'MOP'
  )
}

// ─────────────────────────────────────────────
// 공통 옵션 — 안정성 기본값
//   • timeoutMs : 15초
//   • retry     : 2회 (지수 백오프)
// ─────────────────────────────────────────────
const DEFAULT_OPT = {
  timeoutMs: 15000,
  retry: { retries: 2 },
}

// ============================================================================
// 1️⃣ 계약 목록 조회
// ----------------------------------------------------------------------------
// 목적 : HR 화면(직원 계약 관리)에서 계약 목록 로드
// 경로 : GET /api/contracts?property_code=MOP
// 파라미터 : { employee_id?, latest_only?, property_code? }
// 반환형 : { items: [...], total: n }
// ============================================================================
export async function list(params?: Record<string, any>) {
  const qs = new URLSearchParams()
  const propertyCode = getPropertyCode()
  qs.append('property_code', propertyCode)

  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && String(v).trim() !== '') {
        qs.append(k, String(v))
      }
    }
  }

  const query = qs.toString() ? `?${qs.toString()}` : ''
  return await httpEx.getJSON<{ items: any[]; total: number }>(
    `contracts${query}`,
    DEFAULT_OPT
  )
}

// ============================================================================
// 2️⃣ 신규 계약 생성 (append-only)
// ----------------------------------------------------------------------------
// 목적 : DialogContractForm.vue에서 신규 계약 등록
// 경로 : POST /api/contracts
// ============================================================================
export async function create(data: Record<string, any>) {
  const payload = { property_code: getPropertyCode(), ...data }
  return await httpEx.postJSON<{ ok: boolean; id: number; contract_no?: string }>(
    'contracts',
    payload,
    DEFAULT_OPT
  )
}

// ============================================================================
// 3️⃣ 계약 이력 조회 (직원별)
// ----------------------------------------------------------------------------
// 목적 : 특정 직원의 과거 계약 이력 확인
// 경로 : GET /api/contracts/history/{employee_id}
// ============================================================================
export async function history(employeeId: number) {
  const propertyCode = getPropertyCode()
  return await httpEx.getJSON<{ items: any[]; total: number }>(
    `contracts/history/${employeeId}?property_code=${propertyCode}`,
    DEFAULT_OPT
  )
}

// ============================================================================
// 4️⃣ 계약 종료 (기본 종료 처리)
// ----------------------------------------------------------------------------
// 목적 : HR 화면에서 간단 종료 버튼 클릭 시 사용
// 경로 : POST /api/contracts/terminate/{contract_id}
// ============================================================================
export async function terminate(contractId: number) {
  const propertyCode = getPropertyCode()
  return await httpEx.postJSON<{ ok: boolean; terminated: number }>(
    `contracts/terminate/${contractId}?property_code=${propertyCode}`,
    undefined,
    DEFAULT_OPT
  )
}

// ============================================================================
// 5️⃣ 계약 종료 (종료일 지정형 v2)
// ----------------------------------------------------------------------------
// 목적 : HR 화면에서 종료일을 직접 지정할 때 사용
// 경로 : PATCH /api/contracts/{id}/end?date=YYYY-MM-DD&property_code=MOP
// ============================================================================
export async function endWithDate(contractId: number, endDate: string) {
  const propertyCode = getPropertyCode()
  return await httpEx.patchJSON<{ ok: boolean; id: number; end_date: string }>(
    `contracts/${contractId}/end?date=${endDate}&property_code=${propertyCode}`,
    undefined,
    DEFAULT_OPT
  )
}

// ============================================================================
// 6️⃣ 계약 확정 (인쇄 후 활성화)
// ----------------------------------------------------------------------------
// 목적 : 근로계약서 인쇄 후 '미계약 → 진행중' 으로 상태 변경
// 경로 : PATCH /api/contracts/{id}/activate
// ============================================================================
export async function activate(contractId: number) {
  const propertyCode = getPropertyCode()
  return await httpEx.patchJSON<{ ok: boolean; id: number; status: string }>(
    `contracts/${contractId}/activate?property_code=${propertyCode}`,
    undefined,
    DEFAULT_OPT
  )
}

// ============================================================================
// 7️⃣ 스캔본 업로드 (날인본 PDF/JPG → 자동 확정)
// ----------------------------------------------------------------------------
// 목적 : 계약서 날인본 업로드 후 계약을 자동 확정 처리
// 경로 : POST /api/contracts/{id}/upload
// Body  : multipart/form-data (file + start_date + end_date)
// ============================================================================
export async function uploadScan(
  contractId: number,
  file: File,
  extra: { start_date?: string | null; end_date?: string | null } = {}
) {
  const form = new FormData()
  form.append('file', file)
  if (extra.start_date) form.append('start_date', extra.start_date)
  if (extra.end_date) form.append('end_date', extra.end_date)

  return await httpEx.uploadForm<{ ok: boolean; id: number }>(
    `contracts/${contractId}/upload`,
    form,
    { ...DEFAULT_OPT, timeoutMs: 20000 } // 업로드는 타임아웃 20초
  )
}

// ============================================================================
// ✅ EOF — Version 1.7.0 (2025-10-28 / Final Stable · httpEx 기반 · Property-Safe)
// ============================================================================
