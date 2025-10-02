const LEGACY_KEY = 'internalToken'                     // 레거시 키
const KEY = 'ADMIN_TOKEN'                              // 현행 키
const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').trim() || '/api'

let ADMIN_TOKEN = (import.meta.env.VITE_ADMIN_TOKEN || '').trim()
let DEBUG_ROLE: string | null = localStorage.getItem('debugRole') || null

export const getToken = () =>
  ADMIN_TOKEN ||
  localStorage.getItem(KEY) ||
  localStorage.getItem(LEGACY_KEY) || ''

export const setToken = (v: string | null) => {
  ADMIN_TOKEN = v || ''
  if (v) {
    localStorage.setItem(KEY, v)
    localStorage.setItem(LEGACY_KEY, v)            // 이행 단계 동기화(선택)
  } else {
    localStorage.removeItem(KEY)
    localStorage.removeItem(LEGACY_KEY)
  }
}

export function setDebugRole(r: string | null) {
  DEBUG_ROLE = r
  if (r) localStorage.setItem('debugRole', r)
  else localStorage.removeItem('debugRole')
}

function buildUrl(p: string) {
  if (/^https?:\/\//i.test(p)) return p
  if (p.startsWith('/')) p = p.slice(1)
  return `${API_BASE}/${p}`
}

function makeHeaders(init?: HeadersInit): Headers {
  const h = new Headers(init || {})
  const t = getToken()
  if (t) h.set('X-Internal-Token', t)

  // DEV ONLY: X-Debug-Role
  const currentDebug =
    (typeof DEBUG_ROLE === 'string' ? DEBUG_ROLE : null) ??
    (localStorage.getItem('debugRole') ?? null)
  if (currentDebug) h.set('X-Debug-Role', currentDebug)

  if (!h.has('Accept')) h.set('Accept', 'application/json')
  // 고정 언어(서버 로깅/감사로그용 메타): ko-KR
  if (!h.has('Accept-Language')) h.set('Accept-Language', 'ko-KR')
  return h
}

function extractErrorMessage(detail: any): string | undefined {
  if (!detail) return undefined
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const first = detail[0]
    if (first?.msg) return String(first.msg)
    try { return JSON.stringify(detail) } catch { return String(detail) }
  }
  if (typeof detail === 'object') {
    if (typeof detail.detail === 'string') return detail.detail
    if (Array.isArray(detail.detail) && detail.detail[0]?.msg) return String(detail.detail[0].msg)
  }
  try { return JSON.stringify(detail) } catch { return String(detail) }
}

async function request<T>(method: string, path: string, body?: any, init?: RequestInit): Promise<T> {
  const url = buildUrl(path)
  const headers = makeHeaders(init?.headers)
  const opts: RequestInit = { method, headers, ...init }

  if (body instanceof FormData) {
    opts.body = body
  } else if (body !== undefined) {
    headers.set('Content-Type', 'application/json')
    opts.body = JSON.stringify(body)
  }

  const res = await fetch(url, opts)

  if (!res.ok) {
    let detail: any = undefined
    try { detail = await res.json() } catch {}
    const message = extractErrorMessage(detail) || res.statusText || 'HTTP error'
    const err: any = new Error(message)
    err.status = res.status
    err.detail = detail
    throw err
  }

  if (res.status === 204) return undefined as unknown as T

  const ct = res.headers.get('content-type') || ''
  if (ct.includes('application/json')) {
    return await res.json() as T
  }
  return await (res.text() as any as Promise<T>)
}

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

async function getBlob(path: string, init?: RequestInit): Promise<Blob> {
  const url = buildUrl(path)
  const headers = makeHeaders(init?.headers)
  const res = await fetch(url, { ...init, headers })
  if (!res.ok) {
    let detail: any = undefined
    try { detail = await res.json() } catch {}
    const err: any = new Error(extractErrorMessage(detail) || res.statusText || 'HTTP error')
    err.status = res.status; err.detail = detail
    throw err
  }
  return await res.blob()
}

const http = {
  get:    <T>(p: string, init?: RequestInit)          => request<T>('GET',    p, undefined, init),
  post:   <T>(p: string, b?: any, init?: RequestInit) => request<T>('POST',   p, b, init),
  put:    <T>(p: string, b?: any, init?: RequestInit) => request<T>('PUT',    p, b, init),
  patch:  <T>(p: string, b?: any, init?: RequestInit) => request<T>('PATCH',  p, b, init),
  delete: <T>(p: string, init?: RequestInit)          => request<T>('DELETE', p, undefined, init),

  // helpers
  url: (p: string) => buildUrl(p),
  headers: () => makeHeaders(),
  qs,
  getBlob,

  // token/debug
  setToken, getToken, setDebugRole,
}

export default http
