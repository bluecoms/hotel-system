// ============================================================================
// File      : src/services/reports.ts
// Version   : 2025.10-20 Final Stable
// Purpose   : Reports API Service Layer (Frontend → Backend /api/reports/*)
// ----------------------------------------------------------------------------
// 주요 변경사항 (v2025.10-20)
//   ✅ BankLedgerSummary API 파라미터명 변경 대응 (date → business_date)
//   ✅ 백엔드 reports_bank.py v2025.10-20 호환
//   ✅ KPI, SalesTags, RoomsSplit, F&B 모듈 구조 및 타입 유지
// ----------------------------------------------------------------------------
// 요청 구조 요약
//   - KPI                → /reports/dashboard-kpi?property_code=&business_date=
//   - SalesTags          → /reports/sales-tags?date_from=&date_to=&property_code=
//   - RoomsSplit / F&B   → /reports/rooms-split, /reports/fnb-summary
//   - BankLedgerSummary  → /reports/bank_ledger?property_code=&business_date=&account_code=
// ============================================================================

import http from '@/services/http'

/** ─ KPI (기존 그대로) ─ */
export type KpiResponse = {
  ok: boolean
  property_code: string
  business_date: string
  room_only_amount: number
  package_amount: number
  other_amount: number
}

export async function getDashboardKPI(params: { date: string; property_code: string }) {
  const q = { business_date: params.date, property_code: params.property_code }
  const res = await http.get<KpiResponse>(`/reports/dashboard-kpi${http.qs(q)}`)
  if (!res?.ok) throw new Error('KPI 응답 실패')
  return {
    ...res,
    room_only_amount: Number(res.room_only_amount || 0),
    package_amount: Number(res.package_amount || 0),
    other_amount: Number(res.other_amount || 0),
  }
}

/** ─ SalesTags (기존 그대로) ─ */
export type SalesTagsItem = { tag: string; count: number; amount?: number; sales_amount?: number }
export type SalesTagsResponse = {
  ok: boolean
  property_code: string
  from: string
  to: string
  summary?: Record<string, any>
  items: Array<{ tag: string; count: number; amount?: number; sales_amount?: number }>
}
export async function getSalesTags(params: { date_from?: string; date_to?: string; property_code?: string }) {
  const res = await http.get<SalesTagsResponse>(`/reports/sales-tags${http.qs(params)}`)
  if (!res?.ok) throw new Error('SalesTags 응답 실패')
  res.items = Array.isArray(res.items) ? res.items : []
  return res
}
export async function exportSalesTags(params: { date_from?: string; date_to?: string; property_code?: string }) {
  return await http.getBlob(`/reports/sales-tags/export${http.qs(params)}`)
}

/** ─ Rooms Split / F&B (기존 그대로) ─ */
export type RoomsSplitResp = {
  property_code: string
  date_from: string
  date_to: string
  rooms: { room_only: number; package: number; cash: number; card: number; etc: number }
}
export async function getRoomsSplit(params: { date_from: string; date_to: string; property_code: string }) {
  return await http.get<RoomsSplitResp>(`/reports/rooms-split${http.qs(params)}`)
}
export type FnbRow = { category: string; amount: number; count: number }
export type FnbSummaryResp = { property_code: string; date_from: string; date_to: string; fnb: FnbRow[] }
export async function getFnbSummary(params: { date_from: string; date_to: string; property_code: string }) {
  return await http.get<FnbSummaryResp>(`/reports/fnb-summary${http.qs(params)}`)
}

/** ─ BankLedger (v2025.10-20 수정반영) ─ */
export type BankLedgerRow = {
  direction: 'IN' | 'OUT'
  amount: number | string
  note?: string
  branch?: string
  txn_time?: string
}

export type BankLedgerSummaryResp = {
  ok: boolean
  property_code: string
  business_date: string
  account_code: string
  in_amount: number | string
  out_amount: number | string
  net_amount: number | string
  last_balance: number | string | null
  items: BankLedgerRow[]
  version_no?: number
}

/**
 * Bank Ledger Summary
 * - 백엔드 reports_bank.py (v2025.10-20) 대응
 * - business_date 기준으로 요청
 */
export async function getBankLedgerSummary(params: {
  business_date: string
  property_code: string
  account_code: string
}) {
  const res = await http.get<BankLedgerSummaryResp>(`/reports/bank_ledger${http.qs(params)}`)
  if (!res?.ok) throw new Error('Bank ledger 응답 실패')
  return {
    ...res,
    in_amount: Number(res.in_amount || 0),
    out_amount: Number(res.out_amount || 0),
    net_amount: Number(res.net_amount || 0),
    last_balance: res.last_balance == null ? null : Number(res.last_balance),
    items: (res.items || []).map(r => ({
      ...r,
      amount: Number(r.amount || 0),
    })),
  }
}
