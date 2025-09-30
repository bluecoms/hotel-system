<template>
  <div class="dash-wrap">
    <!-- Toolbar -->
    <div class="toolbar panel">
      <div class="left row">
        <label class="lbl">Property</label>
        <select v-model="propertyCode">
          <option v-for="p in propertyOptions" :key="p" :value="p">{{ p }}</option>
        </select>

        <span class="sep" />

        <label class="lbl">Business Date</label>
        <Button variant="ghost" size="sm" @click="shiftDay(-1)">‹</Button>
        <input type="date" v-model="bizDate" />
        <Button variant="ghost" size="sm" @click="shiftDay(1)">›</Button>
        <Button variant="outline" size="sm" @click="setToday">Today</Button>
      </div>

      <div class="space" />

      <!-- Closing status block -->
      <div class="right row">
        <Tooltip :text="closingTooltip" placement="bottom">
          <Badge :class="closingBadgeClass">
            <template v-if="closing.status==='CLOSED'">CLOSED</template>
            <template v-else>OPEN · {{ closing.done }}/{{ closing.total }}</template>
          </Badge>
        </Tooltip>
        <div class="progress-wrap">
          <ProgressBar :percent="closingPercent" />
        </div>
        <Button variant="solid" size="sm" @click="fetchAll">Refresh</Button>
      </div>
    </div>

    <!-- KPI grid -->
    <div class="top-grid">
      <KpiCard
        title="Rooms"
        :value="`${rooms.occ}/${totalRooms}`"
        :sub="`Sold ${rooms.sold}, Stay ${rooms.stay}`"
      >
        <div class="rooms-row">
          <ProgressRing :percent="roomsPct" :size="96" />
          <div class="chips">
            <span class="tag">Sold {{ rooms.sold }}</span>
            <span class="tag">Stay {{ rooms.stay }}</span>
            <span class="tag">Arrivals {{ rooms.arrivals }}</span>
            <span class="tag">Departures {{ rooms.departures }}</span>
          </div>
        </div>
      </KpiCard>

      <KpiCard title="Front Sales" :value="front.v" prefix="₩" />
      <KpiCard title="F&B Sales"    :value="fnb.v"   prefix="₩" />
      <KpiCard title="Expenses"     :value="exp.v"   prefix="₩" />
      <KpiCard title="Settlement"   :value="pay.v"   prefix="₩" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import KpiCard from '@/ui/KpiCard.vue'
import ProgressRing from '@/ui/ProgressRing.vue'
import Button from '@/ui/Button.vue'
import Badge from '@/ui/Badge.vue'
import Tooltip from '@/ui/Tooltip.vue'
import ProgressBar from '@/ui/ProgressBar.vue'

/** 호텔별 객실 수 */
const ROOMS_BY_PROPERTY: Record<string, number> = {
  MOP: 170,
  // 다른 호텔 있으면 추가
}

const propertyOptions = ref<string[]>(Object.keys(ROOMS_BY_PROPERTY))
const route = useRoute()
const router = useRouter()

function toYMD(d: Date) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${dd}`
}
function parseYMD(s: string) {
  const [y, m, d] = (s || '').split('-').map(Number)
  return new Date(y || 1970, (m || 1) - 1, d || 1)
}

const propertyCode = ref<string>(
  (route.query.property_code as string) || localStorage.getItem('__property') || 'MOP'
)
watch(propertyCode, (v) => localStorage.setItem('__property', v))

const bizDate = ref<string>((route.query.date as string) || toYMD(new Date()))

function syncUrl() {
  router.replace({ query: { ...route.query, date: bizDate.value, property_code: propertyCode.value } })
}
watch([bizDate, propertyCode], () => { syncUrl(); fetchAll() })
watch(() => route.query.date, (v) => { if (typeof v==='string' && v && v!==bizDate.value) bizDate.value = v })
watch(() => route.query.property_code, (v) => { if (typeof v==='string' && v && v!==propertyCode.value) propertyCode.value = v })

const totalRooms = computed(() => ROOMS_BY_PROPERTY[propertyCode.value] ?? 0)

/** Rooms KPI */
const rooms = reactive({ occ: 0, sold: 0, stay: 0, arrivals: 0, departures: 0 })
const roomsPct = computed(() => totalRooms.value ? (rooms.occ / totalRooms.value) * 100 : 0)
const front = reactive({ v: 0 }); const fnb = reactive({ v: 0 })
const exp   = reactive({ v: 0 }); const pay = reactive({ v: 0 })

/** Closing status */
const closing = reactive({ status: 'OPEN', done: 0, total: 5, complete: false })
const closingPercent = computed(() => closing.total ? Math.round((closing.done/closing.total)*100) : 0)
const closingBadgeClass = computed(() => ({
  success: closing.status === 'CLOSED',
  warn: closing.status !== 'CLOSED' && closingPercent.value >= 60,
  danger: closing.status !== 'CLOSED' && closingPercent.value < 60
}))
const closingTooltip = computed(() =>
  closing.status === 'CLOSED'
    ? '마감 완료'
    : `진행 ${closing.done}/${closing.total} (${closingPercent.value}%)`
)

/** 날짜 이동 */
function shiftDay(delta: number) {
  const d = parseYMD(bizDate.value); d.setDate(d.getDate() + delta); bizDate.value = toYMD(d)
}
function setToday(){ bizDate.value = toYMD(new Date()) }

/** Fetchers */
async function fetchKpi() {
  const qs = new URLSearchParams({ date: bizDate.value, property_code: propertyCode.value })
  const res = await fetch(`/api/reports/dashboard-kpi?${qs}`, {
    headers: { 'X-Internal-Token': localStorage.getItem('__token') || '' }
  })
  const data = await res.json()
  const cards: Array<{ key: string; value: any }> = data.cards || []
  // Rooms
  const rc = cards.find(c => c.key === 'rooms')
  let occ=0, sold=0, stay=0, arr=0, dep=0
  if (rc) {
    if (rc.value && typeof rc.value === 'object') {
      occ  = Number(rc.value.occ || 0)
      sold = Number(rc.value.sold ?? occ)
      stay = Number(rc.value.stay || 0)
      arr  = Number(rc.value.arrivals || 0)
      dep  = Number(rc.value.departures || 0)
    } else if (typeof rc?.value === 'string') {
      const nums = (rc.value as string).match(/\d+/g)?.map(Number) || []
      occ = nums[0] || 0; sold = nums[0] || 0
    }
  }
  rooms.occ = occ; rooms.sold = sold; rooms.stay = stay; rooms.arrivals = arr; rooms.departures = dep
  // 숫자 카드
  const getNum = (k: string) => Number(cards.find(c => c.key===k)?.value ?? 0)
  front.v = getNum('front'); fnb.v = getNum('fnb'); exp.v = getNum('exp'); pay.v = getNum('pay')
}

async function fetchClosing() {
  const qs = new URLSearchParams({ date: bizDate.value, property_code: propertyCode.value })
  const res = await fetch(`/api/closing/day?${qs}`, {
    headers: { 'X-Internal-Token': localStorage.getItem('__token') || '' }
  })
  const data = await res.json().catch(()=> ({}))
  closing.status = (data.status || 'OPEN').toUpperCase()
  closing.done = Number(data.done ?? 0)
  closing.total = Number(data.total ?? 5)
  closing.complete = Boolean(data.complete)
}

async function fetchAll() {
  await Promise.all([fetchKpi(), fetchClosing()])
}

onMounted(() => { syncUrl(); fetchAll() })
</script>

<style scoped>
/* Dashboard.vue <style scoped> 교체 */
.dash-wrap{ display:flex; flex-direction:column; gap:16px; padding:8px }
.toolbar.panel{ padding:12px 14px; display:flex; align-items:center; gap:12px; }
.left .lbl{ font-size:.92rem; color:var(--ink-3) }
.sep{ display:inline-block; width:10px }
.progress-wrap{ width:140px }

.top-grid{ display:grid; grid-template-columns:2fr 1fr 1fr 1fr 1fr; gap:16px }
@media (max-width:1200px){ .top-grid{ grid-template-columns:repeat(3,minmax(0,1fr)) } }
@media (max-width:800px){ .top-grid{ grid-template-columns:1fr } }

.rooms-row{ display:flex; align-items:center; gap:16px }
.chips{ display:flex; gap:8px; flex-wrap:wrap }
.tag{ padding:.2rem .55rem; border-radius:999px; background:#f3f4f6; font-size:.8rem; color:#374151 }
</style>
