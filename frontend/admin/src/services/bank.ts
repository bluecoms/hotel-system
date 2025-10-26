// ============================================================================
// File      : src/services/bank.ts
// Version   : 2025.11-05 · v2.0 (SSOT Consistent · DefaultParam Safe)
// Purpose   : Hotel Admin — Bank Ledger Report Service (은행 입출금 리포트)
// ----------------------------------------------------------------------------
// 목적:
//   • /api/reports/bank_ledger API 래퍼.
//   • 거래 내역(입금·출금) 및 일자별 합계 리포트 구조 표준화.
// ----------------------------------------------------------------------------
// 주요 개선 (v2.0):
//   ✅ property_code 기본값 'MOP' 자동 보정
//   ✅ 타입 주석 강화 (rows, totals, balance_after 등)
//   ✅ 코드/주석 SSOT 표준 양식 통일 (auth/master 등과 동일)
// ----------------------------------------------------------------------------
// 연동 백엔드:
//   • GET /api/reports/bank_ledger?date=YYYY-MM-DD&property_code=MOP&account_code=...
//     → 응답 구조: { ok, business_date, property_code, totals, rows }
// ============================================================================

import http from '@/services/http'

// ----------------------------------------------------------------------------
//  타입 정의
// ----------------------------------------------------------------------------

/** 단일 거래 레코드 */
export type BankLedgerRow = {
  /** 입출 방향: IN=입금, OUT=출금 */
  direction: 'IN' | 'OUT'
  /** 거래 금액 (문자열로 반환됨) */
  amount: string
  /** 거래 후 잔액 (선택적) */
  balance_after?: string
  /** 비고 / 메모 */
  note?: string
  /** 지점명 (선택적) */
  branch?: string
  /** 거래 시각 (YYYY-MM-DD HH:mm:ss) */
  txn_time?: string
}

/** 전체 리포트 응답 구조 */
export type BankLedgerReport = {
  ok: boolean
  business_date: string
  property_code: string
  account_code: string
  version_no: number | null
  totals: {
    /** 총 입금액 */
    in: number
    /** 총 출금액 */
    out: number
    /** 순이익(입금-출금) */
    net: number
  }
  /** 마지막 잔액 (nullable) */
  balance_after?: number | null
  /** 개별 거래 목록 */
  rows: BankLedgerRow[]
}

// ----------------------------------------------------------------------------
//  API 호출
// ----------------------------------------------------------------------------

/**
 * 은행 입출금 리포트 조회
 * @param params - { date, property_code, account_code }
 * @returns BankLedgerReport
 */
export async function getBankLedgerReport(params: {
  date: string
  property_code?: string
  account_code: string
}) {
  // ✅ 기본값 보정: property_code 누락 방지
  const query = {
    property_code:
      params.property_code ||
      localStorage.getItem('property_code') ||
      import.meta.env.VITE_DEFAULT_PROPERTY_CODE ||
      'MOP',
    date: params.date,
    account_code: params.account_code,
  }

  return await http.get<BankLedgerReport>(
    `/reports/bank_ledger${http.qs(query)}`
  )
}

// ============================================================================
// End of File — src/services/bank.ts (v2.0 Final)
// ============================================================================
