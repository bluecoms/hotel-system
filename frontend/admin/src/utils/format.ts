export const fmtKRW = (n: number | undefined | null) =>
  new Intl.NumberFormat('ko-KR', { style: 'currency', currency: 'KRW', maximumFractionDigits: 0 })
    .format(Number(n ?? 0))

export const fmtDate = (s: string | Date) =>
  new Intl.DateTimeFormat('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit' })
    .format(typeof s === 'string' ? new Date(s) : s)
