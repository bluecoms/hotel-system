// src/stores/auth.ts
import { defineStore } from 'pinia'
import http, { setToken } from '@/services/http'
import router from '@/router'
import { login as apiLogin } from '@/services/auth'

type Me = { email: string; name?: string; roles: string[] }
type AccessLevel = 'none' | 'view' | 'edit' | 'admin'
type AccessRec = { role_code: string; route_name: string; access_level: AccessLevel }

const LEVEL_ORDER: Record<AccessLevel, number> = { none: 0, view: 1, edit: 2, admin: 3 }

function normalizeRoute(input: string): string {
  if (!input) return ''
  let s = input.trim()
  return s
    .replace(/^\/api\//i, '')
    .replace(/^\//, '')
    .replace(/[./]/g, '-')
    .replace(/--+/g, '-')
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as Me | null,
    _booting: null as Promise<void> | null,
    _access: [] as AccessRec[],
    _accessLoaded: false,
    _effective: {} as Record<string, AccessLevel>,
    _effectiveLoaded: false,
  }),

  getters: {
    isAuthenticated: (s) => !!s.user,
    hasRole: (s) => (r: string) =>
      (s.user?.roles ?? []).map(x => x.toUpperCase()).includes(r.toUpperCase()),
    hasAnyRole: (s) => (need: string[]) =>
      need.map(x => x.toUpperCase()).some(r =>
        (s.user?.roles ?? []).map(x => x.toUpperCase()).includes(r)
      ),
    hasAccess: (s) => (route: string, level: AccessLevel = 'view') => {
      const roles = (s.user?.roles ?? []).map(x => x.toUpperCase())
      if (roles.includes('SUPERADMIN')) return true

      const needed = LEVEL_ORDER[level] ?? 1
      const rn = normalizeRoute(route)

      // 1) effective 맵 우선
      const eff = s._effective[rn] ?? s._effective['*']
      if (eff && LEVEL_ORDER[eff] >= needed) return true

      // 2) 원시 role_access 테이블(백업 경로)
      for (const r of roles) {
        const exact = s._access.find(
          a => a.role_code.toUpperCase() === r && normalizeRoute(a.route_name) === rn
        )
        if (exact && LEVEL_ORDER[exact.access_level] >= needed) return true

        const star = s._access.find(
          a => a.role_code.toUpperCase() === r && a.route_name === '*'
        )
        if (star && LEVEL_ORDER[star.access_level] >= needed) return true
      }

      // 3) ADMIN 관대한 기본값 (view/edit 허용)
      if (roles.includes('ADMIN') && (level === 'view' || level === 'edit')) return true
      return false
    },
    can() {
      return this.hasAccess
    },
    displayName: (s) => s.user?.name || s.user?.email || 'ADMIN',
  },

  actions: {
    async bootstrap() {
      if (this._booting) return this._booting
      this._booting = (async () => {
        try {
          const r: any = await http.get('me')
          const u = r?.user ?? r
          this.user = {
            email: u?.email ?? '',
            name: u?.name ?? (u?.email ?? ''),
            roles: Array.isArray(u?.roles) ? u.roles : [],
          }
          if (this.user) {
            await Promise.allSettled([
              this.loadEffectiveAccess(),
              this.loadAccessMatrix(),
            ])
          }
        } catch {
          this.user = null
        } finally {
          this._booting = null
        }
      })()
      return this._booting
    },

    async login(token: string) {
      setToken(token || 'dev-admin-token')
      await this.bootstrap()
      if (!this.user) throw new Error('인증 실패')
    },

    async loginWithCredentials(email: string, password: string) {
      const res = await apiLogin(email, password)
      setToken(res.token)
      await this.bootstrap()
      if (!this.user) throw new Error('인증 실패')
    },

    handle401() {
      this.user = null
      setToken(null)
      sessionStorage.clear()
      this._effective = {}
      this._effectiveLoaded = false
      this._access = []
      this._accessLoaded = false
    },

    logout() {
      this.handle401()
      router.push({ name: 'login' }).catch(() => {
        location.href = '/login'
      })
    },

    async loadAccessMatrix() {
      try {
        const r: any = await http.get('/users/roles/access')
        this._access = Array.isArray(r) ? r : r.items ?? []
        this._accessLoaded = true
      } catch (e) {
        console.warn('⚠️ 권한 매트릭스 로드 실패:', e)
        this._access = []
        this._accessLoaded = false
      }
    },

    async loadEffectiveAccess() {
      const myRoles = (this.user?.roles ?? []).map(r => r.toUpperCase())

      try {
        const r: any = await http.get('/users/roles/access/effective')

        // 서버는 { roles: string[], access: Record<string, AccessLevel> } 형태를 반환
        const mapRaw: unknown =
          r && typeof r === 'object' && 'access' in r ? (r as any).access : r

        if (!mapRaw || typeof mapRaw !== 'object') throw { status: 404 }

        const map = mapRaw as Record<string, unknown>
        const out: Record<string, AccessLevel> = {}

        for (const [k, v] of Object.entries(map)) {
          const rn = normalizeRoute(k)
          const lvlStr = String(v).toLowerCase()
          if (lvlStr === 'none' || lvlStr === 'view' || lvlStr === 'edit' || lvlStr === 'admin') {
            out[rn] = lvlStr
          }
        }

        this._effective = out
        this._effectiveLoaded = true
        return
      } catch (e: any) {
        if (e?.status !== 404) {
          console.warn('⚠️ 효율 권한 맵 로드 실패:', e)
        }
      }

      // fallback: /users/roles/access (role_access 테이블에서 계산)
      try {
        const list: any = await http.get('/users/roles/access')
        const rows: AccessRec[] = Array.isArray(list) ? list : (list.items ?? [])
        const out: Record<string, AccessLevel> = {}

        const apply = (route: string, level: AccessLevel) => {
          const rn = normalizeRoute(route)
          const cur = out[rn]
          if (!cur || LEVEL_ORDER[level] > LEVEL_ORDER[cur]) out[rn] = level
        }

        for (const rec of rows) {
          const role = rec.role_code.toUpperCase()
          if (!myRoles.includes(role)) continue
          apply(rec.route_name, rec.access_level)
        }

        const starBest = rows
          .filter(r => myRoles.includes(r.role_code.toUpperCase()) && r.route_name === '*')
          .map(r => r.access_level)
          .sort((a, b) => LEVEL_ORDER[b] - LEVEL_ORDER[a])[0]
        if (starBest) out['*'] = starBest

        this._effective = out
        this._effectiveLoaded = true
      } catch (e) {
        console.warn('⚠️ 효율 권한 맵 폴백 계산 실패:', e)
        this._effective = {}
        this._effectiveLoaded = false
      }
    },
  },
})
