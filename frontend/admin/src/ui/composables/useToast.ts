// ============================================================================
// File    : src/ui/composables/useToast.ts
// Version : 2025.11-04 · v2.1 (전역 토스트 큐 · i18n 안전 래퍼 · 중복억제 · Promise 헬퍼)
// Purpose : 앱 전역에서 공통으로 사용하는 토스트(Notification) 구성요소의 상태/함수 제공
// ----------------------------------------------------------------------------
// 설계 목표
//   1) 전역 단일 큐(queue) 기반으로 토스트 여러 개를 순차/병렬 표시 가능
//   2) vue-i18n 초기화 전에도 안전하게 동작 (i18n의 존재 유무를 런타임 안전 처리)
//   3) 서버/네트워크 오류를 사용자가 이해하기 쉬운 문구로 현지화(localize)
//   4) 짧은 시간에 반복되는 동일 토스트는 자동 중복 억제(De-dup)
//   5) 성공/실패를 Promise로 감싸는 래퍼(useToast().wrap) 제공 → 호출처 간소화
//   6) 접근성(aria-live) 수준을 토스트 종류별로 합리적인 기본값 제공
// ----------------------------------------------------------------------------
// 사용 방법(예시)
//   import { useToast } from '@/ui/composables/useToast'
//   const toast = useToast()
//   toast.success('저장되었습니다.')
//   toast.fromError(err)  // 서버 오류 객체를 사람이 읽을 수 있는 메시지로 변환 후 출력
//   await toast.wrap(apiCall(), '완료되었습니다.')
// ----------------------------------------------------------------------------
// 화면 연결(전역 스낵바)
//   App.vue 등 전역 레이아웃에서 queue를 구독해 노출하면 됨:
//     const { queue, remove } = useToast()
//     <v-snackbar
//       v-for="n in queue"
//       :key="n.id"
//       v-model="visibleMap[n.id]"        // 혹은 리스트 렌더로 자동 보이게 처리
//       :timeout="n.timeout"
//       :color="n.kind === 'error' ? 'error' : (n.kind === 'warning' ? 'warning' : (n.kind === 'success' ? 'success' : 'primary'))"
//       location="top right"
//       :aria-live="n.ariaLive"
//       @timeout="remove(n.id)"
//     >{{ n.message }}</v-snackbar>
// ============================================================================
import { ref } from 'vue'
import type { Ref } from 'vue'
import { useI18n } from 'vue-i18n'  // ✅ 정식 import 사용 (require 지양)

// ============================================================================
// i18n 안전 래퍼
// - 컴포저블이 라우트 전환 등 시점에 import 될 수 있으므로,
//   vue-i18n 인스턴스가 아직 없을 수도 있다. try-catch로 보호한다.
// ============================================================================
let t = (k: string, vars?: Record<string, any>) => {
  try {
    const { t: tt } = useI18n()
    // vue-i18n 인스턴스가 없거나 훅 사용 불가한 시점이면 실패 → 원문 키 반환
    return typeof tt === 'function' ? (tt(k, vars ?? {}) as string) : k
  } catch {
    return k
  }
}

// ============================================================================
// 타입 선언부
// ============================================================================
export type ToastKind = 'info' | 'success' | 'error' | 'warning'

/** 전역 토스트 1건의 데이터 구조 */
export interface ToastItem {
  /** 내부 식별자 (큐에서 제거에 사용) */
  id: number
  /** 토스트 종류 (색상/의미/aria-live 기본값에 영향) */
  kind: ToastKind
  /** 사용자에게 노출할 메시지 (현지화 결과 문자열) */
  message: string
  /** 자동 종료 타임아웃(ms). 0 또는 undefined면 개발자가 직접 제거 */
  timeout?: number
  /** sticky=true면 자동 종료하지 않음(사용자 확인 필요) */
  sticky?: boolean
  /** 스크린리더 읽기 우선순위: error → 'assertive', 그 외 → 'polite' */
  ariaLive?: 'polite' | 'assertive'
}

// ============================================================================
// 전역 상태: 토스트 큐 및 식별자 시퀀스
// - queue는 앱 전체에서 하나만 존재. 어떤 화면에서든 useToast()로 접근.
// ============================================================================
const queue: Ref<ToastItem[]> = ref([])
let seq = 1

// ============================================================================
// 기본 타임아웃(ms)
// - UX 고려: success는 짧게, warning/error는 조금 더 길게
// ============================================================================
const DEFAULT_TIMEOUT: Record<ToastKind, number> = {
  info:    2500,
  success: 2200,
  warning: 3500,
  error:   4000,
}

// ============================================================================
// 1) 에러 객체를 사람이 읽을 수 있는 문자열로 변환
// - axios/fetch 응답, Error 인스턴스, 커스텀 에러 모두 안전 처리
// ============================================================================
function toMessage(e: any): string {
  if (!e) return ''
  if (typeof e === 'string') return e
  if (e instanceof Error && e.message) return e.message

  // HTTP 상태 코드 및 서버 응답 본문 구조를 최대한 유연하게 해석
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
  // 상태 코드 + 메시지를 합쳐 사용자가 상황을 이해하게 돕는다.
  if (status && text && !/^HTTP\s+\d+/.test(text)) {
    return `HTTP ${status} ${text}`
  }
  // 정보가 거의 없을 때는 전체 객체를 stringify (마지막 보루)
  return text || JSON.stringify(e)
}

// ============================================================================
// 2) 메시지 현지화(i18n) + 범용 문자열 매핑
// - 공통 에러/상태 문구를 한국어로 일관되게 관리
// - 정규식 판별 및 정확 매핑 병행
// ============================================================================
function localize(raw: string): string {
  const s = String(raw ?? '').trim()
  if (!s) return ''

  // 대표적인 HTTP 코드 → 약칭 문구 매핑
  if (/^HTTP 401\b/.test(s)) return t('auth.needLogin')    || '로그인이 필요합니다.'
  if (/^HTTP 403\b/.test(s)) return t('auth.noPermission') || '권한이 없습니다.'
  if (/^HTTP 404\b/.test(s)) return t('state.notFound')    || '대상을 찾을 수 없습니다.'
  if (/^HTTP 409\b/.test(s)) return t('msg.conflict')      || '충돌이 발생했습니다.'
  if (/^HTTP 5\d{2}\b/.test(s)) return t('msg.serverError')|| '서버 오류가 발생했습니다.'

  // 정확 매핑 테이블
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

  // 정규식 매핑 규칙(부분 문자열에 대응)
  const rules: Array<[RegExp, string]> = [
    [/validation/i, t('msg.validation') || '입력값이 올바르지 않습니다.'],
    [/duplicate|unique/i, '이미 존재하는 값입니다.'],
    [/(closed day|closed.*date)/i, t('msg.closedDayBlocked') || '마감일에는 작업할 수 없습니다.'],
    [/file.*required/i, t('msg.fileRequired') || '파일이 필요합니다.'],
    [/size.*too.*(large|big)/i, t('msg.fileTooLarge') || '파일 용량이 너무 큽니다.'],
    [/(csv|xlsx|excel)/i, t('msg.fileType') || '파일 형식이 올바르지 않습니다.'],
    [/network/i, t('msg.networkError') || '네트워크 오류입니다.'],
    [/timeout/i, t('msg.timeout') || '요청이 시간 초과되었습니다.'],
    [/not\s*found/i, t('state.notFound') || '대상을 찾을 수 없습니다.'],
  ]

  for (const [re, translated] of rules) {
    if (re.test(s)) return translated
  }
  // 그 외는 원문 그대로
  return s
}

// ============================================================================
// 3) 중복 토스트 방지 (Dedup)
// - DEDUP_MS 내에 동일 메시지가 다시 들어오면 무시
// - pushOnce(key) 는 메시지 대신 키로 중복 제어
// ============================================================================
const recent = new Map<string, number>()
const DEDUP_MS = 1500

function shouldDedup(signature: string) {
  const now = Date.now()
  const last = recent.get(signature) ?? 0
  if (now - last < DEDUP_MS) return true
  recent.set(signature, now)
  return false
}

// ============================================================================
// 내부 유틸: 큐에서 id로 제거
// ============================================================================
function remove(id: number) {
  queue.value = queue.value.filter(t => t.id !== id)
}

// ============================================================================
// 4) push 계열: 메시지를 큐에 적재
// - sticky=true 이면 자동 타임아웃 없음 (사용자 확인 필요)
// - timeout 지정 없을 경우 종류별 DEFAULT_TIMEOUT 사용
// ============================================================================
function push(
  raw: string | any,
  kind: ToastKind = 'info',
  timeout?: number,
  sticky = false
) {
  // 메시지 변환(에러 객체 등 → string) + 현지화
  const message = localize(typeof raw === 'string' ? raw : toMessage(raw))
  if (!message) return

  // sticky가 아니면 중복 억제
  if (!sticky && shouldDedup(message)) return

  const id = seq++
  const item: ToastItem = {
    id,
    kind,
    message,
    timeout: sticky ? 0 : (timeout ?? DEFAULT_TIMEOUT[kind]),
    sticky,
    ariaLive: kind === 'error' ? 'assertive' : 'polite',
  }
  queue.value.push(item)

  // 자동 제거 타이머
  if (item.timeout && item.timeout > 0) {
    window.setTimeout(() => remove(id), item.timeout)
  }
  return id
}

// 동일 signature(메시지 or key) 기준으로 1회만 표시
function pushOnce(raw: string | any, kind: ToastKind = 'info', key?: string) {
  const msg = localize(typeof raw === 'string' ? raw : toMessage(raw))
  if (!msg) return
  const sig = key ? `${kind}:${key}` : `${kind}:${msg}`
  if (shouldDedup(sig)) return
  return push(msg, kind)
}

// 큐의 첫 번째 항목 즉시 제거
function shift() {
  const first = queue.value[0]
  if (first) remove(first.id)
}

// ============================================================================
// 5) 에러/Promise 래퍼
// - fromError: 에러 객체 → 현지화 후 토스트 출력
// - wrap: Promise를 감싸서 성공/실패 토스트를 자동 처리
// ============================================================================
function fromError(e: any) {
  const status = e?.status ?? e?.response?.status
  const msg = localize(toMessage(e))
  let kind: ToastKind = 'error'
  // 권한/충돌류는 error가 아닌 warning 으로 톤다운
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

// ============================================================================
// 6) 외부 노출: useToast()
// - 어디서든 import 후 공통 토스트 사용
// - queue는 전역 스낵바 렌더링에 바인딩하여 사용
// ============================================================================
export function useToast() {
  return {
    // 상태
    queue,

    // 기본 조작
    push,
    pushOnce,
    shift,
    remove,
    clear: () => (queue.value = []),

    // 종류별 숏컷
    info:    (m: string | any, t?: number) => push(m, 'info', t),
    success: (m: string | any, t?: number) => push(m, 'success', t),
    warning: (m: string | any, t?: number) => push(m, 'warning', t),
    error:   (m: string | any, t?: number) => push(m, 'error', t),

    // 고급
    fromError,
    wrap,
  }
}
