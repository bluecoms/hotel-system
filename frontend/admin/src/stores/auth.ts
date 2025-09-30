// src/stores/auth.ts
import { defineStore } from 'pinia'
import http, { setToken, setDebugRole } from '@/services/http'

export const ROLES = { SUPERADMIN: 'SUPERADMIN', ADMIN: 'ADMIN' } as const
type Role = typeof ROLES[keyof typeof ROLES]
type Me = { email:string; name:string; roles:string[] }

export const useAuthStore = defineStore('auth', {
  state: () => ({ user: null as Me | null }),
  getters: {
    isAuthenticated: (s) => !!s.user,
    hasRole: (s) => (r:string) => s.user?.roles?.includes(r) ?? false,
    hasAnyRole: (s) => (need:string[]) => need.some(r => s.user?.roles?.includes(r)),
  },
  actions: {
    async bootstrap() {
      try {
        const me = await http.get<Me>('me')
        this.user = me
      } catch {
        this.user = null
      }
    },
    async devLogin(role: Role, token?: string) {
      setToken(token || 'dev-admin-token')
      setDebugRole(role)
      await this.bootstrap()
    },
    handle401() {
      this.user = null
      setToken(null)
      // setDebugRole(null) // 필요하면 주석 해제
    },
    logout() {
      this.handle401()
    }
  }
})
