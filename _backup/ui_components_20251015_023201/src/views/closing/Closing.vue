<template>
  <v-container fluid class="page-shell py-6">
    <div class="bar brand-panel mb-5 d-flex align-center justify-space-between flex-wrap">
      <div class="bar-left d-flex align-center flex-wrap gap8">
        <v-breadcrumbs
          :items="[{ title:'마감 관리', disabled:true }, { title:'마감 캘린더', disabled:true }]"
          class="pa-0 ma-0"
        />
        <v-chip size="small" variant="outlined">
          Property: {{ propertyCode }}
        </v-chip>
        <v-chip size="small" variant="tonal">
          Range: {{ from }} ~ {{ to }}
        </v-chip>
      </div>

      <div class="bar-right d-flex align-center gap8 mt-2 mt-sm-0">
        <v-btn variant="text" icon="mdi-chevron-left" @click="shift(-1)" />
        <v-text-field
          v-model="month"
          label="Month (YYYY-MM)"
          variant="outlined"
          density="comfortable"
          class="month-input"
          hide-details
          @keyup.enter="load"
        />
        <v-btn color="primary" :loading="loading" class="btn-action" @click="load">불러오기</v-btn>
        <v-btn variant="text" icon="mdi-chevron-right" @click="shift(1)" />
      </div>
    </div>

    <div class="brand-panel legend pa-3 mb-4">
      <div class="legend-row">
        <div class="legend-item">
          <span class="legend-chip open">OPEN</span>
          <span class="legend-text">마감 안함</span>
        </div>
        <div class="legend-item">
          <span class="legend-chip closed">CLOSED</span>
          <span class="legend-text">마감 완료</span>
        </div>
        <div class="legend-item">
          <span class="legend-swatch uploaded" />
          <span class="legend-text">파트 업로드 완료</span>
        </div>
        <div class="legend-item">
          <span class="legend-swatch missing" />
          <span class="legend-text">파트 누락</span>
        </div>
      </div>
    </div>

    <v-alert v-if="err" type="warning" class="mb-3">{{ err }}</v-alert>

    <div class="week-head">
      <div
        v-for="(w, idx) in WEEK_LABELS"
        :key="w"
        class="week-cell"
        :class="{'sun':idx===0,'sat':idx===6}"
      >
        {{ w }}
      </div>
    </div>

    <div class="cal-grid">
      <div v-for="(wk, wi) in weeks" :key="wi" class="week-row">
        <v-card
          v-for="c in wk"
          :key="c.dateStr"
          class="day-card"
          variant="outlined"
          :class="[
            c.inMonth ? '' : 'other-month',
            c.weekday===0 ? 'is-sun' : (c.weekday===6 ? 'is-sat' : ''),
            isToday(c.dateStr) ? 'is-today' : '',
            c.day ? statusClass(c.day) : ''
          ]"
          :ripple="false"
          :tabindex="c.inMonth ? 0 : -1"
          :aria-disabled="!c.inMonth"
          @click="c.inMonth && onSelect(c)"
        >
          <div class="day-top">
            <div class="date-num">{{ c.dateNum }}</div>

            <v-chip
              v-if="c.day"
              :color="c.day.status==='CLOSED' ? 'red' : 'blue'"
              size="x-small"
              label
              variant="flat"
              class="status-chip"
            >
              {{ c.day.status }}
            </v-chip>
          </div>

          <div class="chips" v-if="c.day">
            <v-chip
              v-for="ds in required"
              :key="ds"
              size="x-small"
              :variant="c.day.uploaded.includes(ds) ? 'flat' : 'outlined'"
              :class="c.day.uploaded.includes(ds) ? 'chip--uploaded' : 'chip--missing'"
              :color="c.day.uploaded.includes(ds) ? 'green' : 'grey'"
              label
              class="chip"
            >
              {{ label(ds) }}
              <span v-if="c.day.counts?.[ds]" class="vtag">v{{ c.day.counts[ds] }}</span>
            </v-chip>
          </div>

          <div v-if="c.day" class="mt-2">
            <v-progress-linear
              :model-value="pct(c.day)"
              height="8"
              rounded
              color="primary"
              class="prog"
            />
            <div class="prog-text">
              {{ c.day.done }}/{{ c.day.total }} ({{ Math.round(pct(c.day)) }}%)
            </div>
          </div>

          <div v-if="!c.inMonth" class="badge-other">다른 월</div>

          <div v-if="isSuper && c.day && c.inMonth" class="day-actions">
            <v-btn
              v-if="c.day.status==='OPEN'"
              size="x-small"
              color="red"
              variant="text"
              @click.stop="setStatus(c.dateStr,'CLOSED')"
            >
              Close
            </v-btn>
            <v-btn
              v-else
              size="x-small"
              color="blue"
              variant="text"
              @click.stop="setStatus(c.dateStr,'OPEN')"
            >
              Reopen
            </v-btn>
          </div>
        </v-card>
      </div>
    </div>

    <UploadNeedDialog
      v-model="needOpen"
      :items="needItems"
      @goto="(anchor: string) => router.push({ path: '/closing/board', query: { date: selDate, anchor } })"
    />
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/ui/composables/useToast'
import { getClosingCalendar, setClosingDayStatus, type ClosingDay } from '@/services/closing'
import { useAuthStore } from '@/stores/auth'
import UploadNeedDialog from './UploadNeedDialog.vue'

const router = useRouter()
const auth = useAuthStore()
const { error: toastError, success: toastOk } = useToast()

const propertyCode = 'MOP'
const month = ref(new Date().toISOString().slice(0, 7))
const from = ref('')
const to = ref('')
const required = ref<string[]>([])
const days = ref<ClosingDay[]>([])
const loading = ref(false)
const err = ref<string | null>(null)

const isSuper = computed(
  () => !!(auth as any)?.hasRole?.('SUPERADMIN') || auth.user?.roles?.includes('SUPERADMIN')
)

const WEEK_LABELS = ['일', '월', '화', '수', '목', '금', '토']

const labels: Record<string, string> = {
  rooms_status: '객실',
  sales_front: '매출',
  fnb_sales: 'F&B',
  expenses: '출금',
  pay_settlement: '입금',
}
const label = (k: string) => labels[k] ?? k

function ymd(dt: Date) {
  const y = dt.getFullYear()
  const m = String(dt.getMonth() + 1).padStart(2, '0')
  const d = String(dt.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

const dayByDate = computed<Record<string, ClosingDay>>(() => {
  const m: Record<string, ClosingDay> = {}
  for (const d of days.value) m[d.date] = d
  return m
})

type Cell = { dateStr: string; dateNum: number; inMonth: boolean; weekday: number; day?: ClosingDay }
const grid = computed<Cell[]>(() => {
  const [y, m] = month.value.split('-').map(n => +n)
  const first = new Date(y, m - 1, 1)
  const firstW = first.getDay()
  const lastThis = new Date(y, m, 0).getDate()
  const prevMonthLast = new Date(y, m - 1, 0).getDate()

  const cells: Cell[] = []
  for (let i = firstW - 1; i >= 0; i--) {
    const num = prevMonthLast - i
    const dt = new Date(y, m - 2, num)
    cells.push({ dateStr: ymd(dt), dateNum: num, inMonth: false, weekday: dt.getDay() })
  }
  for (let d = 1; d <= lastThis; d++) {
    const dt = new Date(y, m - 1, d)
    const ds = ymd(dt)
    cells.push({ dateStr: ds, dateNum: d, inMonth: true, weekday: dt.getDay(), day: dayByDate.value[ds] })
  }
  while (cells.length % 7 !== 0) {
    const last = cells[cells.length - 1]
    const dt = new Date(last.dateStr)
    dt.setDate(dt.getDate() + 1)
    cells.push({ dateStr: ymd(dt), dateNum: dt.getDate(), inMonth: false, weekday: dt.getDay() })
  }
  return cells
})

const weeks = computed<Cell[][]>(() => {
  const out: Cell[][] = []
  for (let i = 0; i < grid.value.length; i += 7) out.push(grid.value.slice(i, i + 7))
  return out
})

function isToday(ds: string) {
  return ds === ymd(new Date())
}

function shift(delta: number) {
  const [y, m] = month.value.split('-').map(n => +n)
  let nm = m + delta,
    ny = y
  if (nm < 1) {
    nm += 12
    ny -= 1
  }
  if (nm > 12) {
    nm -= 12
    ny += 1
  }
  month.value = `${ny}-${String(nm).padStart(2, '0')}`
  load()
}

async function load() {
  loading.value = true
  err.value = null
  try {
    const res = await getClosingCalendar({ month: month.value, property_code: propertyCode })
    from.value = (res as any).from
    to.value = (res as any).to
    required.value = (res as any).required || []
    days.value = (res as any).days || []
  } catch (e: any) {
    err.value = e?.detail ?? e?.message ?? '캘린더 로드 실패'
    days.value = []
    required.value = []
  } finally {
    loading.value = false
  }
}

function pct(r: ClosingDay) {
  return r.total ? (r.done * 100) / r.total : 0
}
function statusClass(r: ClosingDay) {
  return r.status === 'CLOSED' ? 'is-closed' : 'is-open'
}

const needOpen = ref(false)
const needItems = ref<string[]>([])
const selDate = ref('')
function onSelect(c: Cell) {
  if (!c.inMonth || !c.day) return
  selDate.value = c.dateStr
  const missing = required.value.filter(ds => !c.day!.uploaded.includes(ds))
  needItems.value = missing
  if (missing.length) needOpen.value = true
}

async function setStatus(date: string, status: 'OPEN' | 'CLOSED') {
  try {
    await setClosingDayStatus({ date, status, property_code: propertyCode })
    await load()
    toastOk(status === 'CLOSED' ? '해당 영업일 마감' : '해당 영업일 재오픈')
  } catch (e: any) {
    toastError(e?.detail ?? e?.message ?? '상태 변경 실패')
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

/* ✅ 통일 스타일 */
.brand-panel {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(16, 24, 40, 0.06);
}

/* 범례 */
.legend-row {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  align-items: baseline;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.legend-text {
  font-size: 0.9rem;
  opacity: 0.9;
}
.legend-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.72rem;
  padding: 2px 8px;
  border-radius: 999px;
  color: #fff;
}
.legend-chip.open {
  background: #3b82f6;
}
.legend-chip.closed {
  background: #ef4444;
}
.legend-swatch {
  display: inline-block;
  width: 16px;
  height: 10px;
  border-radius: 3px;
  border: 1px solid #9ca3af;
}
.legend-swatch.uploaded {
  background: #22c55e;
}
.legend-swatch.missing {
  background: rgba(120, 120, 120, 0.25);
}

/* 주차 헤더 */
.week-head {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
  margin: 8px 0 6px;
  font-weight: 700;
  color: #6b7280;
  text-align: center;
}
.week-cell.sun {
  color: #ef4444;
}
.week-cell.sat {
  color: #2563eb;
}

/* 달력 카드 */
.cal-grid {
  display: grid;
  grid-template-rows: repeat(6, minmax(120px, 1fr));
  gap: 8px;
}
.week-row {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
}
.day-card {
  min-height: 150px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  border-radius: 12px;
  background: linear-gradient(180deg, #ffffff, #fbfbfd);
  border-color: #e5e7eb;
  transition: 0.15s ease box-shadow, 0.05s ease transform;
}
.day-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(16, 24, 40, 0.08);
}
.day-card.other-month {
  pointer-events: none;
  filter: grayscale(0.35) brightness(0.94);
  opacity: 0.7;
  position: relative;
}
.badge-other {
  position: absolute;
  right: 8px;
  bottom: 8px;
  font-size: 0.72rem;
  padding: 2px 8px;
  border-radius: 999px;
  background: #4b5563;
  color: white;
}

/* 상태별 톤 */
.day-card.is-closed {
  border-color: #fca5a5;
  background: linear-gradient(180deg, #fff7f7, #fff1f1);
}
.day-card.is-open {
  border-color: #bfdbfe;
  background: linear-gradient(180deg, #fbfdff, #f5f9ff);
}

/* 오늘 표시 */
.day-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.date-num {
  font-weight: 800;
  font-size: 0.98rem;
  text-align: center;
  width: 2.5rem;
  color: #111827;
}
.day-card.is-sun .date-num {
  color: #ef4444;
  font-weight: 900;
}
.day-card.is-sat .date-num {
  color: #2563eb;
  font-weight: 900;
}
.day-card.is-today {
  box-shadow: 0 0 0 2px #2563eb inset, 0 0 0 2px rgba(37, 99, 235, 0.35);
  background: linear-gradient(180deg, #ffffff, #f5f9ff);
}

/* 칩 / 진행바 */
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}
.chip {
  --v-chip-height: 22px;
}
.status-chip {
  font-weight: 700;
}
.chip--uploaded :deep(.v-chip__content) {
  font-weight: 600;
}
.chip--missing :deep(.v-chip__content) {
  color: #6b7280 !important;
}
.chip--missing :deep(.v-chip__underlay) {
  opacity: 0.15;
  border: 1px dashed #9ca3af !important;
}
.vtag {
  margin-left: 4px;
  opacity: 0.9;
  font-weight: 700;
}
.prog {
  background-color: rgba(148, 163, 184, 0.25);
}
.prog :deep(.v-progress-linear__determinate) {
  background-color: #2563eb !important;
  opacity: 0.9;
}
.prog :deep(.v-progress-linear__determinate) {
  background-color: #2563eb !important;
  opacity: 0.9;
}

.prog-text {
  font-size: 0.8rem;
  color: #374151;
  margin-top: 4px;
  text-align: right;
}

.day-actions {
  margin-top: auto;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

/* 반응형 */
@media (max-width: 1280px) {
  .week-row {
    grid-template-columns: repeat(4, 1fr);
  }
  .week-head {
    grid-template-columns: repeat(4, 1fr);
  }
}
@media (max-width: 720px) {
  .week-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .week-head {
    display: none;
  }
}
</style>