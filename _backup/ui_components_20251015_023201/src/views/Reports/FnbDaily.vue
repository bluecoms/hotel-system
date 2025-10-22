<template>
  <ReportsShell
    title="F&B 일별 매출 리포트"
    icon="mdi-silverware-fork-knife"
    property-code="MOP"
    @filter="onFilter"
  >
    <StateBlock v-if="loading" :loading="true" />

    <v-card v-else>
      <v-card-title class="d-flex align-center justify-space-between">
        <span>F&B Daily Summary</span>
        <v-chip size="small" variant="outlined">{{ propertyCode }}</v-chip>
      </v-card-title>
      <v-divider />

      <v-table density="comfortable">
        <thead>
          <tr>
            <th>날짜</th>
            <th>건수</th>
            <th class="text-right">매출금액</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rows" :key="r.business_date">
            <td>{{ r.business_date }}</td>
            <td>{{ n(r.count) }}</td>
            <td class="text-right">{{ k(r.amount) }}</td>
          </tr>
          <tr v-if="!rows.length">
            <td colspan="3" class="text-center text-medium-emphasis py-6">No data</td>
          </tr>
        </tbody>
        <tfoot v-if="rows.length">
          <tr class="font-weight-bold">
            <td>Total</td>
            <td>{{ n(total.count) }}</td>
            <td class="text-right">{{ k(total.amount) }}</td>
          </tr>
        </tfoot>
      </v-table>

      <v-alert v-if="err" type="warning" class="ma-3">{{ err }}</v-alert>
    </v-card>
  </ReportsShell>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ReportsShell from './ReportsShell.vue'
import StateBlock from '@/ui/components/common/StateBlock.vue'
import { useToast } from '@/ui/composables/useToast'
import http from '@/services/http'

const { error: toastError } = useToast()
const propertyCode = ref('MOP')
const dateFrom = ref('')
const dateTo = ref('')
const loading = ref(false)
const rows = ref<{ business_date: string; count: number; amount: number }[]>([])
const err = ref<string | null>(null)

const total = ref({ count: 0, amount: 0 })
const k = (n: number) => Number(n || 0).toLocaleString('ko-KR')
const n = (n: number) => Number(n || 0).toLocaleString('ko-KR')

async function onFilter(p: { date_from: string; date_to: string; property_code: string }) {
  dateFrom.value = p.date_from
  dateTo.value = p.date_to
  propertyCode.value = p.property_code
  loading.value = true
  err.value = null

  try {
    const url = `/api/reports/fnb-daily?property_code=${propertyCode.value}&date_from=${dateFrom.value}&date_to=${dateTo.value}`
    const res: any = await http.get(url)
    rows.value = res.items || []
    total.value = rows.value.reduce(
      (acc, r) => ({ count: acc.count + (r.count || 0), amount: acc.amount + (r.amount || 0) }),
      { count: 0, amount: 0 }
    )
  } catch (e: any) {
    err.value = e?.message || '불러오기 실패'
    toastError(err.value)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.v-table { font-size: 0.95rem; }
</style>
