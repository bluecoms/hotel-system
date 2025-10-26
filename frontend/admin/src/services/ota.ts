// ============================================================================
// File      : src/services/ota.ts
// Version   : 2.1 Final (2025-11-05 · SSOT Stable · Commission/Channel Safe)
// Purpose   : Hotel Admin — OTA Channels & Commissions API Service
// ----------------------------------------------------------------------------
// 목적:
//   • OTA 채널(Booking, Agoda 등) 및 커미션(수수료율) 관리.
//   • /api/ota/channels, /api/ota/commissions 기반 CRUD.
// ----------------------------------------------------------------------------
// 주요 개선 (v2.1):
//   ✅ { items } / [] 응답 자동 정규화
//   ✅ /api prefix 자동 적용 (Dev/Prod 프록시 호환)
//   ✅ 오류 시 빈 배열 반환 및 안전 로깅
//   ✅ 주석/타입 SSOT 규격(auth/master와 통일)
// ----------------------------------------------------------------------------
// 연동 백엔드 (최신 기준):
//   • GET  /api/ota/channels
//   • POST /api/ota/channels
//   • GET  /api/ota/commissions
//   • POST /api/ota/commissions
//   • PUT  /api/ota/commissions/{id}
//   • DELETE /api/ota/commissions/{id}
// ============================================================================

import http from '@/services/http'

// ----------------------------------------------------------------------------
//  타입 정의
// ----------------------------------------------------------------------------
export type Channel = {
  id?: number
  code: string
  name: string
  created_at?: string
}

export type Commission = {
  id?: number
  channel: string
  valid_from: string
  valid_to: string
  rate: number
  note?: string
}

export type Paged<T> = {
  items: T[]
  total?: number
}

// ============================================================================
// 1️⃣ OTA 채널 목록 조회
// ----------------------------------------------------------------------------
export async function listChannels(params?: { limit?: number; offset?: number }): Promise<Paged<Channel>> {
  try {
    const res = await http.get<Paged<Channel> | Channel[]>(`/ota/channels${http.qs(params)}`)
    if (Array.isArray(res)) return { items: res, total: res.length }
    if (Array.isArray((res as any)?.items)) return res as Paged<Channel>
    return { items: [], total: 0 }
  } catch (err) {
    console.error('[OTA.listChannels] failed:', err)
    return { items: [], total: 0 }
  }
}

// ============================================================================
// 2️⃣ OTA 채널 등록
// ----------------------------------------------------------------------------
export async function createChannel(body: { code: string; name: string }) {
  try {
    return await http.post<Channel>('/ota/channels', body)
  } catch (err) {
    console.error('[OTA.createChannel] failed:', err)
    throw err
  }
}

// ============================================================================
// 3️⃣ 커미션 목록 조회
// ----------------------------------------------------------------------------
export async function listCommissions(params?: {
  channel?: string
  date_from?: string
  date_to?: string
  limit?: number
  offset?: number
}): Promise<Paged<Commission>> {
  try {
    const res = await http.get<Paged<Commission> | Commission[]>(`/ota/commissions${http.qs(params)}`)
    if (Array.isArray(res)) return { items: res, total: res.length }
    if (Array.isArray((res as any)?.items)) return res as Paged<Commission>
    return { items: [], total: 0 }
  } catch (err) {
    console.error('[OTA.listCommissions] failed:', err)
    return { items: [], total: 0 }
  }
}

// ============================================================================
// 4️⃣ 커미션 등록
// ----------------------------------------------------------------------------
export async function createCommission(body: Commission) {
  try {
    return await http.post<Commission>('/ota/commissions', body)
  } catch (err) {
    console.error('[OTA.createCommission] failed:', err)
    throw err
  }
}

// ============================================================================
// 5️⃣ 커미션 수정
// ----------------------------------------------------------------------------
export async function updateCommission(id: number, body: Partial<Commission>) {
  try {
    return await http.put<Commission>(`/ota/commissions/${id}`, body)
  } catch (err) {
    console.error('[OTA.updateCommission] failed:', err)
    throw err
  }
}

// ============================================================================
// 6️⃣ 커미션 삭제
// ----------------------------------------------------------------------------
export async function deleteCommission(id: number) {
  try {
    return await http.delete<{ ok?: boolean }>(`/ota/commissions/${id}`)
  } catch (err) {
    console.error('[OTA.deleteCommission] failed:', err)
    throw err
  }
}

// ============================================================================
// ✅ EOF — src/services/ota.ts (v2.1 Final · SSOT 안정판)
// ============================================================================
