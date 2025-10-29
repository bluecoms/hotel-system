<!-- ============================================================================
# File      : src/views/Admin/HR/Dashboard.vue
# Version   : 2025.11-10 · v2.0 (SSOT Stable · Mock Fallback + UI Polished)
# Purpose   : Hotel Admin — HR 대시보드 (직원 현황 · 계약 만료 · 인사 추이)
# ----------------------------------------------------------------------------
# 주요 특징
#   ✅ HR 핵심지표(KPI) + 인력 추이 + 계약 만료 예고
#   ✅ 백엔드 API 미구현 시에도 목업 데이터 표시(Fallback)
#   ✅ BaseChart / KpiCard 공통 컴포넌트 기반
# ----------------------------------------------------------------------------
# 연계 API (예정)
#   • GET /api/hr/dashboard/summary  → KPI / 계약 만료
#   • GET /api/hr/dashboard/trend    → 인력 추이 (기간별)
# ----------------------------------------------------------------------------
# 구성
#   1) KPI 카드 4개 (총원, 신규, 퇴사, 평균 근속)
#   2) 인력 추이 그래프 (3/6/12개월 단위)
#   3) 계약 만료 예정 테이블
# ============================================================================ -->
<template>
  <v-container fluid class="page-shell py-6">

    <!-- ▣ 상단 툴바 -->
    <div class="bar mb-6">
      <div class="bar-left">
        <v-icon color="primary" icon="mdi-account-group-outline" size="22" />
        <h2 class="text-h6 font-weight-bold">HR 대시보드</h2>
        <span class="text-muted text-body-2">
          직원 현황 · 계약 만료 · 인력 추이
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

    <!-- ▣ KPI 카드 -->
    <v-row dense class="mb-4">
      <v-col v-for="kpi in kpis" :key="kpi.key" cols="12" sm="6" md="3">
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

    <!-- ▣ 인력 추이 그래프 -->
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
        표시할 데이터가 없습니다.
      </div>
    </v-card>

    <!-- ▣ 계약 만료 예정 테이블 -->
    <v-card class="pa-4 panel">
      <div class="d-flex justify-space-between align-center mb-3">
        <h3 class="text-h6 font-weight-medium">계약 만료 예정</h3>
        <v-btn
          variant="text"
          color="primary"
          @click="$router.push('/admin/hr/contracts')"
        >
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
/* ============================================================================
# Script — HR Dashboard (v2.0)
# ----------------------------------------------------------------------------
# • KPI 카드, 인력 추이, 계약 만료 목록을 로드하여 표시
# • HrDashboardApi 없을 시 목업 데이터로 대체 표시
# ============================================================================ */
import { ref, reactive, onMounted } from 'vue'
import { useToast } from '@/ui/composables/useToast'
import * as HrDashboardApi from '@/services/hr_dashboard'
import KpiCard from '@/ui/components/common/KpiCard.vue'
import BaseChart from '@/ui/components/common/BaseChart.vue'

const toast = useToast()
const loading = ref(false)
const kpis = ref<any[]>([])
const trendData = reactive({ labels: [] as string[], datasets: [] as any[] })
const expiringContracts = ref<any[]>([])

/* ▣ 기간 선택 */
const period = ref('3m')
const periodItems = [
  { title: '최근 3개월', value: '3m' },
  { title: '최근 6개월', value: '6m' },
  { title: '최근 12개월', value: '12m' },
]

/* ▣ 만료 계약 테이블 헤더 */
const expireHeaders = [
  { title: '직원명', key: 'employee_name' },
  { title: '계약명', key: 'contract_title' },
  { title: '종료일', key: 'end_date' },
]

/* ▣ 메인 로드 */
async function reload() {
  loading.value = true
  try {
    const res: any = await HrDashboardApi.getSummary()
    kpis.value = res.kpis || mockKpis()
    expiringContracts.value = res.expiring_contracts || mockExpiring()
    await reloadTrend()
  } catch (e: any) {
    console.warn('[HR Dashboard] API unavailable → fallback data')
    toast.info('HR 대시보드를 목업 데이터로 표시합니다.')
    kpis.value = mockKpis()
    expiringContracts.value = mockExpiring()
    trendData.labels = mockTrend().labels
    trendData.datasets = mockTrend().datasets
  } finally {
    loading.value = false
  }
}

/* ▣ 인력 추이 로드 */
async function reloadTrend() {
  try {
    const res: any = await HrDashboardApi.getTrend({ period: period.value })
    trendData.labels = res.labels || []
    trendData.datasets = res.datasets || []
  } catch {
    const mock = mockTrend()
    trendData.labels = mock.labels
    trendData.datasets = mock.datasets
  }
}

/* ▣ 유틸 */
function isExpired(dateStr: string) {
  if (!dateStr) return false
  const today = new Date().toISOString().slice(0, 10)
  return dateStr < today
}

/* ▣ 차트 옵션 */
const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: 'bottom' } },
  scales: { y: { beginAtZero: true } },
}

/* ▣ 목업 데이터 (Fallback) */
function mockKpis() {
  return [
    { key: 'total', title: '총 직원 수', value: 42, icon: 'mdi-account', color: 'primary' },
    { key: 'new', title: '신규 입사', value: 3, icon: 'mdi-account-plus', color: 'success' },
    { key: 'leave', title: '퇴사자', value: 1, icon: 'mdi-account-off', color: 'error' },
    { key: 'avg_years', title: '평균 근속(년)', value: 2.8, icon: 'mdi-timer-sand', color: 'indigo' },
  ]
}

function mockExpiring() {
  return [
    { employee_name: '기창민', contract_title: '정규직(월급제)', end_date: '2025-12-31' },
    { employee_name: '백초휘', contract_title: '계약직(연장)', end_date: '2025-11-15' },
  ]
}

function mockTrend() {
  return {
    labels: ['7월', '8월', '9월', '10월', '11월'],
    datasets: [
      {
        label: '직원 수',
        data: [38, 40, 41, 42, 42],
        borderColor: '#3b82f6',
        fill: false,
      },
      {
        label: '이직률(%)',
        data: [3.2, 2.8, 2.5, 2.4, 2.0],
        borderColor: '#ef4444',
        fill: false,
        yAxisID: 'y1',
      },
    ],
  }
}

/* ▣ 초기 실행 */
onMounted(reload)
</script>

<style scoped src="@/styles/toolbar.scss"></style>

<style scoped>
.page-shell {
  max-width: 1280px;
  margin: 0 auto;
}

/* 테이블 / 차트 / 카드 톤 일원화 */
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

/* 경고색 강조 */
.text-error { color: var(--color-error) !important; }

/* 카드 패널 공통 스타일 */
.panel {
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}
</style>
