<template>
  <v-container fluid class="page-shell py-6">
    <div class="bar mb-6">
      <div class="bar-left">
        <v-icon color="primary" icon="mdi-view-dashboard-outline" size="22" />
        <h2 class="text-h6 font-weight-bold">마감 대시보드</h2>
        <span class="text-muted text-body-2">월별 업로드 현황</span>
      </div>
      <div class="bar-right d-flex align-center" style="gap:8px">
        <v-btn icon="mdi-chevron-left" variant="text" @click="moveMonth(-1)" />
        <v-text-field
          v-model="month"
          label="Month (YYYY-MM)"
          density="comfortable"
          hide-details
          style="max-width:160px"
        />
        <v-btn color="primary" prepend-icon="mdi-refresh" @click="load">불러오기</v-btn>
        <v-btn icon="mdi-chevron-right" variant="text" @click="moveMonth(1)" />
      </div>
    </div>

    <v-row>
      <v-col cols="12" md="8">
        <v-card class="brand-panel mb-4">
          <v-card-title class="font-weight-bold">업로드 현황 ({{ month }})</v-card-title>
          <v-divider />
          <div class="calendar">
            <div class="calendar-head">
              <div v-for="d in weekHeaders" :key="d" class="cell head">{{ d }}</div>
            </div>
            <div class="calendar-body">
              <div
                v-for="(cell, idx) in grid"
                :key="idx"
                class="cell day"
                :class="{
                  'is-other-month': !cell.inMonth,
                  'is-complete': cell.day?.complete
                }"
                @click="onSelect(cell.dateStr)"
              >
                <div class="day-top">
                  <span class="day-num">{{ cell.dateNum }}</span>
                </div>
                <div class="day-body" v-if="cell.day && cell.day.uploaded?.length">
                  <div
                    v-for="ds in cell.day.uploaded"
                    :key="ds"
                    class="tag"
                    :title="`${ds} v${cell.day.counts?.[ds] ?? 1}`"
                  >
                    {{ label(ds) }}
                    <small>v{{ cell.day.counts?.[ds] ?? 1 }}</small>
                  </div>
                </div>
                <div v-else class="day-body empty">
                  <span class="muted">-</span>
                </div>
              </div>
            </div>
          </div>
        </v-card>
      </v-col>

      <v-col cols="12" md="4">
        <v-card class="brand-panel">
          <v-card-title class="d-flex align-center justify-space-between">
            <span>선택일: {{ selectedDate || '—' }}</span>
            <v-btn
              size="small"
              variant="flat"
              color="primary"
              prepend-icon="mdi-open-in-new"
              @click="goBoard"
              :disabled="!selectedDate"
            >
              Upload Board
            </v-btn>
          </v-card-title>
          <v-divider />
          <v-card-text>
            <div v-if="!selectedDate" class="text-medium-emphasis">날짜를 선택하세요.</div>
            <template v-else>
              <v-table density="compact">
                <thead>
                  <tr>
                    <th>Dataset</th>
                    <th class="text-right" style="width:90px">Versions</th>
                    <th class="text-right" style="width:80px">Exists</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="ds in required" :key="ds">
                    <td>{{ label(ds) }} <span class="text-disabled text-caption">({{ ds }})</span></td>
                    <td class="text-right">
                      {{ dayByDate[selectedDate]?.counts?.[ds] ?? 0 }}
                    </td>
                    <td class="text-right">
                      <v-icon
                        size="18"
                        v-if="(dayByDate[selectedDate]?.uploaded || []).includes(ds)"
                        color="success"
                      >mdi-check-circle</v-icon>
                      <v-icon size="18" v-else color="grey">mdi-close-circle-outline</v-icon>
                    </td>
                  </tr>
                </tbody>
              </v-table>
              <div class="mt-3 text-caption text-medium-emphasis">
                완료도: {{ dayByDate[selectedDate]?.done ?? 0 }} /
                {{ dayByDate[selectedDate]?.total ?? required.length }}
              </div>
            </template>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/ui/composables/useToast'
import http from '@/services/http'

const { error, success } = useToast()

type Day = {
  date: string
  uploaded: string[]
  counts: Record<string, number>
  done: number
  total: number
  complete: boolean
}
type CalResp = {
  from: string
  to: string
  required: string[]
  property_code: string
  days: Day[]
}

const router = useRouter()
const propertyCode = 'MOP'

const month = ref(new Date().toISOString().slice(0, 7))
const loading = ref(false)

const required = ref<string[]>([])
const days = ref<Day[]>([])
const dayByDate = computed<Record<string, Day>>(() => {
  const m: Record<string, Day> = {}
  for (const d of days.value) m[d.date] = d
  return m
})
const selectedDate = ref<string | null>(null)
const weekHeaders = ['일', '월', '화', '수', '목', '금', '토']

function label(ds: string) {
  switch (ds) {
    case 'rooms_status': return '객실 현황'
    case 'sales_front': return 'Front 매출'
    case 'fnb_sales': return 'F&B 매출'
    case 'expenses': return '지출 내역'
    case 'pay_settlement': return '입금 내역'
    default: return ds
  }
}

function ymd(y: number, m: number, d: number) {
  const mm = String(m).padStart(2, '0')
  const dd = String(d).padStart(2, '0')
  return `${y}-${mm}-${dd}`
}

function monthInfo(mstr: string) {
  const [yS, mS] = mstr.split('-')
  const y = Number(yS), m = Number(mS)
  const first = new Date(y, m - 1, 1)
  const lastDay = new Date(y, m, 0).getDate()
  const firstWeekday = first.getDay()
  return { y, m, lastDay, firstWeekday }
}

const grid = computed(() => {
  const g: Array<{ inMonth: boolean; dateNum: number | ''; dateStr: string | null; day: Day | null }> = []
  const { y, m, lastDay, firstWeekday } = monthInfo(month.value)
  for (let i = 0; i < firstWeekday; i++) g.push({ inMonth: false, dateNum: '', dateStr: null, day: null })
  for (let d = 1; d <= lastDay; d++) {
    const ds = ymd(y, m, d)
    g.push({ inMonth: true, dateNum: d, dateStr: ds, day: dayByDate.value[ds] ?? null })
  }
  while (g.length % 7 !== 0) g.push({ inMonth: false, dateNum: '', dateStr: null, day: null })
  while (g.length < 42) g.push({ inMonth: false, dateNum: '', dateStr: null, day: null })
  return g
})

async function load() {
  loading.value = true
  try {
    const data = await http.get<CalResp>(
      `/api/closing/calendar?month=${encodeURIComponent(month.value)}&property_code=${propertyCode}`
    )
    days.value = data?.days ?? []
    required.value = data?.required ?? required.value
    const today = new Date().toISOString().slice(0, 10)
    const inMonth = days.value.find((d) => d.date === today)
    selectedDate.value = inMonth ? today : (days.value[0]?.date ?? null)
    success('캘린더를 불러왔습니다.')
  } catch {
    error('캘린더 로드 실패')
    days.value = []
    selectedDate.value = null
  } finally {
    loading.value = false
  }
}

function moveMonth(delta: number) {
  const [yS, mS] = month.value.split('-')
  let y = Number(yS), m = Number(mS)
  m += delta
  if (m <= 0) { y--; m += 12 }
  if (m > 12) { y++; m -= 12 }
  month.value = `${y}-${String(m).padStart(2, '0')}`
  load()
}

function onSelect(ds: string | null) {
  if (!ds) return
  selectedDate.value = ds
}

function goBoard() {
  if (!selectedDate.value) return
  router.push({ path: '/closing/board', query: { date: selectedDate.value } })
}

onMounted(load)
</script>

<style scoped src="@/styles/toolbar.scss"></style>

<style scoped>
.page-shell { max-width: 1280px; margin: 0 auto; }
.brand-panel {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(16, 24, 40, 0.06);
}

/* calendar */
.calendar { display: grid; gap: 6px; }
.calendar-head { display: grid; grid-template-columns: repeat(7, 1fr); }
.calendar-body { display: grid; grid-template-columns: repeat(7, 1fr); grid-auto-rows: 120px; gap: 6px; }
.cell { border: 1px solid #e5e7eb; border-radius: 10px; padding: 6px; background: #fff; transition: 0.15s; }
.cell.head { text-align: center; font-weight: 600; padding: 8px 0; background: #f9fafb; border: none; }
.cell.day:hover { transform: translateY(-2px); box-shadow: 0 2px 8px rgba(0,0,0,0.08); cursor:pointer; }
.cell.day.is-other-month { opacity: .45; }
.cell.day.is-complete { border-color: #22c55e; box-shadow: 0 0 0 1px rgba(34,197,94,0.3) inset; }
.day-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; }
.day-num { font-weight: 600; }
.day-body { display:flex; flex-wrap:wrap; gap:4px; }
.day-body.empty { opacity:.4; }
.tag { font-size:11px; border:1px dashed #9ca3af; border-radius:6px; padding:2px 6px; background:#f9fafb; }
.muted { color: #9ca3af; }
</style>
