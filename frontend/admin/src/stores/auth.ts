// src/stores/auth.ts
import { defineStore } from 'pinia'
import http, { setToken, setDebugRole } from '@/services/http'
import router from '@/router'

export const ROLES = { SUPERADMIN: 'SUPERADMIN', ADMIN: 'ADMIN' } as const
type Role = typeof ROLES[keyof typeof ROLES]
type Me = { email: string; name?: string; roles: string[] }

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as Me | null,
    _booting: null as Promise<void> | null, // 중복 호출 방지
  }),
  getters: {
    isAuthenticated: (s) => !!s.user,
    hasRole: (s) => (r: string) => s.user?.roles?.includes(r) ?? false,
    hasAnyRole: (s) => (need: string[]) => need.some((r) => s.user?.roles?.includes(r)),
    displayName: (s) => s.user?.name || s.user?.email || 'ADMIN', // 표시 폴백
  },
  actions: {
    async bootstrap() {
      if (this._booting) return this._booting
      this._booting = (async () => {
        try {
          const r: any = await http.get('me') // /api/me
          const u = (r?.user) ?? r
          this.user = {
            email: u?.email ?? '',
            name: u?.name ?? (u?.email ?? ''),
            roles: Array.isArray(u?.roles) ? u.roles : [],
          }
        } catch {
          this.user = null
        } finally {
          this._booting = null
        }
      })()
      return this._booting
    },

    async devLogin(role: Role, token?: string) {
      setToken(token || 'dev-admin-token')
      setDebugRole(role)
      await this.bootstrap()
    },

    handle401() {
      this.user = null
      setToken(null)                // ADMIN_TOKEN / internalToken 모두 제거됨
      setDebugRole(null as any)
      try { localStorage.removeItem('debugRole') } catch {}
      try { sessionStorage.clear() } catch {}
    },

    logout() {
      this.handle401()
      router.push({ name: 'login' }).catch(() => { location.href = '/login' })
    },
  },
})
