// src/stores/menu.ts
import { defineStore } from 'pinia'
import http from '@/services/http'
import { useAuthStore } from '@/stores/auth'

export type MenuItem = { label:string; to:string; roles?:string[] }

export const useMenuStore = defineStore('menu', {
  state: () => ({ items: [] as MenuItem[], loaded: false }),
  getters: {
    visibleItems: (s) => {
      const auth = useAuthStore()
      const isSuper = auth.user?.roles?.includes('SUPERADMIN')
      const needToShow = (m:MenuItem) =>
        isSuper || !m.roles?.length || m.roles!.some(r => auth.user?.roles?.includes(r))
      return (s.items ?? []).filter(needToShow)
    },
  },
  actions: {
    async load() {
      if (this.loaded) return
      try {
        const data = await http.get<{items:MenuItem[]}>('menu')
        this.items = data?.items ?? []
      } catch {
        // fallback (슈퍼도 보이게)
        this.items = [
          { label:'Dashboard',     to:'/dashboard',      roles:['ADMIN','SUPERADMIN'] },
          { label:'Closing',       to:'/closing',        roles:['ADMIN','SUPERADMIN'] },
          { label:'Closing Board', to:'/closing/board',  roles:['ADMIN','SUPERADMIN'] },
          { label:'Users',         to:'/admin/users',    roles:['SUPERADMIN'] },
          { label:'Keywords',      to:'/keywords',       roles:['ADMIN','SUPERADMIN'] },
          { label:'OTA',           to:'/ota',            roles:['ADMIN','SUPERADMIN'] },
        ]
      } finally {
        this.loaded = true
      }
    }
  }
})
