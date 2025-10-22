// src/services/menu.ts
import http from '@/services/http'

export type MenuItem = {
  id?: string
  label: string
  path?: string
  to?: string
  children?: MenuItem[]
  roles?: string[]
}

export async function getMenu(): Promise<MenuItem[] | { items: MenuItem[] }> {
  return await http.get('menu')
}
