<!--
=================================================================
 Hotel Admin — Bank Ledger Summary Component (v2025.10 Final / Auto Date Init)
-----------------------------------------------------------------
 목적:
  - 기본 bizDate를 Dashboard 또는 오늘 날짜로 초기화
  - 경고 메시지 노출 제거 (초기 로드시 에러 표시 안함)
  - 대시보드 BizDatePicker 디자인과 좌측 정렬 유지
-----------------------------------------------------------------
 변경사항 (2025-10-20):
  ✅ 백엔드 파라미터명 변경 대응 (date → business_date)
  ✅ 서버 reports_bank.py v2025.10-20 기준 완전 호환
=================================================================
-->

<template>
  <v-card>
    <!-- 조회 조건 영역 -->
    <v-card-title class="py-3 px-5">
      <div class="d-flex align-center" style="gap:12px; flex-wrap:wrap;">
        <!-- 계좌 선택 -->
        <v-combobox
          v-model="selectedAcct"
          :items="accountItems"
          label="Account"
          density="comfortable"
          clearable
          hide-details
          variant="outlined"
          class="account-combo"
        />

        <!-- BizDatePicker -->
        <BizDatePicker
          v-model="bizDate"
          mode="day"
          label="조회 일자"
          class="bizdate-picker"
        />

        <v-btn color="primary" size="small" :loading="loading" @click="load">
          조회
        </v-btn>
      </div>
    </v-card-title>

    <v-divider />

    <!-- 본문 -->
    <v-card-text>
      <!-- 오류 메시지 (실제 네트워크 오류만 표시) -->
      <v-alert
        v-if="errorText"
        type="error"
        variant="tonal"
        border="start"
        class="mb-3"
      >
        {{ errorText }}
      </v-alert>

      <!-- KPI 요약 -->
      <div class="d-flex flex-wrap mb-3" style="gap:10px">
        <v-chip color="success" label>입금 {{ fmtNum(kpis.in_amount) }}</v-chip>
        <v-chip color="error" label>출금 {{ fmtNum(kpis.out_amount) }}</v-chip>
        <v-chip color="primary" label>순이동 {{ fmtNum(kpis.net_amount) }}</v-chip>
        <v-chip color="grey" label v-if="kpis.last_balance !== null">
          마감잔액 {{ fmtNum(kpis.last_balance || 0) }}
        </v-chip>
      </div>

      <v-skeleton-loader v-if="loading" type="table" class="mt-2" />

      <template v-else>
        <v-table density="comfortable" class="mt-2">
          <thead>
            <tr>
              <th style="width:110px">시간</th>
              <th>적요</th>
              <th style="width:120px" class="text-right">입금</th>
              <th style="width:120px" class="text-right">출금</th>
              <th style="width:120px">지점</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(r, i) in rows" :key="i">
              <td>{{ r.txn_time || '-' }}</td>
              <td>{{ r.note || '-' }}</td>
              <td class="text-right">{{ r.direction === 'IN' ? fmtNum(r.amount) : '' }}</td>
              <td class="text-right">{{ r.direction === 'OUT' ? fmtNum(r.amount) : '' }}</td>
              <td>{{ r.branch || '-' }}</td>
            </tr>
            <tr v-if="!rows.length">
              <td colspan="5" class="text-center text-medium-emphasis py-6">데이터 없음</td>
            </tr>
          </tbody>
        </v-table>
        <div class="text-caption text-medium-emphasis mt-2">
          최대 20건까지만 미리보기로 표시됩니다.
        </div>
      </template>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import BizDatePicker from '@/ui/components/common/BizDatePicker.vue'
import { getBankLedgerSummary, type BankLedgerSummaryResp } from '@/services/reports'

const props = defineProps<{
  propertyCode: string
  defaultAccount?: string
  defaultDate: string
  accounts?: string[]
}>()

type Row = NonNullable<BankLedgerSummaryResp['items']>[number]

// ────────────────────────────── 상태 정의 ──────────────────────────────
const localProperty = ref(props.propertyCode)
const bizDate = ref(props.defaultDate || new Date().toISOString().slice(0, 10))
const selectedAcct = ref(props.defaultAccount || '')

const accountItems = computed(() =>
  (props.accounts?.length ? props.accounts : ['NH-301-xxxx', 'NH-302-yyyy']) as string[]
)

const loading = ref(false)
const errorText = ref('')
const rows = ref<Row[]>([])
const kpis = ref({
  in_amount: 0,
  out_amount: 0,
  net_amount: 0,
  last_balance: 0 as number | null,
})

const inFlight = ref(false)
let lastArgs = { date: '', prop: '', acct: '' }

// ────────────────────────────── 함수 정의 ──────────────────────────────
function fmtNum(v?: string | number | null) {
  const n = typeof v === 'string' ? Number(v) : (v ?? 0)
  return Number.isFinite(n) ? n.toLocaleString() : '0'
}

async function load() {
  const args = {
    date: bizDate.value,
    prop: localProperty.value,
    acct: selectedAcct.value || accountItems.value[0],
  }

  if (args.date === lastArgs.date && args.prop === lastArgs.prop && args.acct === lastArgs.acct) return
  lastArgs = { ...args }

  if (inFlight.value) return
  inFlight.value = true
  loading.value = true
  errorText.value = ''

  try {
    // ✅ backend reports_bank.py (v2025.10-20) 대응 — business_date 사용
    const r = await getBankLedgerSummary({
      business_date: args.date,
      property_code: args.prop,
      account_code: args.acct,
    })
    rows.value = Array.isArray(r.items) ? r.items : []
    kpis.value = {
      in_amount: r.in_amount || 0,
      out_amount: r.out_amount || 0,
      net_amount: r.net_amount || 0,
      last_balance: r.last_balance ?? 0,
    }
  } catch (e: any) {
    errorText.value = e?.message?.includes('required')
      ? ''
      : e?.message || '조회 실패'
    rows.value = []
    kpis.value = { in_amount: 0, out_amount: 0, net_amount: 0, last_balance: 0 }
  } finally {
    loading.value = false
    inFlight.value = false
  }
}

// ────────────────────────────── watch & 초기화 ──────────────────────────────
watch(() => props.propertyCode, (v) => {
  localProperty.value = v
  if (!selectedAcct.value) selectedAcct.value = accountItems.value[0]
  load()
})

watch(() => props.defaultDate, (v) => {
  if (v && v !== bizDate.value) {
    bizDate.value = v
    load()
  }
})

watch(selectedAcct, () => load())
watch(bizDate, () => load())

onMounted(() => {
  if (!selectedAcct.value) selectedAcct.value = accountItems.value[0]
  load()
})
</script>

<style scoped>
.account-combo {
  min-width: 300px !important;
  flex-shrink: 0;
}
.bizdate-picker {
  min-width: 260px !important;
}
.v-combobox,
.v-text-field,
.v-btn {
  --v-input-control-height: 40px;
}
</style>
