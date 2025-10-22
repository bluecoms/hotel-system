// ============================================================================
// File      : src/services/http.ts
// Version   : 2025.10-31 · v3.6 (DeptAccess / Property Header Unified Final)
// Purpose   : Hotel Admin — Fetch 기반 HTTP 클라이언트 (axios 금지, SSOT 규격)
// ----------------------------------------------------------------------------
// 핵심 기능:
//   • 모든 API 호출을 fetch 단일 인터페이스로 관리
//   • 인증: X-Internal-Token 헤더 기반 (localStorage + .env)
//   • 지점(property_code): ✅ “헤더 단일화(X-Property-Code)” 전달
//   • RoleAccess → DeptAccess 구조 전환 이후 완전 호환
//   • Silent Toast / Unauthorized / Network Error 일관 처리
// ----------------------------------------------------------------------------
// 변경 이력:
//   - v2025-10-24 : property_code 헤더 단일화
//   - v2025-10-31 : ✅ DeptAccess 백엔드 완전 정합 / 401 루프 방지 개선
// ============================================================================

import { useToast } from '@/ui/composables/useToast'
import { t } from '@/i18n'
import { usePropertyStore } from '@/stores/property'

const { fromError } = useToast()

// ─────────────────────────────────────────────
// 환경 변수 / 내부 토큰 설정
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

// ─────────────────────────────────────────────
// 토큰 헬퍼
// ─────────────────────────────────────────────
export const getToken = () =>
  ADMIN_TOKEN ||
  localStorage.getItem(KEY) ||
  localStorage.getItem(LEGACY_KEY) ||
  ''

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

/** 디버그 역할(X-Debug-Role) */
export const setDebugRole = (r: string | null) => {
  DEBUG_ROLE = r
  if (r) localStorage.setItem('debugRole', r)
  else localStorage.removeItem('debugRole')
}

// ─────────────────────────────────────────────
// 내부 유틸
// ─────────────────────────────────────────────

/** URL 정규화 (/api 베이스 적용, 중복 슬래시 제거) */
function buildUrl(p: string) {
  if (/^https?:\/\//i.test(p)) return p
  if (p.startsWith('/')) p = p.slice(1)
  const base = API_BASE.replace(/\/+$/, '')
  return `${base}/${p}`.replace(/([^:]\/)\/+/g, '$1')
}

/** 기본 헤더 구성 */
function makeHeaders(init?: HeadersInit): Headers {
  const h = new Headers(init || {})

  // 인증 토큰
  const token = getToken()
  if (token) h.set('X-Internal-Token', token)

  // 디버그 역할
  const role = localStorage.getItem('debugRole') || DEBUG_ROLE
  if (role) h.set('X-Debug-Role', role)

  // Accept / Language
  if (!h.has('Accept')) h.set('Accept', 'application/json')
  if (!h.has('Accept-Language')) h.set('Accept-Language', 'ko-KR')

  // ✅ 지점 코드: 헤더 단일화
  const store = usePropertyStore()
  const property = localStorage.getItem('property_code') || store.get()
  if (property) h.set('X-Property-Code', property)

  return h
}

/** FastAPI detail 메시지 추출 */
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

/** 401 처리 — 루프 방지 */
function handleUnauthorized() {
  setToken(null)
  try {
    sessionStorage.clear()
  } catch {}
}

/** Silent Toast 모드 판별 */
function isSilent(init?: RequestInit) {
  const h = new Headers(init?.headers || {})
  return h.get('X-Silent-Toast') === '1'
}

// ─────────────────────────────────────────────
// fetch wrapper
//   • buildUrl → makeHeaders → fetch
//   • property_code 쿼리 첨부 절대 금지
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

  // Body 직렬화
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

  // JSON or Text 파싱
  const ct = res.headers.get('content-type') || ''
  return ct.includes('application/json')
    ? ((await res.json()) as T)
    : ((await res.text()) as any)
}

// ─────────────────────────────────────────────
// Blob (파일 다운로드)
// ─────────────────────────────────────────────
async function getBlob(path: string, init?: RequestInit): Promise<Blob> {
  const url = buildUrl(path)
  const headers = makeHeaders(init?.headers)
  const res = await fetch(url, { ...init, headers })
  if (!res.ok) throw new Error(`Download failed: ${res.status}`)
  return await res.blob()
}

// ─────────────────────────────────────────────
// 쿼리스트링 유틸 (property_code 자동 금지)
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
  setToken,
  getToken,
  setDebugRole,
}

export default http
