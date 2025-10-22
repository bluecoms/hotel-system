// ============================================================================
// File      : src/services/http.ts
// Version   : 2025.10-24 Final Stable (Property Header Unification · SSOT 규격)
// Purpose   : Hotel Admin — Fetch 기반 HTTP 클라이언트 (axios 완전 금지)
// ----------------------------------------------------------------------------
// 목적
//   • 모든 네트워크 통신(fetch)을 단일 모듈로 통합 관리
//   • 인증: X-Internal-Token 헤더 기반 (localStorage + .env)
//   • 지점: ✅ property_code 전달을 “헤더 단일화(X-Property-Code)”로 변경
//            (이 파일에서는 절대 URL 쿼리 ?property_code=… 를 자동 첨부하지 않는다)
//   • DeptAccess / RoleAccess / Closing / Reports 등과 완전 호환
// ----------------------------------------------------------------------------
// 특징
//   ✅ buildUrl()       : 상대/절대 경로 정규화
//   ✅ makeHeaders()    : 토큰/언어/디버그/프로퍼티 코드 헤더 자동 세팅
//   ✅ handleUnauthorized(): 401 시 세션 초기화(루프 방지)
//   ✅ Silent Toast 모드 : X-Silent-Toast 헤더로 에러 토스트 억제
//   ✅ getBlob()        : 파일 다운로드 전용 유틸리티
// ----------------------------------------------------------------------------
// 변경 이력
//   - v2025-10-17 : fetch 구조 안정화 / i18n 메시지 적용
//   - v2025-10-18 : handleUnauthorized() 루프 방지
//   - v2025-10-19 : (구) property_code 자동 반영(쿼리) 도입
//   - v2025-10-23 : DeptAccess / DebugRole 완전 통합
//   - v2025-10-24 : ✅ property_code “헤더 단일화” (쿼리 자동 첨부 로직 전면 제거)
//                    → 모든 API는 X-Property-Code 헤더만으로 필터링
// ============================================================================

import { useToast } from '@/ui/composables/useToast'
import { t } from '@/i18n'
import { usePropertyStore } from '@/stores/property'

const { fromError } = useToast()

// ─────────────────────────────────────────────
// 환경 변수 / 인증 토큰
// ─────────────────────────────────────────────
const KEY = 'ADMIN_TOKEN'
const LEGACY_KEY = 'internalToken'

let API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api').trim()
if (!/^https?:\/\//i.test(API_BASE)) API_BASE = '/api'

const ENV_INTERNAL_TOKEN = (import.meta.env.VITE_INTERNAL_TOKEN || '').trim()
let ADMIN_TOKEN = (import.meta.env.VITE_ADMIN_TOKEN || ENV_INTERNAL_TOKEN || '').trim()
let DEBUG_ROLE: string | null =
  localStorage.getItem('debugRole') ||
  (import.meta.env.VITE_DEBUG_ROLE || '').trim().toUpperCase() ||
  null

/** 토큰 getter (우선순위: 메모리 → localStorage 2키 호환) */
export const getToken = () =>
  ADMIN_TOKEN ||
  localStorage.getItem(KEY) ||
  localStorage.getItem(LEGACY_KEY) ||
  ''

/** 토큰 setter (메모리 + localStorage 2키 동기화) */
export const setToken = (v: string | null) => {
  ADMIN_TOKEN = v || ''
  if (v) {
    localStorage.setItem(KEY, v)
    localStorage.setItem(LEGACY_KEY, v)
  } else {
    localStorage.removeItem(KEY)
    localStorage.removeItem(LEGACY_KEY)
  }
}

/** 디버그용 역할 설정 (X-Debug-Role) */
export const setDebugRole = (r: string | null) => {
  DEBUG_ROLE = r
  if (r) localStorage.setItem('debugRole', r)
  else localStorage.removeItem('debugRole')
}

// ─────────────────────────────────────────────
// 내부 유틸
// ─────────────────────────────────────────────

/** URL 정규화 (중복 슬래시 제거, /api 베이스 적용) */
function buildUrl(p: string) {
  if (/^https?:\/\//i.test(p)) return p
  if (p.startsWith('/')) p = p.slice(1)
  const base = API_BASE.replace(/\/+$/, '')
  return `${base}/${p}`.replace(/([^:]\/)\/+/g, '$1')
}

/** 기본 헤더 구성 (토큰 / 언어 / 디버그 / 지점코드) */
function makeHeaders(init?: HeadersInit): Headers {
  const h = new Headers(init || {})

  // 인증 토큰
  const token = getToken()
  if (token) h.set('X-Internal-Token', token)

  // 디버그 역할
  const role = localStorage.getItem('debugRole') || DEBUG_ROLE
  if (role) h.set('X-Debug-Role', role)

  // 공통 헤더
  if (!h.has('Accept')) h.set('Accept', 'application/json')
  if (!h.has('Accept-Language')) h.set('Accept-Language', 'ko-KR')

  // ✅ 지점 코드: “헤더로만” 전달 (쿼리 금지)
  const store = usePropertyStore()
  const property = localStorage.getItem('property_code') || store.get()
  if (property) h.set('X-Property-Code', property)

  return h
}

/** FastAPI 표준 에러(detail)에서 메시지 추출 */
function extractErrorMessage(detail: any): string | undefined {
  if (!detail) return
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const f = detail[0]
    if (f?.msg) return String(f.msg)
  }
  if (typeof detail === 'object') {
    if (detail.detail) return String(detail.detail)
    if (detail.message) return String(detail.message)
  }
  return undefined
}

/** 401 처리 — 루프 방지(세션/스토리지 초기화만, 리다이렉트는 라우터가 담당) */
function handleUnauthorized() {
  setToken(null)
  try {
    sessionStorage.clear()
  } catch {}
}

/** Silent Toast 모드 여부 (요청 헤더에 X-Silent-Toast: 1 일 때) */
function isSilent(init?: RequestInit) {
  const h = new Headers(init?.headers || {})
  return h.get('X-Silent-Toast') === '1'
}

// ─────────────────────────────────────────────
// fetch wrapper
//   • buildUrl → makeHeaders → fetch
//   • ✅ property_code 쿼리 자동 첨부 로직 제거 (헤더 단일화)
// ─────────────────────────────────────────────
async function request<T>(
  method: string,
  path: string,
  body?: any,
  init?: RequestInit
): Promise<T> {
  const url = buildUrl(path)
  const headers = makeHeaders(init?.headers)
  const opts: RequestInit = { method, headers, credentials: 'omit', ...init }

  // Body 직렬화 처리
  if (body instanceof FormData) {
    opts.body = body
  } else if (body !== undefined) {
    if (!headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
    opts.body = JSON.stringify(body)
  }

  // 실제 호출
  let res: Response
  try {
    res = await fetch(url, opts)
  } catch {
    const err: any = new Error(t('msg.networkError'))
    err.status = 0
    if (!isSilent(init)) fromError(err)
    throw err
  }

  // 401 공통 처리
  if (res.status === 401) {
    handleUnauthorized()
    const err: any = new Error(t('msg.unauthorized'))
    err.status = 401
    if (!isSilent(init)) fromError(err)
    throw err
  }

  // 비정상 응답 처리
  if (!res.ok) {
    let msg = ''
    try {
      const json = await res.json()
      msg = extractErrorMessage(json) || ''
    } catch {}
    const err: any = new Error(msg || t('msg.serverError'))
    err.status = res.status
    if (!isSilent(init)) fromError(err)
    throw err
  }

  // 204(No Content)
  if (res.status === 204) return undefined as unknown as T

  // 응답 파싱
  const ct = res.headers.get('content-type') || ''
  return ct.includes('application/json')
    ? ((await res.json()) as T)
    : ((await res.text()) as any)
}

// ─────────────────────────────────────────────
// 다운로드 전용 (Blob)
// ─────────────────────────────────────────────
async function getBlob(path: string, init?: RequestInit): Promise<Blob> {
  const url = buildUrl(path)
  const headers = makeHeaders(init?.headers)
  const res = await fetch(url, { ...init, headers })
  if (!res.ok) throw new Error(`Download failed: ${res.status}`)
  return await res.blob()
}

// ─────────────────────────────────────────────
// 쿼리 스트링 유틸 (선택적 사용 — property_code 자동 부착은 여기서도 금지)
// ─────────────────────────────────────────────
function qs(params?: Record<string, any>) {
  if (!params) return ''
  const s = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null) continue
    s.append(k, String(v))
  }
  const q = s.toString()
  return q ? `?${q}` : ''
}

// ─────────────────────────────────────────────
// Export 객체
// ─────────────────────────────────────────────
const http = {
  get:    <T>(p: string, init?: RequestInit)          => request<T>('GET',    p, undefined, init),
  post:   <T>(p: string, b?: any, init?: RequestInit) => request<T>('POST',   p, b, init),
  put:    <T>(p: string, b?: any, init?: RequestInit) => request<T>('PUT',    p, b, init),
  patch:  <T>(p: string, b?: any, init?: RequestInit) => request<T>('PATCH',  p, b, init),
  delete: <T>(p: string, init?: RequestInit)          => request<T>('DELETE', p, undefined, init),
  getBlob,
  url: (p: string) => buildUrl(p),
  headers: () => makeHeaders(),
  qs,
  setToken, getToken, setDebugRole,
}

export default http
