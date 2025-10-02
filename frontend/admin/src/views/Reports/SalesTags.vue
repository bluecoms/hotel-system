<template>
  <v-container class="py-6">
    <h1 class="text-h5 mb-1">{{ t('reports.salesTags') }}</h1>
    <div class="text-body-2 text-medium-emphasis mb-4">
      Phase 2 — READ 전용 + 에러/합계 강화
    </div>

    <!-- 빠른 기간 + Export -->
    <v-row class="mb-3" align="center" no-gutters>
      <v-chip-group column>
        <v-chip size="small" @click="setRange('today')">{{ t('reports.range.today') }}</v-chip>
        <v-chip size="small" @click="setRange('thisMonth')">{{ t('reports.range.thisMonth') }}</v-chip>
        <v-chip size="small" @click="setRange('prevMonth')">{{ t('reports.range.prevMonth') }}</v-chip>
      </v-chip-group>
      <v-spacer />
      <v-btn size="small" variant="flat" :loading="exporting" @click="exportCsv">
        {{ t('cta.export') }}
      </v-btn>
    </v-row>

    <!-- 기간 입력 -->
    <v-row class="mb-3" dense>
      <v-col cols="12" md="3">
        <v-text-field v-model="dateFrom" label="From (YYYY-MM-DD)" density="comfortable" />
      </v-col>
      <v-col cols="12" md="3">
        <v-text-field v-model="dateTo" label="To (YYYY-MM-DD)" density="comfortable" />
      </v-col>
      <v-col cols="12" md="6" class="d-flex ga-2">
        <v-btn @click="refreshTags" :loading="loading" variant="flat">조회</v-btn>
      </v-col>
    </v-row>

    <!-- 상태 블록 (로딩/빈/에러) -->
    <stateblock v-if="loading || rows.length === 0 || error"
      :loading="loading"
      :error="error" />

    <!-- 합계 카드 -->
    <v-card v-if="!loading && !error && rows.length > 0" class="mb-4 pa-4">
      <div class="text-subtitle-1 mb-2">{{ t('table.total') }}</div>
      <div class="text-medium-emphasis">
        {{ t('table.count') }}:
        <b>{{ totals.count.toLocaleString('ko-KR') }}</b>
        &nbsp;/&nbsp;
        {{ t('table.amount') }}:
        <b>{{ fmtKRW(totals.amount) }}</b>
      </div>
    </v-card>

    <!-- 테이블 -->
    <v-card v-if="!loading && !error && rows.length > 0">
      <v-data-table
        :items="rows"
        :headers="headers"
        class="elevation-0"
        :items-per-page="10"
        aria-label="태그별 매출 테이블"
      >
        <template #item.count="{ item }">
          {{ item.count.toLocaleString('ko-KR') }}
        </template>

        <template #item.amount="{ item }">
          {{ fmtKRW(item.amount) }}
        </template>

        <template #footer.prepend>
          <div class="pa-3">
            {{ t('table.total') }} —
            {{ t('table.count') }}:
            <b>{{ totals.count.toLocaleString('ko-KR') }}</b>
            <span class="mx-2">/</span>
            {{ t('table.amount') }}:
            <b>{{ fmtKRW(totals.amount) }}</b>
          </div>
        </template>

        <template #no-data>
          <div class="pa-6 text-medium-emphasis">{{ t('state.empty') }}</div>
        </template>
      </v-data-table>
    </v-card>

    <!-- 에러 토스트 1종 -->
    <v-snackbar v-model="toast.show" timeout="3500">
      {{ toast.message }}
    </v-snackbar>
  </v-container>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import http from '@/services/http'
import StateBlock from '@/ui/components/StateBlock.vue'
import { fmtKRW } from '@/utils/format'

type Row = { tag: string; count: number; amount: number }

const { t } = useI18n()

const headers = [
  { title: '태그', key: 'tag' },
  { title: '건수', key: 'count' },
  { title: '금액', key: 'amount' },
]

const dateFrom    = ref<string>('')    // YYYY-MM-DD
const dateTo      = ref<string>('')    // YYYY-MM-DD
const rows        = ref<Row[]>([])
const totals      = ref<{ count:number; amount:number }>({ count:0, amount:0 })
const loading     = ref(false)
const exporting   = ref(false)
const error       = ref(false)
const toast       = ref<{ show: boolean; message: string }>({ show: false, message: '' })

function pad2(n:number){ return String(n).padStart(2,'0') }
function ymd(d: Date){ return `${d.getFullYear()}-${pad2(d.getMonth()+1)}-${pad2(d.getDate())}` }
function firstDayOfMonth(d = new Date()){ return new Date(d.getFullYear(), d.getMonth(), 1) }
function lastDayOfMonth(d = new Date()){ return new Date(d.getFullYear(), d.getMonth()+1, 0) }

function setRange(preset: 'today'|'thisMonth'|'prevMonth'){
  const today = new Date()
  if (preset === 'today'){
    dateFrom.value = ymd(today)
    dateTo.value   = ymd(today)
  } else if (preset === 'thisMonth'){
    dateFrom.value = ymd(firstDayOfMonth(today))
    dateTo.value   = ymd(lastDayOfMonth(today))
  } else {
    const prev = new Date(today.getFullYear(), today.getMonth()-1, 15)
    dateFrom.value = ymd(firstDayOfMonth(prev))
    dateTo.value   = ymd(lastDayOfMonth(prev))
  }
  refreshTags()
}

// API 호출 (+ 배열/래핑 방어)
const fetchTags = async (from?: string, to?: string) => {
  const q = new URLSearchParams()
  if (from) q.set('date_from', from)
  if (to) q.set('date_to', to)

  const res: any = await http.get(`/reports/sales-tags?${q}`)
  const arr = Array.isArray(res) ? res : (Array.isArray(res?.items) ? res.items : [])

  const normalized: Row[] = arr.map((x: any) => ({
    tag: String(x.tag ?? ''),
    count: Number(x.count ?? 0),
    // BE가 sales_amount로 내려줘도 흡수
    amount: Number(x.amount ?? x.sales_amount ?? 0),
  }))

  const t = normalized.reduce(
    (a, r) => ({
      count: a.count + (Number.isFinite(r.count) ? r.count : 0),
      amount: a.amount + (Number.isFinite(r.amount) ? r.amount : 0),
    }),
    { count: 0, amount: 0 }
  )

  return { rows: normalized, totals: t }
}

async function refreshTags() {
  // 날짜 역전 방지
  if (dateFrom.value && dateTo.value && dateFrom.value > dateTo.value) {
    toast.value = { show: true, message: t('state.error') }
    return
  }

  loading.value = true
  error.value = false
  try {
    const { rows: r, totals: t } = await fetchTags(dateFrom.value, dateTo.value)
    rows.value = r
    totals.value = t
  } catch (e: any) {
    rows.value = []
    totals.value = { count:0, amount:0 }
    error.value = true
    const status = e?.status ?? e?.response?.status
    const detail = e?.message ?? e?.detail ?? e?.response?.data?.detail ?? ''
    if (status === 400 || status === 422) {
      toast.value = { show: true, message: detail || t('state.error') }
    } else {
      toast.value = { show: true, message: 'Sales Tags를 불러오지 못했습니다.' }
    }
  } finally {
    loading.value = false
  }
}

async function exportCsv() {
  if (dateFrom.value && dateTo.value && dateFrom.value > dateTo.value) {
    toast.value = { show: true, message: t('state.error') }
    return
  }

  exporting.value = true
  try {
    const q = http.qs({ date_from: dateFrom.value || undefined, date_to: dateTo.value || undefined })
    const blob = await http.getBlob(`/reports/sales-tags/export${q}`, {
      headers: { Accept: 'text/csv, */*' }
    })
    const from = (dateFrom.value || 'NA').replace(/-/g, '')
    const to   = (dateTo.value   || 'NA').replace(/-/g, '')
    const fname = `sales-tags_${from}-${to}.csv`
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = fname
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  } catch {
    toast.value = { show: true, message: '내보내기에 실패했습니다.' }
  } finally {
    exporting.value = false
  }
}

onMounted(refreshTags)
</script>
