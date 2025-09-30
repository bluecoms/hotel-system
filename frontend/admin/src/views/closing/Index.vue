<!-- src/views/closing/Index.vue -->
<template>
  <v-container class="py-6">
    <div class="d-flex align-center justify-space-between mb-3">
      <h2 class="text-h5">Closing</h2>
      <div class="text-caption text-medium-emphasis">property: {{ propertyCode }}</div>
    </div>

    <v-row class="mb-3" align="center">
      <v-col cols="12" md="6" class="d-flex align-center" style="gap:8px">
        <v-btn size="small" variant="text" icon="mdi-chevron-left" @click="moveMonth(-1)" />
        <v-text-field
          v-model="month"
          label="Month (YYYY-MM)"
          hide-details
          density="comfortable"
          style="max-width:180px"
        />
        <v-btn size="small" variant="text" icon="mdi-chevron-right" @click="moveMonth(1)" />
        <v-btn color="primary" class="ml-2" @click="load">LOAD</v-btn>
        <v-progress-circular
          v-if="loading"
          indeterminate
          size="18"
          class="ml-2"
        />
      </v-col>
      <v-col cols="12" md="6" class="d-flex justify-end">
        <div class="d-flex flex-wrap" style="gap:6px">
          <v-chip size="small" variant="outlined">rooms_status</v-chip>
          <v-chip size="small" variant="outlined">sales_front</v-chip>
          <v-chip size="small" variant="outlined">fnb_sales</v-chip>
          <v-chip size="small" variant="outlined">expenses</v-chip>
          <v-chip size="small" variant="outlined">pay_settlement</v-chip>
        </div>
      </v-col>
    </v-row>

    <v-alert v-if="err" type="warning" class="mb-4">
      캘린더 로드 실패
    </v-alert>

    <v-row>
      <!-- Calendar grid -->
      <v-col cols="12" md="8">
        <div class="text-subtitle-2 mb-2">Uploaded datasets (versions)</div>
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
                  {{ label(ds) }} <small>v{{ cell.day.counts?.[ds] ?? 1 }}</small>
                </div>
              </div>
              <div v-else class="day-body empty">
                <span class="muted">-</span>
              </div>
            </div>
          </div>
        </div>
      </v-col>

      <!-- Right detail -->
      <v-col cols="12" md="4">
        <v-card>
          <v-card-title class="d-flex align-center justify-space-between">
            <span>Selected: {{ selectedDate || '—' }}</span>
            <v-btn
              size="small"
              variant="tonal"
              @click="goBoard"
              :disabled="!selectedDate"
            >Upload Board</v-btn>
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
                      <v-icon size="18" v-if="(dayByDate[selectedDate]?.uploaded || []).includes(ds)" color="success">mdi-check-circle</v-icon>
                      <v-icon size="18" v-else color="grey">mdi-close-circle-outline</v-icon>
                    </td>
                  </tr>
                </tbody>
              </v-table>
              <div class="mt-3 text-caption text-medium-emphasis">
                완료도: {{ dayByDate[selectedDate]?.done ?? 0 }} / {{ dayByDate[selectedDate]?.total ?? required.length }}
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
import http from '@/services/http'

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

const month = ref(new Date().toISOString().slice(0,7)) // YYYY-MM
const loading = ref(false)
const err = ref(false)

const required = ref<string[]>([
  'rooms_status','sales_front','fnb_sales','expenses','pay_settlement'
])

const days = ref<Day[]>([])
const dayByDate = computed<Record<string, Day>>(() => {
  const m: Record<string, Day> = {}
  for (const d of days.value) m[d.date] = d
  return m
})

const selectedDate = ref<string | null>(null)

const weekHeaders = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']

function label(ds: string){
  switch (ds){
    case 'rooms_status': return 'Rooms'
    case 'sales_front': return 'Front'
    case 'fnb_sales': return 'F&B'
    case 'expenses': return 'Expenses'
    case 'pay_settlement': return 'Settlement'
    default: return ds
  }
}

function ymd(y:number, m:number, d:number){
  const mm = String(m).padStart(2,'0')
  const dd = String(d).padStart(2,'0')
  return `${y}-${mm}-${dd}`
}

function monthInfo(mstr:string){
  const [yS, mS] = mstr.split('-')
  const y = Number(yS), m = Number(mS)
  const first = new Date(y, m-1, 1)
  const lastDay = new Date(y, m, 0).getDate()
  const firstWeekday = first.getDay() // 0:Sun
  return { y, m, lastDay, firstWeekday }
}

const grid = computed(() => {
  // 6주(42칸) 그리드 (Sun~Sat)
  const g: Array<{
    inMonth: boolean
    dateNum: number | ''
    dateStr: string | null
    day: Day | null
  }> = []

  const { y, m, lastDay, firstWeekday } = monthInfo(month.value)

  // 앞쪽 빈칸
  for (let i=0; i<firstWeekday; i++){
    g.push({ inMonth:false, dateNum:'', dateStr:null, day:null })
  }
  // 본월
  for (let d=1; d<=lastDay; d++){
    const ds = ymd(y, m, d)
    g.push({
      inMonth:true,
      dateNum:d,
      dateStr:ds,
      day: dayByDate.value[ds] ?? null
    })
  }
  // 뒤쪽 채우기
  while (g.length % 7 !== 0) {
    g.push({ inMonth:false, dateNum:'', dateStr:null, day:null })
  }
  // 6주로 고정
  while (g.length < 42){
    g.push({ inMonth:false, dateNum:'', dateStr:null, day:null })
  }
  return g
})

async function load(){
  loading.value = true
  err.value = false
  try{
    const data = await http.get<CalResp>(
      `closing/calendar?month=${encodeURIComponent(month.value)}&property_code=${propertyCode}`
    )
    days.value = data?.days ?? []
    required.value = data?.required ?? required.value
    // 선택 날짜 초기화: 이번달에 오늘이 있으면 오늘, 아니면 첫째날
    const today = new Date().toISOString().slice(0,10)
    const inMonth = days.value.find(d => d.date === today)
    selectedDate.value = inMonth ? today : (days.value[0]?.date ?? null)
  }catch{
    days.value = []
    err.value = true
    selectedDate.value = null
  }finally{
    loading.value = false
  }
}

function moveMonth(delta:number){
  const [yS, mS] = month.value.split('-')
  let y = Number(yS), m = Number(mS)
  m += delta
  if (m <= 0){ y--; m += 12 }
  if (m > 12){ y++; m -= 12 }
  month.value = `${y}-${String(m).padStart(2,'0')}`
  load()
}

function onSelect(ds: string | null){
  if (!ds) return
  selectedDate.value = ds
}

function goBoard(){
  if (!selectedDate.value) return
  router.push({ path: '/closing/board', query: { date: selectedDate.value } })
}

onMounted(load)
</script>

<style scoped>
.calendar { display: grid; gap: 6px; }
.calendar-head {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
}
.calendar-body {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  grid-auto-rows: 120px;
  gap: 6px;
}
.cell {
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 10px;
  padding: 6px;
  background: rgb(var(--v-theme-surface));
}
.cell.head {
  text-align: center;
  font-weight: 600;
  padding: 8px 0;
  background: transparent;
  border: none;
}
.cell.day.is-other-month { opacity: .45; }
.cell.day.is-complete { border-color: rgb(var(--v-theme-success)); box-shadow: 0 0 0 1px rgba(var(--v-theme-success), .4) inset; }
.day-top {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;
}
.day-num { font-weight: 600; }
.day-body { display: flex; flex-wrap: wrap; gap: 4px; }
.day-body.empty { opacity: .4; }
.tag {
  font-size: 11px;
  border: 1px dashed rgba(0,0,0,0.15);
  border-radius: 6px;
  padding: 2px 6px;
}
.muted { color: rgba(0,0,0,0.38); }
</style>
