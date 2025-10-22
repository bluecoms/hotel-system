// src/ui/composables/useToast.ts
import { ref } from 'vue'
import type { Ref } from 'vue'
import { useI18n } from 'vue-i18n' // ✅ 정식 import 사용 (require 제거)

// 안전한 i18n 래퍼 (vue-i18n 미초기화 시도 방지)
let t = (k: string, vars?: Record<string, any>) => {
  try {
    const { t: tt } = useI18n()
    return typeof tt === 'function' ? (tt(k, vars ?? {}) as string) : k
  } catch {
    return k
  }
}

export type ToastKind = 'info' | 'success' | 'error' | 'warning'
export interface ToastItem {
  id: number
  kind: ToastKind
  message: string
  timeout?: number
  sticky?: boolean
  ariaLive?: 'polite' | 'assertive'
}

const queue: Ref<ToastItem[]> = ref([])
let seq = 1

// 기본 타임아웃(ms)
const DEFAULT_TIMEOUT: Record<ToastKind, number> = {
  info: 2500,
  success: 2200,
  warning: 3500,
  error: 4000,
}

// ──────────────────────────────
// 1) 에러 → 문자열 변환
// ──────────────────────────────
function toMessage(e: any): string {
  if (!e) return ''
  if (typeof e === 'string') return e
  if (e instanceof Error && e.message) return e.message

  const status = e.status ?? e.response?.status
  const data = e.response?.data ?? e.data
  const detail = data?.detail ?? e.detail
  const msg =
    (typeof detail === 'string' && detail) ||
    detail?.message ||
    data?.message ||
    e.message ||
    e.error ||
    e.reason

  const text = String(msg ?? '').trim()
  if (status && text && !/^HTTP\s+\d+/.test(text)) {
    return `HTTP ${status} ${text}`
  }
  return text || JSON.stringify(e)
}

// ──────────────────────────────
// 2) 메시지 현지화(i18n)
// ──────────────────────────────
function localize(raw: string): string {
  const s = String(raw ?? '').trim()
  if (!s) return ''

  if (/^HTTP 401\b/.test(s)) return t('msg.unauthorized')
  if (/^HTTP 403\b/.test(s)) return t('msg.forbidden')
  if (/^HTTP 404\b/.test(s)) return t('state.notFound')
  if (/^HTTP 409\b/.test(s)) return t('msg.conflict')
  if (/^HTTP 5\d{2}\b/.test(s)) return t('msg.serverError')

  const exact: Record<string, string> = {
    'Not Found': t('state.notFound'),
    'No data': t('state.empty'),
    'Unauthorized': t('auth.needLogin'),
    'Forbidden': t('auth.noPermission'),
    'Timeout': t('msg.timeout'),
    'Network Error': t('msg.networkError'),
    'Validation error.': t('msg.validation'),
    'Method Not Allowed': '허용되지 않은 요청 방식입니다.',
    'Conflict': t('msg.conflict'),
    'Service Unavailable': '일시적으로 사용할 수 없습니다.',
    'Internal Server Error': t('msg.serverError'),
  }
  if (exact[s]) return exact[s]

  const rules: Array<[RegExp, string]> = [
    [/validation/i, t('msg.validation')],
    [/duplicate|unique/i, '이미 존재하는 값입니다.'],
    [/(closed day|closed.*date)/i, t('msg.closedDayBlocked')],
    [/file.*required/i, t('msg.fileRequired')],
    [/size.*too.*(large|big)/i, t('msg.fileTooLarge')],
    [/(csv|xlsx|excel)/i, t('msg.fileType')],
    [/network/i, t('msg.networkError')],
    [/timeout/i, t('msg.timeout')],
    [/not\s*found/i, t('state.notFound')],
  ]

  for (const [re, translated] of rules) {
    if (re.test(s)) return translated
  }
  return s
}

// ──────────────────────────────
// 3) 중복 토스트 방지
// ──────────────────────────────
const recent = new Map<string, number>()
const DEDUP_MS = 1500

function shouldDedup(message: string) {
  const now = Date.now()
  const last = recent.get(message) ?? 0
  if (now - last < DEDUP_MS) return true
  recent.set(message, now)
  return false
}

function remove(id: number) {
  queue.value = queue.value.filter(t => t.id !== id)
}

function push(raw: string | any, kind: ToastKind = 'info', timeout?: number, sticky = false) {
  const message = localize(typeof raw === 'string' ? raw : toMessage(raw))
  if (!message) return
  if (!sticky && shouldDedup(message)) return

  const id = seq++
  const item: ToastItem = {
    id, kind, message,
    timeout: sticky ? 0 : (timeout ?? DEFAULT_TIMEOUT[kind]),
    sticky,
    ariaLive: kind === 'error' ? 'assertive' : 'polite',
  }
  queue.value.push(item)

  if (item.timeout && item.timeout > 0) {
    window.setTimeout(() => remove(id), item.timeout)
  }
  return id
}

function pushOnce(raw: string | any, kind: ToastKind = 'info', key?: string) {
  const message = localize(typeof raw === 'string' ? raw : toMessage(raw))
  if (!message) return
  const sig = key ? `${kind}:${key}` : `${kind}:${message}`
  if (shouldDedup(sig)) return
  return push(message, kind)
}

function shift() {
  const first = queue.value[0]
  if (first) remove(first.id)
}

// ──────────────────────────────
// 4) 에러 전용/Promise 래퍼
// ──────────────────────────────
function fromError(e: any) {
  const status = e?.status ?? e?.response?.status
  const msg = localize(toMessage(e))
  let kind: ToastKind = 'error'
  if (status === 409 || status === 401 || status === 403) kind = 'warning'
  return push(msg, kind)
}

async function wrap<T>(p: Promise<T>, okMsg?: string) {
  try {
    const res = await p
    if (okMsg) push(okMsg, 'success')
    return res
  } catch (e: any) {
    fromError(e)
    throw e
  }
}

// ──────────────────────────────
// 5) 외부 노출
// ──────────────────────────────
export function useToast() {
  return {
    queue,
    push,
    pushOnce,
    shift,
    remove,
    clear: () => (queue.value = []),
    info:    (m: string | any, t?: number) => push(m, 'info', t),
    success: (m: string | any, t?: number) => push(m, 'success', t),
    error:   (m: string | any, t?: number) => push(m, 'error', t),
    warning: (m: string | any, t?: number) => push(m, 'warning', t),
    fromError,
    wrap,
  }
}
