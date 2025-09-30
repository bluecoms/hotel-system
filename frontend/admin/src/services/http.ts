// /volume1/web/hotel-system/frontend/admin/src/services/http.ts
const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').trim() || '/api'

let ADMIN_TOKEN = (import.meta.env.VITE_ADMIN_TOKEN || '').trim()
let DEBUG_ROLE: string | null = null

export const getToken = () =>
  ADMIN_TOKEN || localStorage.getItem('ADMIN_TOKEN') || ''

export const setToken = (v: string | null) => {
  ADMIN_TOKEN = v || ''
  if (v) localStorage.setItem('ADMIN_TOKEN', v)
  else localStorage.removeItem('ADMIN_TOKEN')
}

export function setDebugRole(r: string | null) { DEBUG_ROLE = r }

/** 절대/상대 경로 모두 허용 */
function buildUrl(p: string) {
  if (/^https?:\/\//i.test(p)) return p
  if (p.startsWith('/')) p = p.slice(1)
  return `${API_BASE}/${p}`
}

function makeHeaders(init?: HeadersInit): Headers {
  const h = new Headers(init || {})
  const t = getToken()
  if (t) h.set('X-Internal-Token', t)
  if (DEBUG_ROLE) h.set('X-Debug-Role', DEBUG_ROLE)
  if (!h.has('Accept')) h.set('Accept', 'application/json')
  return h
}

/** FastAPI 오류(detail)가 배열/문자열 등 다양한 형태일 때 메시지를 뽑아줌 */
function extractErrorMessage(detail: any): string | undefined {
  if (!detail) return undefined
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    // [{loc:..., msg: "..."}] 형태
    const first = detail[0]
    if (first?.msg) return String(first.msg)
    return JSON.stringify(detail)
  }
  if (typeof detail === 'object') {
    if (typeof detail.detail === 'string') return detail.detail
    if (Array.isArray(detail.detail) && detail.detail[0]?.msg) return String(detail.detail[0].msg)
  }
  try { return JSON.stringify(detail) } catch { return String(detail) }
}

async function request<T>(
  method: string,
  path: string,
  body?: any,
  init?: RequestInit
): Promise<T> {
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
    try { detail = await res.json() } catch { /* non-json error */ }
    const message = extractErrorMessage(detail) || res.statusText || 'HTTP error'
    const err: any = new Error(message)
    err.status = res.status
    err.detail = detail
    throw err
  }

  // 204 No Content
  if (res.status === 204) {
    return undefined as unknown as T
  }

  const ct = res.headers.get('content-type') || ''

  if (ct.includes('application/json')) {
    return await res.json() as T
  }
  // 텍스트 응답은 text로 반환 (필요 시 raw/blob 헬퍼 사용 권장)
  return await (res.text() as any as Promise<T>)
}

/** 간단 쿼리 문자열 빌더 (obj -> foo=1&bar=baz) */
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

/** Blob 다운로드가 필요한 경우(예: CSV) */
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
  get:    <T>(p: string, init?: RequestInit)               => request<T>('GET',    p, undefined, init),
  post:   <T>(p: string, b?: any, init?: RequestInit)      => request<T>('POST',   p, b, init),
  put:    <T>(p: string, b?: any, init?: RequestInit)      => request<T>('PUT',    p, b, init),
  patch:  <T>(p: string, b?: any, init?: RequestInit)      => request<T>('PATCH',  p, b, init),
  delete: <T>(p: string, init?: RequestInit)               => request<T>('DELETE', p, undefined, init),

  // 헬퍼
  url: (p: string) => buildUrl(p),
  headers: () => makeHeaders(),
  qs,

  // 파일용
  getBlob,

  // 토큰/디버그 롤
  setToken, getToken, setDebugRole,
}

export default http
