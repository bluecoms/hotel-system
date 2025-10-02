import { defineStore } from 'pinia'
import http from '@/services/http'
import { useAuthStore } from '@/stores/auth'

export type MenuItem = { label: string; to: string; roles?: string[] }

function up(arr?: string[]) {
  return (arr ?? []).map(s => String(s).toUpperCase())
}

// API(backend)는 title/to/roles 를 내려줌 → FE는 label/to/roles 사용
function normalize(items: any[]): MenuItem[] {
  return (items ?? []).map((m: any) => ({
    label: String(m.label ?? m.title ?? ''),   // ← 핵심: title → label 매핑
    to: String(m.to ?? ''),
    roles: Array.isArray(m.roles) ? m.roles : [],
  }));
}

export const useMenuStore = defineStore('menu', {
  state: () => ({ items: [] as MenuItem[], loaded: false }),
  getters: {
    visibleItems: (s) => {
      const auth = useAuthStore()
      const my = up(auth.user?.roles)
      const isSuper = my.includes('SUPERADMIN')
      return (s.items ?? []).filter((m) => {
        const need = up(m.roles)
        if (isSuper) return true
        if (!need.length) return true
        return need.some(r => my.includes(r))
      })
    },
  },
  actions: {
    async load() {
      if (this.loaded) return
      try {
        const data = await http.get<{ items: any[] }>('menu')
        this.items = normalize(data?.items ?? [])
      } catch {
        // Fallback (개발용)
        this.items = [
          { label:'Dashboard', to:'/dashboard', roles:['ADMIN','SUPERADMIN'] },
          { label:'Closing', to:'/closing', roles:['ADMIN','SUPERADMIN'] },
          { label:'Users', to:'/admin/users', roles:['SUPERADMIN'] },
          { label:'OTA', to:'/admin/ota/list', roles:['ADMIN'] },
          { label:'Commissions', to:'/admin/ota/commission', roles:['ADMIN'] },
          { label:'Reports — Sales Tags', to:'/admin/reports/sales-tags', roles:['ADMIN'] },
        ]
      } finally {
        this.loaded = true
      }
    }
  }
})
