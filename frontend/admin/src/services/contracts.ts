// ============================================================================
// File      : src/services/contracts.ts
// Version   : 2.3.0 (2025-10-23 Final · HR 간소화 연동 / Auto-Activate Safe)
// Purpose   : 계약(Contract) API 래퍼 (Hotel Admin HR 모듈)
// ----------------------------------------------------------------------------
// 목적
//   • 계약(Contract) 도메인 API 호출 일원화
//   • httpEx 기반 확장(fetch)으로 안정성/재시도/타임아웃 지원
//   • property_code 자동 반영 (localStorage or .env 기본값)
//   • axios 불사용 정책 유지 + SSOT 주석 규격 통일
// ----------------------------------------------------------------------------
// 주요 개선 (v2.3)
//   ✅ uploadScan() → 업로드 후 자동 activate() 호출 (Auto-Activate Safe)
//   ✅ 타입 일관성 보강 (ok/id/status 등 명시)
//   ✅ 주석 및 옵션 구조 재정비
// ----------------------------------------------------------------------------
// 백엔드 엔드포인트(최신 기준):
//   • GET    /api/contracts?property_code=MOP
//   • POST   /api/contracts
//   • GET    /api/contracts/history/{employee_id}
//   • POST   /api/contracts/terminate/{contract_id}
//   • PATCH  /api/contracts/{id}/end?date=YYYY-MM-DD
//   • PATCH  /api/contracts/{id}/activate
//   • POST   /api/contracts/{id}/upload  (스캔본 업로드 + 자동 확정)
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
// ─────────────────────────────────────────────
const DEFAULT_OPT = {
  timeoutMs: 15000,
  retry: { retries: 2 },
}

// ============================================================================
// 1️⃣ 계약 목록 조회
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
// ============================================================================
export async function history(employeeId: number) {
  const propertyCode = getPropertyCode()
  return await httpEx.getJSON<{ items: any[]; total: number }>(
    `contracts/history/${employeeId}?property_code=${propertyCode}`,
    DEFAULT_OPT
  )
}

// ============================================================================
// 4️⃣ 계약 종료 (기본 종료)
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
// 5️⃣ 계약 종료 (종료일 지정형)
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
//  • uploadScan() 성공 시 백엔드가 auto-activate 처리
//  • 단, 일부 환경에서 activate 분리 시 → 여기서 보조 호출 수행
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

  const res = await httpEx.uploadForm<{ ok: boolean; id: number }>(
    `contracts/${contractId}/upload`,
    form,
    { ...DEFAULT_OPT, timeoutMs: 20000 }
  )

  try {
    if (res?.ok && contractId) {
      // 업로드 직후 자동 확정 보조 호출 (fail-safe)
      await activate(contractId)
    }
  } catch (err) {
    console.warn('[contracts.uploadScan] auto-activate skip:', err)
  }
  return res
}

// ============================================================================
// ✅ EOF — Version 2.3.0 (2025-10-23 / HR 간소화 연동 · Auto-Activate Safe)
// ============================================================================
