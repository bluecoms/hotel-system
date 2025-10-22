// src/services/ota.ts
import http from '@/services/http'

export type Channel = { id?: number; code: string; name: string; created_at?: string }
export type Commission = {
  id?: number
  channel: string
  valid_from: string
  valid_to: string
  rate: number
  note?: string
}

type Paged<T> = T[] | { items: T[]; total?: number }

export async function listChannels(params?: { limit?: number; offset?: number }) {
  return await http.get<Paged<Channel>>(`/ota/channels${http.qs(params)}`)
}

export async function createChannel(body: { code: string; name: string }) {
  return await http.post<Channel>('/ota/channels', body)
}

export async function listCommissions(params: {
  channel?: string
  date_from?: string
  date_to?: string
  limit?: number
  offset?: number
}) {
  return await http.get<Paged<Commission>>(`/ota/commissions${http.qs(params)}`)
}

export async function createCommission(body: Commission) {
  return await http.post<Commission>('/ota/commissions', body)
}

export async function updateCommission(id: number, body: Partial<Commission>) {
  return await http.put<Commission>(`/ota/commissions/${id}`, body)
}

export async function deleteCommission(id: number) {
  return await http.delete<void>(`/ota/commissions/${id}`)
}
