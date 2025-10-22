// src/services/http.ts
import { useToast } from '@/ui/composables/useToast'

const { fromError } = useToast()

const LEGACY_KEY = 'internalToken'
const KEY = 'ADMIN_TOKEN'
const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').trim() || '/api'

// ─────────────────────────────────────────────
// ✅ 개발환경 기본값 설정 (env에서 읽기)
const ENV_INTERNAL_TOKEN = (import.meta.env.VITE_INTERNAL_TOKEN || '').trim()
const ENV_DEBUG_ROLE = (import.meta.env.VITE_DEBUG_ROLE || '').trim().toUpperCase() || null

let ADMIN_TOKEN = (import.meta.env.VITE_ADMIN_TOKEN || ENV_INTERNAL_TOKEN || '').trim()
let DEBUG_ROLE: string | null =
  localStorage.getItem('debugRole') ||
  ENV_DEBUG_ROLE ||
  null
// ─────────────────────────────────────────────

export const getToken = () =>
  ADMIN_TOKEN ||
  localStorage.getItem(KEY) ||
  localStorage.getItem(LEGACY_KEY) || ''

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
    if (detail.message) return String(detail.message)
  }
  try { return JSON.stringify(detail) } catch { return String(detail) }
}

function handleUnauthorized() {
  setToken(null)
  try { sessionStorage.clear() } catch {}
  if (location.pathname.startsWith('/login')) return
  const here = location.pathname + location.search
  const redirect = encodeURIComponent(here)
  location.href = `/login?redirect=${redirect}`
}

function shouldLogoutOn401(requestUrl: string) {
  try {
    const u = new URL(requestUrl, location.origin)
    // 기본은 /api/me 에서만 자동 로그아웃 트리거
    return u.pathname.endsWith('/api/me')
  } catch {
    return false
  }
}

/** 헤더에 X-Silent-Toast: '1' 이 있으면 자동 토스트 억제 */
function isSilent(init?: RequestInit) {
  const h = new Headers(init?.headers || {})
  return h.get('X-Silent-Toast') === '1'
}

/** Content-Disposition 에서 filename 추출 */
function parseFilename(disposition: string | null): string | undefined {
  if (!disposition) return
  // filename*=utf-8''encoded or filename="..."
  const star = /filename\*\s*=\s*([^']*)''([^;]+)/i.exec(disposition)
  if (star && star[2]) {
    try { return decodeURIComponent(star[2]) } catch { return star[2] }
  }
  const normal = /filename\s*=\s*"?([^"]+)"?/i.exec(disposition)
  if (normal && normal[1]) return normal[1]
}

async function request<T>(method: string, path: string, body?: any, init?: RequestInit): Promise<T> {
  const url = buildUrl(path)
  const headers = makeHeaders(init?.headers)
  const opts: RequestInit = { method, headers, credentials: 'omit', ...init }

  if (body instanceof FormData) {
    opts.body = body
  } else if (body !== undefined) {
    if (!headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
    opts.body = JSON.stringify(body)
  }

  let res: Response
  try {
    res = await fetch(url, opts)
  } catch (e: any) {
    const err: any = new Error(e?.message || '네트워크 오류')
    err.status = 0
    if (!isSilent(init)) fromError(err)
    throw err
  }

  if (res.status === 401) {
    if (shouldLogoutOn401(url)) handleUnauthorized()
    const err: any = new Error('Unauthorized')
    err.status = 401
    if (!isSilent(init)) fromError(err)
    throw err
  }

  if (!res.ok) {
    // JSON 시도 → 실패하면 텍스트 메시지라도 살린다
    let detail: any = undefined
    let message: string | undefined
    const ct = res.headers.get('content-type') || ''
    if (ct.includes('application/json')) {
      try { detail = await res.json() } catch {}
      message = extractErrorMessage(detail)
    } else {
      try { const txt = await res.text(); message = txt || undefined } catch {}
    }
    const err: any = new Error(message || res.statusText || 'HTTP error')
    err.status = res.status
    err.detail = detail
    if (!isSilent(init)) fromError(err)
    throw err
  }

  if (res.status === 204) return undefined as unknown as T

  const ct = res.headers.get('content-type') || ''
  if (ct.includes('application/json')) return await res.json() as T
  return await (res.text() as any as Promise<T>)
}

function qs(params?: Record<string, any>) {
  if (!params) return ''
  const s = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null) continue
    if (Array.isArray(v)) {
      for (const it of v) s.append(k, String(it))
    } else {
      s.append(k, String(v))
    }
  }
  const q = s.toString()
  return q ? `?${q}` : ''
}

async function getBlob(path: string, init?: RequestInit): Promise<Blob> {
  const url = buildUrl(path)
  const headers = makeHeaders(init?.headers)
  let res: Response
  try {
    res = await fetch(url, { ...init, headers, credentials: 'omit' })
  } catch (e: any) {
    const err: any = new Error(e?.message || '네트워크 오류')
    err.status = 0
    if (!isSilent(init)) fromError(err)
    throw err
  }

  if (res.status === 401) {
    if (shouldLogoutOn401(url)) handleUnauthorized()
    const err: any = new Error('Unauthorized')
    err.status = 401
    if (!isSilent(init)) fromError(err)
    throw err
  }

  if (!res.ok) {
    let detail: any = undefined
    let message: string | undefined
    const ct = res.headers.get('content-type') || ''
    if (ct.includes('application/json')) {
      try { detail = await res.json() } catch {}
      message = extractErrorMessage(detail)
    } else {
      try { const txt = await res.text(); message = txt || undefined } catch {}
    }
    const err: any = new Error(message || res.statusText || 'HTTP error')
    err.status = res.status
    err.detail = detail
    if (!isSilent(init)) fromError(err)
    throw err
  }

  const blob = await res.blob()
  // filename 부여
  const disp = res.headers.get('content-disposition')
  const name = parseFilename(disp)
  if (name) (blob as any).name = name
  return blob
}

const http = {
  get:    <T>(p: string, init?: RequestInit)          => request<T>('GET',    p, undefined, init),
  post:   <T>(p: string, b?: any, init?: RequestInit) => request<T>('POST',   p, b, init),
  put:    <T>(p: string, b?: any, init?: RequestInit) => request<T>('PUT',    p, b, init),
  patch:  <T>(p: string, b?: any, init?: RequestInit) => request<T>('PATCH',  p, b, init),
  delete: <T>(p: string, init?: RequestInit)          => request<T>('DELETE', p, undefined, init),

  url: (p: string) => buildUrl(p),
  headers: () => makeHeaders(),
  qs,
  getBlob,

  setToken, getToken, setDebugRole,
}

export default http
