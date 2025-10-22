import http from '@/services/http'

/** ─────────────────────────────
 * 1) 일자 단위 마감 상태 조회/변경
 *  (기존 /closing/day 유지)
 * ───────────────────────────── */
export async function getClosingDay(params: { date: string; property_code: string }) {
  return await http.get(`/closing/day${http.qs(params)}`)
}

export async function setClosingDayStatus(body: { date: string; status: 'OPEN'|'CLOSED'; property_code: string }) {
  // ✅ 백엔드가 JSON Body 또는 Query를 받도록 되어있음.
  //   기존 FormData → JSON으로 변경
  return await http.put('closing/day', body)
}

/** ─────────────────────────────
 * 2) 월 단위 캘린더 조회 (/api/closing/calendar)
 *  BE가 from/to(days[] 범위) 계산 — FE는 그대로 표시만
 * ───────────────────────────── */
export type ClosingDay = {
  date: string
  uploaded: string[]
  counts: Record<string, number>
  done: number
  total: number
  complete: boolean
  status: 'OPEN' | 'CLOSED'
}

export type ClosingCalendarResp = {
  ok: boolean
  property_code: string
  month: string
  timezone: string
  from: string
  to: string
  required: string[]
  days: ClosingDay[]
}

export async function getClosingCalendar(params: { month: string; property_code: string }) {
  return await http.get<ClosingCalendarResp>(`/closing/calendar${http.qs(params)}`)
}
