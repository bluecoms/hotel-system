// src/services/bank.ts
import http from '@/services/http'

export type BankLedgerRow = {
  direction: 'IN' | 'OUT'
  amount: string
  balance_after?: string
  note?: string
  branch?: string
  txn_time?: string
}

export type BankLedgerReport = {
  ok: boolean
  business_date: string
  property_code: string
  account_code: string
  version_no: number | null
  totals: { in: number; out: number; net: number }
  balance_after?: number | null
  rows: BankLedgerRow[]
}

export async function getBankLedgerReport(params: {
  date: string
  property_code: string
  account_code: string
}) {
  return await http.get<BankLedgerReport>(
    `/reports/bank_ledger${http.qs(params)}`
  )
}
