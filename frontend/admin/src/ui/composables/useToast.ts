// ============================================================================
// File    : src/ui/composables/useToast.ts
// Version : 2.2.3 Final (2025-10-23 · HR 간소화 10차 Hotfix3 · Export Fix + 주석 보강)
// Purpose : Hotel Admin — 전역 공통 Toast 유틸 (HR/운영/리포트 통합)
// ----------------------------------------------------------------------------
// 목적:
//   • 전역 공용 Toast(알림) 기능 제공 (성공/실패/경고/정보)
//   • HR, 운영, 리포트 등 모든 모듈에서 동일한 호출 방식으로 사용
//   • ToastHost.vue 에서 queue 상태를 구독하여 실제 렌더링 수행
// ----------------------------------------------------------------------------
// 변경 요약
//   ✅ export interface ToastItem 추가 (ToastHost 타입 인식 오류 해결)
//   ✅ Vuetify 색상 일원화(success=primary, error=error, info=secondary)
//   ✅ 중복 메시지 억제 + 자동 dismiss (3초)
//   ✅ 간결 API (success/info/warning/error) 유지
//   ✅ Promise 래퍼 wrap(), fromError() 유지
// ----------------------------------------------------------------------------
// 사용 예시
//   import { useToast } from '@/ui/composables/useToast'
//   const toast = useToast()
//   toast.success('저장되었습니다.')
//   toast.error('오류가 발생했습니다.')
//   toast.wrap(apiCall(), '완료되었습니다.')
// ============================================================================
import { ref } from 'vue'
import type { Ref } from 'vue'
import { useI18n } from 'vue-i18n'

// ─────────────────────────────────────────────
// 타입 정의
// ─────────────────────────────────────────────

/** Toast 종류 정의 (색상/용도 일관화) */
export type ToastKind = 'info' | 'success' | 'error' | 'warning'

/** 전역 Toast 한 건의 데이터 구조 (ToastHost.vue에서 구독) */
export interface ToastItem {
  /** 내부 고유 ID (큐 관리용) */
  id: number
  /** Toast 종류 */
  kind: ToastKind
  /** 메시지 텍스트 */
  message: string
  /** 자동 닫힘 시간(ms) */
  timeout: number
  /** 접근성용 aria-live 속성 */
  ariaLive: 'polite' | 'assertive'
}

// ─────────────────────────────────────────────
// 전역 상태 및 기본값
// ─────────────────────────────────────────────

/** 전역 Toast 큐 (Composition API 전역 singleton) */
const queue: Ref<ToastItem[]> = ref([])
/** 고유 ID 시퀀스 */
let seq = 1
/** 중복 체크 유효시간(ms) */
const DEDUP_MS = 1500
/** 최근 표시된 메시지 기록 (Dedup 용도) */
const recent = new Map<string, number>()

/** 기본 timeout 값 (종류별) */
const DEFAULT_TIMEOUT: Record<ToastKind, number> = {
  info: 2500,
  success: 2200,
  warning: 3500,
  error: 4000,
}

// ─────────────────────────────────────────────
// i18n 안전 호출자 (vue-i18n 인스턴스 미초기화 시 안전 동작)
// ─────────────────────────────────────────────
let t = (k: string) => {
  try {
    const { t: tt } = useI18n()
    return typeof tt === 'function' ? (tt(k) as string) : k
  } catch {
    return k
  }
}

// ─────────────────────────────────────────────
// 중복 방지 로직
//   • 동일 메시지가 일정 시간 내 반복 표시되지 않도록 제어
// ─────────────────────────────────────────────
function shouldDedup(sig: string) {
  const now = Date.now()
  const last = recent.get(sig) ?? 0
  if (now - last < DEDUP_MS) return true
  recent.set(sig, now)
  return false
}

// ─────────────────────────────────────────────
// 큐 조작 함수
// ─────────────────────────────────────────────

/** ID로 특정 Toast 제거 */
function remove(id: number) {
  queue.value = queue.value.filter((q) => q.id !== id)
}

/** 전체 큐 초기화 */
function clear() {
  queue.value = []
}

// ─────────────────────────────────────────────
// 메시지 변환 및 현지화
// ─────────────────────────────────────────────

/**
 * toMsg()
 * - 다양한 오류 객체(fetch/axios/Error 등)를 문자열로 변환
 */
function toMsg(e: any): string {
  if (!e) return ''
  if (typeof e === 'string') return e
  if (e instanceof Error) return e.message || ''
  const msg = e?.response?.data?.message || e?.message || e?.detail || ''
  const status = e?.status || e?.response?.status
  if (status && msg) return `HTTP ${status} ${msg}`
  return msg || JSON.stringify(e)
}

/**
 * localize()
 * - 공통 에러 메시지를 한글화
 */
function localize(raw: string) {
  const s = String(raw ?? '').trim()
  if (/401/.test(s)) return '로그인이 필요합니다.'
  if (/403/.test(s)) return '권한이 없습니다.'
  if (/404/.test(s)) return '대상을 찾을 수 없습니다.'
  if (/5\d{2}/.test(s)) return '서버 오류가 발생했습니다.'
  return s
}

// ─────────────────────────────────────────────
// push() : 토스트 생성 / fromError() / wrap()
// ─────────────────────────────────────────────

/**
 * push()
 * - 새로운 Toast를 큐에 추가
 * - timeout 시간 경과 시 자동 제거
 */
function push(raw: string | any, kind: ToastKind = 'info', timeout?: number) {
  const msg = localize(typeof raw === 'string' ? raw : toMsg(raw))
  if (!msg) return
  if (shouldDedup(`${kind}:${msg}`)) return

  const id = seq++
  const item: ToastItem = {
    id,
    kind,
    message: msg,
    timeout: timeout ?? DEFAULT_TIMEOUT[kind],
    ariaLive: kind === 'error' ? 'assertive' : 'polite',
  }

  queue.value.push(item)

  // 지정 시간 후 자동 제거
  if (item.timeout > 0) {
    setTimeout(() => remove(id), item.timeout)
  }
  return id
}

/**
 * fromError()
 * - Error/Response 객체를 토스트로 출력
 */
function fromError(e: any) {
  const status = e?.status ?? e?.response?.status
  const msg = localize(toMsg(e))
  let kind: ToastKind = 'error'
  if (status === 401 || status === 403 || status === 409) kind = 'warning'
  return push(msg, kind)
}

/**
 * wrap()
 * - Promise 처리 시 자동 Toast 출력
 *   ex) await toast.wrap(apiCall(), '저장 완료')
 */
async function wrap<T>(p: Promise<T>, okMsg?: string) {
  try {
    const r = await p
    if (okMsg) push(okMsg, 'success')
    return r
  } catch (e) {
    fromError(e)
    throw e
  }
}

// ─────────────────────────────────────────────
// useToast() — 외부 노출 (Composition API)
//   • 어디서든 호출 가능
// ─────────────────────────────────────────────
export function useToast() {
  return {
    // 상태
    queue,

    // 조작
    remove,
    clear,

    // 기본형 (shortcut)
    info:    (m: any, t?: number) => push(m, 'info', t),
    success: (m: any, t?: number) => push(m, 'success', t),
    warning: (m: any, t?: number) => push(m, 'warning', t),
    error:   (m: any, t?: number) => push(m, 'error', t),

    // 고급형
    fromError,
    wrap,
  }
}
