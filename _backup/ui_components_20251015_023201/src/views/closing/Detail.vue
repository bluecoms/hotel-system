<template>
  <v-container fluid class="page-shell py-6">
    <div class="bar mb-6">
      <div class="bar-left">
        <v-icon color="primary" icon="mdi-calendar-month-outline" size="22" />
        <h2 class="text-h6 font-weight-bold">마감 상세</h2>
        <span class="text-muted text-body-2">일자별 업로드 현황 및 진행률</span>
      </div>
      <div class="bar-right d-flex align-center" style="gap:8px">
        <v-btn icon="mdi-chevron-left" variant="text" @click="shift(-1)" />
        <v-text-field
          v-model="month"
          label="Month (YYYY-MM)"
          density="comfortable"
          hide-details
          style="max-width:160px"
        />
        <v-btn color="primary" prepend-icon="mdi-refresh" @click="load">불러오기</v-btn>
        <v-btn icon="mdi-chevron-right" variant="text" @click="shift(1)" />
      </div>
    </div>

    <v-card class="brand-panel">
      <v-card-title class="font-weight-bold">일자별 업로드 진행 현황</v-card-title>
      <v-divider />
      <v-table density="comfortable">
        <thead>
          <tr>
            <th style="width:110px">Date</th>
            <th>Uploaded datasets (versions)</th>
            <th style="width:120px" class="text-right">Progress</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in days" :key="d.date">
            <td>{{ d.date }}</td>
            <td>
              <v-chip
                v-for="ds in required"
                :key="ds"
                class="ma-1"
                :color="d.uploaded.includes(ds) ? 'green' : 'grey-lighten-2'"
                :text-color="d.uploaded.includes(ds) ? 'white' : 'black'"
                size="small"
                label
              >
                {{ label(ds) }}
                <span v-if="d.counts?.[ds]" class="ml-1">v{{ d.counts[ds] }}</span>
              </v-chip>
            </td>
            <td class="text-right">
              <v-progress-linear
                :model-value="d.total ? Math.round(d.done * 100 / d.total) : 0"
                height="10"
                color="primary"
                rounded
              />
            </td>
          </tr>
          <tr v-if="!days.length">
            <td colspan="3" class="text-center text-medium-emphasis py-6">
              No data
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '@/services/http'
import { useToast } from '@/ui/composables/useToast'

const { success, error } = useToast()

type DayRow = {
  date: string
  uploaded: string[]
  counts: Record<string, number>
  done: number
  total: number
  complete: boolean
}

const month = ref(new Date().toISOString().slice(0, 7))
const days = ref<DayRow[]>([])
const required = ref<string[]>([])

const labels: Record<string, string> = {
  rooms_status: '객실 현황',
  sales_front: 'Front 매출',
  fnb_sales: 'F&B 매출',
  expenses: '지출 내역',
  pay_settlement: '입금 내역',
}
const label = (k: string) => labels[k] ?? k

function shift(delta: number) {
  const [y, m] = month.value.split('-').map((n) => +n)
  const d = new Date(y, m - 1 + delta, 1)
  month.value = d.toISOString().slice(0, 7)
  load()
}

async function load() {
  try {
    const data = await http.get<{ from: string; to: string; required: string[]; days: DayRow[] }>(
      `/api/closing/calendar?month=${encodeURIComponent(month.value)}&property_code=MOP`
    )
    days.value = data?.days ?? []
    required.value = data?.required ?? []
    success('데이터를 불러왔습니다.')
  } catch {
    error('캘린더 로드 실패')
    days.value = []
    required.value = []
  }
}

onMounted(load)
</script>

<style scoped src="@/styles/toolbar.scss"></style>

<style scoped>
.page-shell {
  max-width: 1280px;
  margin: 0 auto;
}
.brand-panel {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(16, 24, 40, 0.06);
}
:deep(.v-table th) {
  background: #f9fafb;
  font-weight: 600;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
}
</style>
