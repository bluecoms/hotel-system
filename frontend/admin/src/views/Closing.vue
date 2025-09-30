<template>
  <v-container class="py-6">
    <!-- 상단 경로/툴바 -->
    <div class="d-flex align-center justify-space-between mb-4 gap12">
      <div class="d-flex align-center gap12">
        <v-breadcrumbs :items="[
          { title: 'Dashboard', disabled: false, href: '#' },
          { title: 'Closing', disabled: true }
        ]" class="mr-2" />
        <h2 class="text-h5">Closing</h2>
        <v-chip size="small" variant="outlined" class="ml-1">Property: {{ propertyCode }}</v-chip>
      </div>

      <div class="d-flex align-center gap8">
        <v-btn variant="text" @click="shift(-1)">◀</v-btn>
        <v-text-field
          v-model="month"
          label="Month (YYYY-MM)"
          density="comfortable"
          style="max-width: 140px"
          @keyup.enter="load"
        />
        <v-btn color="primary" @click="load">LOAD</v-btn>
        <v-btn variant="text" @click="shift(1)">▶</v-btn>
      </div>
    </div>

    <v-alert v-if="err" type="warning" class="mb-4">{{ err }}</v-alert>

    <!-- 요일 헤더 -->
    <div class="week-head">
      <div v-for="w in WEEK_LABELS" :key="w" class="week-cell">{{ w }}</div>
    </div>

    <!-- 달력 그리드 -->
    <div class="cal-grid">
      <div v-for="(wk, wi) in weeks" :key="wi" class="week-row">
        <v-card
          v-for="cell in wk"
          :key="cell.dateStr"
          class="day-card"
          variant="outlined"
          :class="[{ 'muted': !cell.inMonth }, statusClass(cell.row)]"
        >
          <!-- 상단 -->
          <div class="day-top">
            <div class="date-num">{{ cell.date.getDate() }}</div>
            <v-chip
              v-if="cell.row"
              :color="cell.row.status === 'CLOSED' ? 'red' : 'blue'"
              size="x-small"
              label
              class="status-chip"
              variant="flat"
            >
              {{ cell.row.status }}
            </v-chip>
          </div>

          <!-- 데이터셋 칩 -->
          <div class="chips">
            <v-chip
              v-for="ds in required"
              :key="ds"
              size="x-small"
              :variant="cell.row && cell.row.uploaded.includes(ds) ? 'flat' : 'outlined'"
              :color="cell.row && cell.row.uploaded.includes(ds) ? 'green' : undefined"
              label
              class="chip"
            >
              {{ label(ds) }}
              <span v-if="cell.row && cell.row.counts?.[ds]" class="vtag">v{{ cell.row.counts[ds] }}</span>
            </v-chip>
          </div>

          <!-- 진행도 -->
          <div v-if="cell.row" class="mt-2">
            <v-progress-linear
              :model-value="pct(cell.row)"
              height="8"
              rounded
              color="primary"
            />
            <div class="prog-text">{{ cell.row.done }}/{{ cell.row.total }} ({{ Math.round(pct(cell.row)) }}%)</div>
          </div>

          <!-- 상태 토글 -->
          <div v-if="cell.row && auth?.hasRole && auth.hasRole('SUPERADMIN')" class="day-actions">
            <v-btn
              v-if="cell.row.status === 'OPEN'"
              size="x-small" color="red" variant="text"
              @click="setStatus(cell.dateStr, 'CLOSED')"
            >Close</v-btn>
            <v-btn
              v-else
              size="x-small" color="blue" variant="text"
              @click="setStatus(cell.dateStr, 'OPEN')"
            >Reopen</v-btn>
          </div>
        </v-card>
      </div>
    </div>

    <div v-if="!days.length" class="text-center text-medium-emphasis py-6">No data</div>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import http from '@/services/http'
import { useAuthStore } from '@/stores/auth'

type DayRow = {
  date: string
  uploaded: string[]
  counts: Record<string, number>
  done: number
  total: number
  complete: boolean
  status: 'OPEN' | 'CLOSED'
}

type DayCell = {
  date: Date
  dateStr: string
  inMonth: boolean
  row?: DayRow
}

const propertyCode = 'MOP'
const month = ref(new Date().toISOString().slice(0,7)) // YYYY-MM
const days  = ref<DayRow[]>([])
const required = ref<string[]>([])
const err = ref<string | null>(null)
const auth = useAuthStore()

const labels: Record<string,string> = {
  rooms_status: 'Rooms',
  sales_front:  'Front',
  fnb_sales:    'F&B',
  expenses:     'Expenses',
  pay_settlement:'Settlement',
}
const label = (k:string) => labels[k] ?? k

function shift(delta:number){
  const [y,m] = month.value.split('-').map(n=>+n)
  const d = new Date(y, m-1+delta, 1)
  month.value = d.toISOString().slice(0,7)
  load()
}

async function load(){
  err.value = null
  try{
    const data = await http.get<{from:string;to:string;required:string[];days:DayRow[]}>(
      `closing/calendar?month=${encodeURIComponent(month.value)}&property_code=${propertyCode}`
    )
    days.value = data?.days ?? []
    required.value = data?.required ?? []
  }catch{
    err.value = '캘린더 로드 실패'
    days.value = []
    required.value = []
  }
}

async function setStatus(date:string, status:'OPEN'|'CLOSED'){
  try{
    const fd = new FormData()
    fd.append('date', date)
    fd.append('status', status)
    fd.append('property_code', propertyCode)
    await http.put('closing/day', fd)
    await load()
  }catch{
    alert('상태 변경 실패')
  }
}

const WEEK_LABELS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']

// 해당 월 1일
const firstDayOfMonth = computed(() => {
  const [y,m] = month.value.split('-').map(n => +n)
  return new Date(y, m-1, 1)
})

const byDate = computed(() => {
  const m = new Map<string, DayRow>()
  for (const d of days.value) m.set(d.date, d)
  return m
})

const weeks = computed<DayCell[][]>(() => {
  const first = firstDayOfMonth.value
  const year = first.getFullYear()
  const mon  = first.getMonth()

  // 시작은 그 주의 일요일
  const start = new Date(year, mon, 1)
  const startOffset = start.getDay()
  start.setDate(start.getDate() - startOffset)

  const out: DayCell[][] = []
  for (let w=0; w<6; w++){
    const row: DayCell[] = []
    for (let d=0; d<7; d++){
      const cur = new Date(start)
      cur.setDate(start.getDate() + w*7 + d)
      const ds = cur.toISOString().slice(0,10)
      row.push({
        date: cur,
        dateStr: ds,
        inMonth: cur.getMonth() === mon,
        row: byDate.value.get(ds)
      })
    }
    out.push(row)
  }
  return out
})

function pct(r: DayRow){
  return r.total ? (r.done * 100 / r.total) : 0
}

function statusClass(r?: DayRow){
  if (!r) return null
  return r.status === 'CLOSED' ? 'is-closed' : 'is-open'
}

onMounted(load)
</script>

<style scoped>
.gap8{gap:8px} .gap12{gap:12px}

/* 요일 헤더 */
.week-head{
  display:grid; grid-template-columns:repeat(7,1fr);
  gap:8px; margin-bottom:6px;
}
.week-cell{ text-align:center; font-weight:700; color:var(--ink-3); }

/* 캘린더 그리드 */
.cal-grid{ display:grid; grid-template-rows:repeat(6,1fr); gap:8px; }
.week-row{ display:grid; grid-template-columns:repeat(7,1fr); gap:8px; }

.day-card{
  min-height:150px; padding:10px;
  display:flex; flex-direction:column; justify-content:flex-start;
  border-radius:12px; transition:.15s transform ease,.2s box-shadow ease;
}
.day-card:hover{ transform:translateY(-2px); box-shadow:var(--shadow-2); }

.day-card.is-closed{ border-color:#ffd9d9; background:#fff8f8 }
.day-card.is-open  { border-color:#dbeafe; background:#fbfdff }
.day-card.muted    { opacity:.55; background:#fafbfe }

/* 상단 */
.day-top{ display:flex; align-items:center; justify-content:space-between; }
.date-num{ font-weight:800; font-size:.98rem; }
.status-chip{ margin-left:6px }

/* 칩 */
.chips{ display:flex; flex-wrap:wrap; gap:6px; margin-top:8px; }
.chip{ --v-chip-height:22px; }
.vtag{ margin-left:4px; opacity:.8; font-weight:600; }

/* 진행도 */
.prog-text{ font-size:.78rem; color:var(--ink-3); margin-top:4px; text-align:right; }

/* 액션 */
.day-actions{ margin-top:auto; display:flex; gap:8px; justify-content:flex-end; }

/* 반응형 */
@media (max-width:1200px){ .week-row{grid-template-columns:repeat(4,1fr)} .week-head{grid-template-columns:repeat(4,1fr)} }
@media (max-width:720px){ .week-row{grid-template-columns:repeat(2,1fr)} .week-head{display:none} }
</style>
