// src/stores/kpi.ts
import { defineStore } from 'pinia'

export const useKpiStore = defineStore('kpi', {
  state: () => ({
    totals: {} as Record<string, any>,
  }),
  actions: {
    pushTotals(data: Record<string, any>) {
      this.totals = { ...this.totals, ...data }
    },
    async refreshDashboard(_payload?: Record<string, any>) {
      // 임시 스켈레톤 (나중에 /api/reports/dashboard-kpi 연동)
      return Promise.resolve()
    },
  },
})

