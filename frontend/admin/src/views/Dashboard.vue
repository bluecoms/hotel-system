<!--
===============================================================
 Hotel Admin — Dashboard View (v2025.10 Final / business_date Server Source)
---------------------------------------------------------------
 목적:
  - 접속 시 KPI·Bank 요약 및 마감 상태(Closing) 요약 표시
  - SmartFilterBar + BizDatePicker 로 날짜·속성 제어
  - ⚠️ 프런트는 날짜를 "계산"하지 않음(하루/월 이동 연산 금지)
    → 서버가 산출한 business_date만 사용/표시
---------------------------------------------------------------
 주요 수정 (2025-10-20):
  ✅ 초기값/리셋: 서버 `/closing/day?property_code=...` (date 없이)로 business_date 획득
  ✅ KPI: `/reports/dashboard-kpi?property_code=...&business_date=<서버값>`
  ✅ Closing: `/closing/day?property_code=...` (기본) 또는 `&date=<서버값>` 동기화
  ✅ 프런트 new Date()/toISOString() 등 날짜 계산 제거
  ✅ Debounce 로드 및 watch 안정화
===============================================================
-->

<template>
  <PageShell title="Dashboard" icon="mdi-view-dashboard">
    <!-- ───────────────────────── Toolbar ───────────────────────── -->
    <template #toolbar>
      <SmartFilterBar
        v-model:property="propertyCode"
        :property-options="propertyOptions"
        @search="fetchAll"
        @reset="resetToServerBizDate"
      >
        <!-- 날짜 제어: BizDatePicker는 서버에서 받은 business_date만 바인딩하여 표시 -->
        <template #filters>
          <BizDatePicker v-model="bizDate" mode="day" />
        </template>

        <!-- 상태칩 / 진행률 / 새로고침 -->
        <template #extra>
          <v-chip
            :color="closing.status === 'CLOSED' ? 'green' : 'orange'"
            label
            class="ml-3"
          >
            <template v-if="closing.status === 'CLOSED'">CLOSED</template>
            <template v-else>OPEN · {{ closing.done }}/{{ closing.total }}</template>
          </v-chip>

          <div class="progress-wrap">
            <v-progress-linear
              :model-value="Math.round(closingPercent)"
              height="8"
              rounded
              color="primary"
            />
          </div>

          <v-btn color="primary" size="small" @click="fetchAll">Refresh</v-btn>
        </template>
      </SmartFilterBar>
    </template>

    <!-- ───────────────────────── KPI Cards ───────────────────────── -->
    <div class="top-grid">
      <KpiCard title="Room Only" :value="kpi?.room_only_amount ?? 0" prefix="₩" />
      <KpiCard title="Package"   :value="kpi?.package_amount   ?? 0" prefix="₩" />
      <KpiCard title="Other"     :value="kpi?.other_amount     ?? 0" prefix="₩" />
      <KpiCard title="Total"     :value="totalAmount"               prefix="₩" />
    </div>

    <!-- ─────────────────────── Bank & Cash ─────────────────────── -->
    <v-card class="panel">
      <v-card-title class="d-flex align-center justify-space-between">
        <h3 class="text-h6 font-weight-bold">Bank & Cash</h3>
      </v-card-title>
      <v-card-text>
        <BankLedgerSummary
          :key="propertyCode + ':' + (bizDate || 'auto')"
          :property-code="propertyCode"
          :default-date="bizDate"
          :default-account="'NH-301-xxxx'"
        />
      </v-card-text>
    </v-card>

    <!-- ───────────────────── Inventory / HR (Soon) ───────────────────── -->
    <div class="grid-2">
      <ComingSoonOverlay label="Inventory v1 예정">
        <v-card class="panel">
          <v-card-title><h3 class="text-h6 font-weight-bold">재고 요약</h3></v-card-title>
          <v-card-text><SkeletonCard :lines="4" /></v-card-text>
        </v-card>
      </ComingSoonOverlay>

      <ComingSoonOverlay label="근태 v1 예정">
        <v-card class="panel">
          <v-card-title><h3 class="text-h6 font-weight-bold">근태 요약</h3></v-card-title>
          <v-card-text><SkeletonCard :lines="4" /></v-card-text>
        </v-card>
      </ComingSoonOverlay>
    </div>
  </PageShell>
</template>

<script setup lang="ts">
/* ============================================================
   Dashboard Logic Section
   ------------------------------------------------------------
   - 날짜는 프런트에서 계산하지 않고 서버 산출값만 사용
   - 초기/리셋: /closing/day?property_code=... (date 없이)
   - 이후 KPI/Closing 요청에 해당 business_date 그대로 전달
=========================================================== */
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { debounce } from 'lodash-es'
import http from '@/services/http'

import PageShell from '@/ui/components/layout/PageShell.vue'
import SmartFilterBar from '@/ui/components/common/SmartFilterBar.vue'
import BizDatePicker from '@/ui/components/common/BizDatePicker.vue'
import KpiCard from '@/ui/components/common/KpiCard.vue'
import SkeletonCard from '@/ui/components/common/SkeletonCard.vue'
import ComingSoonOverlay from '@/ui/components/common/ComingSoonOverlay.vue'
import BankLedgerSummary from '@/ui/components/reports/BankLedgerSummary.vue'

// ────────────────────────────── 상태 정의 ──────────────────────────────
const propertyCode = ref<string>('MOP')
const propertyOptions = ['MOP']

// ✅ 서버에서 받은 business_date를 보관 (초기 빈값 → 서버에서 세팅)
const bizDate = ref<string>('')

const kpi = ref<any>(null)
const closing = ref<{ status: 'OPEN' | 'CLOSED'; done: number; total: number }>({
  status: 'OPEN',
  done: 0,
  total: 0,
})

// ────────────────────────────── 계산 속성 ──────────────────────────────
const totalAmount = computed<number>(() => {
  return (
    (kpi.value?.room_only_amount ?? 0) +
    (kpi.value?.package_amount ?? 0) +
    (kpi.value?.other_amount ?? 0)
  )
})
const closingPercent = computed<number>(() => {
  const t = closing.value.total || 0
  const d = closing.value.done || 0
  return t > 0 ? (d / t) * 100 : 0
})

// ────────────────────────────── 서버 사업일 획득 ──────────────────────────────
/**
 * 서버에서 기본 사업일(business_date) 및 요약을 받아와 bizDate/closing을 동기화.
 * - date 없이 호출 → 서버가 오늘의 사업일을 판단.
 */
async function fetchServerBizDate() {
  const pc = propertyCode.value || 'MOP'
  const res: any = await http.get(`/closing/day?property_code=${encodeURIComponent(pc)}`)
  const d = res?.business_date || res?.date || ''
  if (!d) throw new Error('Server did not return business_date')

  // 서버 요약도 같이 왔다면 즉시 반영
  const status = String(res.status || 'OPEN').toUpperCase()
  const done = Number(res.done ?? 0)
  const total = Number(res.total ?? 0)
  bizDate.value = d
  closing.value = { status: status === 'CLOSED' ? 'CLOSED' : 'OPEN', done, total }
}

/** SmartFilterBar "리셋" → 서버 기준일로 동기화 */
async function resetToServerBizDate() {
  try {
    await fetchServerBizDate()
    await fetchAll()
  } catch (e) {
    console.error('[Dashboard] resetToServerBizDate failed:', e)
  }
}

// ────────────────────────────── 데이터 로드 ──────────────────────────────
/**
 * KPI 조회
 *  - 서버에서 받은 bizDate를 그대로 전달
 *  - 백엔드 스키마: business_date 파라미터 사용
 */
async function fetchKpi() {
  if (!bizDate.value) return
  try {
    const url =
      `/reports/dashboard-kpi?property_code=${encodeURIComponent(propertyCode.value)}` +
      `&business_date=${encodeURIComponent(bizDate.value)}`
    const data = await http.get(url)
    kpi.value = data
  } catch (e: any) {
    console.error('[Dashboard] fetchKpi failed (likely invalid param):', e?.response || e)
    kpi.value = null
  }
}

/**
 * 마감 상태 조회
 *  - 원칙: 서버 기본 사업일과 동기화를 위해 가능하면 date 없이 호출(최초/리셋)
 *  - 이미 bizDate가 확보된 이후엔 그 날짜로 조회하여 일관성 유지
 */
async function fetchClosing() {
  try {
    const pc = propertyCode.value || 'MOP'
    let result: any

    if (!bizDate.value) {
      result = await http.get(`/closing/day?property_code=${encodeURIComponent(pc)}`)
    } else {
      const url =
        `/closing/day?date=${encodeURIComponent(bizDate.value)}` +
        `&property_code=${encodeURIComponent(pc)}`
      result = await http.get(url)
    }

    if (result && typeof result === 'object') {
      // 서버가 최신 business_date를 재반환할 수 있으니 싱크
      const d = result?.business_date || result?.date
      if (d && d !== bizDate.value) bizDate.value = d

      const status = String(result.status || 'OPEN').toUpperCase()
      const done = Number(result.done ?? 0)
      const total = Number(result.total ?? 0)
      closing.value = { status: status === 'CLOSED' ? 'CLOSED' : 'OPEN', done, total }
    } else {
      closing.value = { status: 'OPEN', done: 0, total: 0 }
    }
  } catch (e) {
    console.error('[Dashboard] fetchClosing failed:', e)
    closing.value = { status: 'OPEN', done: 0, total: 0 }
  }
}

// ────────────────────────────── 종합 로더 ──────────────────────────────
/**
 * 주의: bizDate가 비어 있으면 먼저 서버에서 확보 후 병렬 호출
 */
const fetchAll = debounce(async () => {
  try {
    if (!propertyCode.value?.trim()) return
    if (!bizDate.value?.trim()) await fetchServerBizDate()
    await Promise.allSettled([fetchKpi(), fetchClosing()])
  } catch (e) {
    console.error('[Dashboard] fetchAll bootstrap failed:', e)
  }
}, 200)

// ────────────────────────────── 라이프사이클 ──────────────────────────────
onMounted(async () => {
  await nextTick()
  // 최초 진입: 서버 기준일 확보 후 전체 로드
  try {
    await fetchServerBizDate()
  } catch (e) {
    console.error('[Dashboard] initial business_date fetch failed:', e)
  }
  fetchAll()

  // Watch: propertyCode 변경 시 서버 기준일로 리셋 + 재조회
  watch(propertyCode, async (p, op) => {
    if (p && p !== op) {
      await resetToServerBizDate()
    }
  })

  // Watch: BizDatePicker로 날짜를 바꾸면 그대로 재조회(연산 없이 서버 값만 사용)
  watch(bizDate, (d, od) => {
    if (d && d !== od) fetchAll()
  })
})
</script>

<style scoped>
/* ============================================================
   Dashboard Local Style
=========================================================== */
.progress-wrap {
  width: 120px;
  margin-left: 8px;
}

.top-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.grid-2 {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 12px;
}

.panel {
  border: 1px solid var(--surface-3, #e8e8e8);
  border-radius: 12px;
  background: var(--surface-1, #fff);
  padding: 12px;
}
</style>
