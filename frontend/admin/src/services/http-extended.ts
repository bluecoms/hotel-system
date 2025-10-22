// ============================================================================
// File      : src/services/http-extended.ts
// Version   : 2025.10-23 Safe Add-on (Abort/Retry/Timeout/Zod Optional)
// Purpose   : 기존 fetch 래퍼(http.ts)를 "수정 없이" 감싸서 안정성/검증 기능 확장
// ----------------------------------------------------------------------------
// 특징
//   ✅ 기존 http.ts 전혀 수정하지 않음 (리스크 0, 완전 호환)
//   ✅ Abort/Timeout 지원: 요청 취소 및 타임아웃 강제
//   ✅ Retry(지수 백오프): 네트워크/일시 오류 자동 재시도
//   ✅ Zod(Optional): schema.safeParse 지원(미사용시 의존성 필요 없음)
//   ✅ property_code/토큰/401 처리 등은 http.ts가 그대로 담당
// ----------------------------------------------------------------------------
// 사용 예
//   import { httpEx } from '@/services/http-extended'
//
//   // 1) 기본 JSON 호출 (+타임아웃/재시도 기본값)
//   const items = await httpEx.getJSON('/roles/access')
//
//   // 2) Zod 검증(선택): schema를 전달하면 응답 타입 보증
//   import { z } from 'zod'
//   const Role = z.object({ route_name: z.string(), access_scope: z.array(z.string()) })
//   const rows = await httpEx.getJSON('/roles/access', { schema: z.array(Role) })
//
//   // 3) 폼 업로드(Abort/Timeout/Retry 가능)
//   const fd = new FormData(); fd.append('file', file)
//   await httpEx.uploadForm('/upload/rooms_status', fd, { timeoutMs: 20000 })
//
//   // 4) Blob 다운로드(재시도/타임아웃)
//   const blob = await httpEx.getBlob('/docs/file/123/download', { timeoutMs: 15000 })
// ----------------------------------------------------------------------------
// 권장 정책
//   • 기존 화면/서비스 코드는 그대로 두고,
//     "신규/리팩토링 대상"에서만 httpEx를 import하여 점진 적용하세요.
// ============================================================================

import http from '@/services/http'

// ─────────────────────────────────────────────
// 옵션/타입
// ─────────────────────────────────────────────

type ZodLike<T> = {
  safeParse?: (data: unknown) => { success: boolean; data?: T; error?: unknown }
}

export type RetryOptions = {
  retries?: number           // 총 재시도 횟수 (기본 2 → 총 3번 시도)
  factor?: number            // 지수 승수 (기본 2)
  minDelayMs?: number        // 최초 대기 (기본 300ms)
  maxDelayMs?: number        // 최대 대기 (기본 3000ms)
  retryOnStatus?: number[]   // 응답 상태 코드 재시도 대상 (기본: [429,502,503,504])
}

export type HttpExOptions<T = any> = {
  signal?: AbortSignal       // 외부 AbortSignal
  timeoutMs?: number         // 타임아웃 (ms). 없으면 무제한
  retry?: RetryOptions       // 재시도 정책
  schema?: ZodLike<T>        // zod 등 safeParse 지원 객체(선택)
  init?: RequestInit         // http.*의 init 전달(헤더/X-Silent-Toast 등)
}

// 기본 Retry 정책
const DEFAULT_RETRY: Required<RetryOptions> = {
  retries: 2,
  factor: 2,
  minDelayMs: 300,
  maxDelayMs: 3000,
  retryOnStatus: [429, 502, 503, 504],
}

// 지수 백오프 계산
function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms))
}

function nextDelay(attempt: number, opt: Required<RetryOptions>) {
  const delay = Math.min(opt.minDelayMs * Math.pow(opt.factor, attempt), opt.maxDelayMs)
  return Math.floor(delay)
}

// Abort + Timeout 통합 컨트롤러
function buildAbortSignal(timeoutMs?: number, external?: AbortSignal) {
  if (!timeoutMs && !external) return { signal: undefined as AbortSignal | undefined, cleanup: () => {} }

  const controller = new AbortController()
  const timers: number[] = []

  // 외부 시그널과 연결
  if (external) {
    if (external.aborted) controller.abort()
    else external.addEventListener('abort', () => controller.abort(), { once: true })
  }

  // 타임아웃
  if (timeoutMs && timeoutMs > 0) {
    const t = window.setTimeout(() => controller.abort(), timeoutMs)
    timers.push(t)
  }

  function cleanup() {
    timers.forEach((t) => clearTimeout(t))
  }

  return { signal: controller.signal, cleanup }
}

// Zod-like safeParse 적용(선택)
function maybeValidate<T>(data: any, schema?: ZodLike<T>): T {
  if (!schema?.safeParse) return data as T
  const parsed = schema.safeParse(data)
  if (parsed?.success) return parsed.data as T
  const err = new Error('응답 스키마 검증 실패(Zod safeParse).')
  ;(err as any).cause = parsed?.error
  throw err
}

// ─────────────────────────────────────────────
// 공통 재시도 래퍼 — http.* 호출을 감쌈
// (http.ts 내부 fetch를 건드리지 않기 위해 try/catch+백오프로 구현)
// ─────────────────────────────────────────────

async function withRetry<T>(
  fn: (init?: RequestInit) => Promise<T>,
  options?: HttpExOptions<T>
): Promise<T> {
  const retry = { ...DEFAULT_RETRY, ...(options?.retry || {}) }
  let attempt = 0
  let lastErr: any

  while (true) {
    try {
      // init 전달 시 signal 포함
      const { signal, cleanup } = buildAbortSignal(options?.timeoutMs, options?.signal)
      const mergedInit: RequestInit | undefined = options?.init || {}
      ;(mergedInit as any).signal = signal

      try {
        return await fn(mergedInit)
      } finally {
        cleanup()
      }
    } catch (e: any) {
      lastErr = e
      const status = e?.status ?? 0
      const isNetwork = status === 0 // fetch 예외
      const shouldRetry = isNetwork || retry.retryOnStatus.includes(status)

      if (!shouldRetry || attempt >= retry.retries) {
        throw lastErr
      }

      const delay = nextDelay(attempt, retry)
      await sleep(delay)
      attempt += 1
    }
  }
}

// ─────────────────────────────────────────────
// 메서드 구현 — http.*를 감싸되, options로 제어
//  * http.ts가 JSON/text 구분/401/토스트/헤더/쿼리(property_code) 모두 처리
//  * 여기선 타임아웃/재시도/검증만 추가
// ─────────────────────────────────────────────

async function getJSON<T = any>(path: string, options?: HttpExOptions<T>): Promise<T> {
  const data = await withRetry<T>((init) => http.get<T>(path, init), options)
  return maybeValidate<T>(data, options?.schema)
}

async function postJSON<T = any>(path: string, body?: any, options?: HttpExOptions<T>): Promise<T> {
  const data = await withRetry<T>((init) => http.post<T>(path, body, init), options)
  return maybeValidate<T>(data, options?.schema)
}

async function putJSON<T = any>(path: string, body?: any, options?: HttpExOptions<T>): Promise<T> {
  const data = await withRetry<T>((init) => http.put<T>(path, body, init), options)
  return maybeValidate<T>(data, options?.schema)
}

async function patchJSON<T = any>(path: string, body?: any, options?: HttpExOptions<T>): Promise<T> {
  const data = await withRetry<T>((init) => http.patch<T>(path, body, init), options)
  return maybeValidate<T>(data, options?.schema)
}

async function deleteJSON<T = any>(path: string, options?: HttpExOptions<T>): Promise<T> {
  const data = await withRetry<T>((init) => http.delete<T>(path, init), options)
  return maybeValidate<T>(data, options?.schema)
}

async function uploadForm<T = any>(path: string, form: FormData, options?: HttpExOptions<T>): Promise<T> {
  // http.ts 는 FormData면 자동으로 Content-Type 미설정(브라우저가 boundary 세팅)
  const data = await withRetry<T>((init) => http.post<T>(path, form, init), options)
  return maybeValidate<T>(data, options?.schema)
}

async function getBlob(path: string, options?: HttpExOptions<Blob>): Promise<Blob> {
  return await withRetry<Blob>((init) => http.getBlob(path, init), options)
}

// 쿼리스트링 유틸 재노출(편의)
function qs(params?: Record<string, any>) {
  return http.qs(params)
}

// 외부 노출 객체
export const httpEx = {
  getJSON,
  postJSON,
  putJSON,
  patchJSON,
  deleteJSON,
  uploadForm,
  getBlob,
  qs,
}
