<template>
  <v-container fluid class="page-shell py-6">
    <div class="bar mb-6">
      <div class="bar-left">
        <v-icon color="primary" icon="mdi-account-group-outline" size="22" />
        <h2 class="text-h6 font-weight-bold">HR 대시보드</h2>
        <span class="text-muted text-body-2">
          직원 현황 · 계약 만료 · 평가 일정 등 인사 주요 지표
        </span>
      </div>
      <div class="bar-right">
        <v-btn
          color="primary"
          prepend-icon="mdi-refresh"
          :loading="loading"
          variant="flat"
          class="btn-action"
          @click="reload"
        >
          새로고침
        </v-btn>
      </div>
    </div>

    <v-row dense class="mb-4">
      <v-col
        v-for="kpi in kpis"
        :key="kpi.key"
        cols="12"
        sm="6"
        md="3"
      >
        <KpiCard
          :title="kpi.title"
          :value="kpi.value"
          :icon="kpi.icon"
          :color="kpi.color"
          :trend="kpi.trend"
          :unit="kpi.unit"
        />
      </v-col>
    </v-row>

    <v-card class="pa-4 mb-4 panel">
      <div class="d-flex justify-space-between align-center mb-2">
        <h3 class="text-h6 font-weight-medium">직원 수 및 이직률 추이</h3>
        <v-select
          v-model="period"
          :items="periodItems"
          label="기간 선택"
          hide-details
          density="compact"
          style="max-width: 180px"
          @update:model-value="reloadTrend"
        />
      </div>

      <BaseChart
        v-if="trendData.labels.length"
        type="line"
        :data="trendData"
        :options="chartOptions"
        height="300px"
      />
      <div v-else class="text-grey text-caption pa-6 text-center">
        데이터 없음
      </div>
    </v-card>

    <v-card class="pa-4 panel">
      <div class="d-flex justify-space-between align-center mb-3">
        <h3 class="text-h6 font-weight-medium">계약 만료 예정</h3>
        <v-btn variant="text" color="primary" @click="$router.push('/admin/hr/contracts')">
          전체 보기
        </v-btn>
      </div>

      <v-data-table
        :headers="expireHeaders"
        :items="expiringContracts"
        density="compact"
        class="text-body-2"
        hide-default-footer
      >
        <template #item.end_date="{ item }">
          <span :class="isExpired(item.end_date) ? 'text-error font-weight-medium' : ''">
            {{ item.end_date }}
          </span>
        </template>

        <template #no-data>
          <div class="pa-4 text-grey text-caption text-center">
            만료 예정 계약이 없습니다.
          </div>
        </template>
      </v-data-table>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useToast } from '@/ui/composables/useToast'
import * as HrDashboardApi from '@/services/hr_dashboard'
import KpiCard from '@/ui/components/KpiCard.vue'
import BaseChart from '@/ui/components/BaseChart.vue'

const toast = useToast()
const loading = ref(false)
const kpis = ref<any[]>([])
const trendData = reactive({ labels: [] as string[], datasets: [] as any[] })
const period = ref('3m')
const periodItems = [
  { title: '최근 3개월', value: '3m' },
  { title: '최근 6개월', value: '6m' },
  { title: '최근 12개월', value: '12m' },
]
const expiringContracts = ref<any[]>([])
const expireHeaders = [
  { title: '직원명', key: 'employee_name' },
  { title: '계약명', key: 'contract_title' },
  { title: '종료일', key: 'end_date' },
]

async function reload() {
  loading.value = true
  try {
    const res: any = await HrDashboardApi.getSummary()
    kpis.value = res.kpis || []
    expiringContracts.value = res.expiring_contracts || []
    reloadTrend()
  } catch (e: any) {
    toast.error('HR 대시보드를 불러올 수 없습니다.')
  } finally {
    loading.value = false
  }
}

async function reloadTrend() {
  try {
    const res: any = await HrDashboardApi.getTrend({ period: period.value })
    trendData.labels = res.labels || []
    trendData.datasets = res.datasets || []
  } catch (e: any) { console.warn(e) }
}

function isExpired(dateStr: string) {
  if (!dateStr) return false
  const today = new Date().toISOString().slice(0, 10)
  return dateStr < today
}

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: 'bottom' } },
  scales: { y: { beginAtZero: true } },
}

onMounted(reload)
</script>

<style scoped src="@/styles/toolbar.scss"></style>

<style scoped>
.page-shell {
  max-width: 1280px;
  margin: 0 auto;
}

/* 표 관련 톤 조정 */
.v-data-table {
  border-radius: var(--radius-sm);
  overflow: hidden;
  border: 1px solid var(--color-line);
}
.v-data-table thead th {
  background-color: var(--color-surface);
  color: var(--color-muted);
  font-weight: 600;
  font-size: 0.9rem;
}

/* 경고색 */
.text-error { color: var(--color-error) !important; }

/* 카드 패널 표준화 */
.panel {
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}
</style>
