// src/services/users.ts
import http from '@/services/http'

export async function list(params: { q?: string; page?: number; size?: number }) {
  const query = new URLSearchParams()
  if (params.q) query.append('q', params.q)
  if (params.page) query.append('page', String(params.page))
  if (params.size) query.append('size', String(params.size))
  return await http.get(`/users?${query.toString()}`)
}

export async function activate(id: number) {
  return await http.put(`/users/${id}/approve`, { is_active: true })
}

export async function deactivate(id: number) {
  return await http.delete(`/users/${id}`)
}
