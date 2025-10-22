<!-- ============================================================================
  File    : src/views/closing/Board.vue
  Version : 2025.10 Final Stable (Phase3 SSOT · KR+UX · SFC 정합판 · Partition)
  Purpose : 일별 마감 보드 (5탭 업로드: 객실매출/예약내역/FNB/지출/입금)
  ------------------------------------------------------------------------------
  주요 기능:
    ✅ DatasetCard 재사용 / 한글화 / 툴팁 / 진행률 / 마감(승인·잠금·해제)
    ✅ 전역 property_code('MOP') 고정, axios 미사용(fetch 기반 http.ts만)
    ✅ BizDatePicker / SectionHeader / GridCards 컴포넌트 분리 (SFC 구조 정합)
    ✅ Partition 지원: FNB(pay/items), Bank(계좌별 in/out) 칩 선택 업로드
  ------------------------------------------------------------------------------
  백엔드 연동:
    • GET  /api/closing/day?date=YYYY-MM-DD&property_code=MOP
    • POST /api/closing/build      → 마감 데이터 재계산
    • POST /api/closing/approve    → 상태 CLOSED
    • POST /api/closing/lock       → 상태 LOCKED
    • POST /api/closing/unlock     → 상태 OPEN
    • POST /api/upload/{dataset}   → DatasetCard 내부 호출(FormData)
    • GET  /api/upload/versions    → DatasetCard 내부 호출
  ------------------------------------------------------------------------------
  Dataset 매핑:
    • 객실 매출   : sales_front     (snapshot / soft_delete)
    • 예약 내역   : rooms_status    (append   / soft_delete)
    • F&B 매출   : fnb_items, fnb_tenders (snapshot / soft_delete)
    • 지출 내역   : expenses        (snapshot / soft_delete)
    • 입금 내역   : bank_ledger     (append   / ignore)
  ------------------------------------------------------------------------------
  상태 규칙:
    • dayStatus = OPEN / CLOSED / LOCKED
      → CLOSED/LOCKED 시 업로드 가드(비활성)
============================================================================ -->

<template>
  <v-container fluid class="page-shell py-6">
    <!-- ▣ 상단 툴바 -->
    <v-card class="brand-panel mb-4 rounded-2xl">
      <v-card-title class="py-3">
        <div class="d-flex align-center justify-space-between flex-wrap" style="gap:12px">
          <!-- ◈ 좌측 : 제목 / 상태칩 / 진행률 -->
          <div class="d-flex align-center flex-wrap" style="gap:12px">
            <div class="d-flex align-center" style="gap:8px">
              <span class="text-h6">일별 마감 보드</span>
              <v-tooltip text="선택한 업무일자의 업로드 현황을 확인하고 승인/잠금 등 마감을 수행합니다.">
                <template #activator="{ props }">
                  <v-icon v-bind="props" icon="mdi-help-circle-outline" size="18" />
                </template>
              </v-tooltip>
            </div>

            <v-chip :color="statusColor" label size="small" variant="flat" class="font-weight-medium">
              {{ dayInfo.status }}
            </v-chip>
            <v-chip size="small" variant="tonal" class="font-weight-medium">
              완료 {{ dayInfo.done }} / {{ dayInfo.total }}
            </v-chip>
          </div>

          <!-- ◈ 우측 : 날짜 컨트롤 + 액션버튼 -->
          <div class="d-flex align-center" style="gap:8px">
            <!-- 날짜 선택기 -->
            <BizDatePicker
              v-model="bizDate"
              class="bizdate-picker"
              @prev="shift(-1)"
              @next="shift(1)"
              @update:model-value="refresh"
            />

            <!-- 재계산 -->
            <v-tooltip text="업로드된 데이터를 기반으로 요약을 재계산합니다. 완료 5/5면 CLOSED로 전환됩니다.">
              <template #activator="{ props }">
                <v-btn v-bind="props" :loading="loading.build" color="primary" class="btn-action" @click="act('build')">
                  재계산(Build)
                </v-btn>
              </template>
            </v-tooltip>

            <!-- 승인 -->
            <v-tooltip text="해당 일자를 승인(CLOSED) 상태로 전환합니다.">
              <template #activator="{ props }">
                <v-btn v-bind="props" :loading="loading.approve" color="success" variant="tonal" class="btn-action" @click="act('approve')">
                  승인
                </v-btn>
              </template>
            </v-tooltip>

            <!-- 잠금 -->
            <v-tooltip text="해당 일자를 잠금(LOCKED) 상태로 전환하여 업로드/수정을 막습니다.">
              <template #activator="{ props }">
                <v-btn v-bind="props" :loading="loading.lock" color="warning" variant="tonal" class="btn-action" @click="act('lock')">
                  잠금
                </v-btn>
              </template>
            </v-tooltip>

            <!-- 잠금 해제 -->
            <v-tooltip text="잠금을 해제하여 OPEN 상태로 되돌립니다.">
              <template #activator="{ props }">
                <v-btn v-bind="props" :loading="loading.unlock" color="grey-darken-1" variant="text" class="btn-action" @click="act('unlock')">
                  잠금해제
                </v-btn>
              </template>
            </v-tooltip>
          </div>
        </div>
      </v-card-title>

      <v-divider />

      <v-card-text class="py-3">
        <v-alert type="info" variant="tonal" border="start" class="mb-0">
          드라이런(DryRun)으로 먼저 검증한 후 실제 업로드를 권장합니다.<br />
          템플릿은 각 카드의 <strong>템플릿</strong> 버튼에서 내려받으세요.
        </v-alert>
      </v-card-text>
    </v-card>

    <!-- ▣ 마감 경고 -->
    <v-alert
      v-if="dayInfo.status === 'CLOSED' || dayInfo.status === 'LOCKED'"
      :type="dayInfo.status === 'LOCKED' ? 'warning' : 'error'"
      variant="tonal"
      border="start"
      class="mb-4"
    >
      <strong>{{ dayInfo.status }}</strong> 상태에서는 업로드가 제한됩니다.
      (잠금 해제 또는 재오픈 후 업로드하세요)
    </v-alert>

    <!-- ▣ 탭 구조 -->
    <v-card class="rounded-2xl">
      <v-tabs
        v-model="tab"
        bg-color="transparent"
        color="primary"
        slider-color="primary"
        class="px-3 pt-2"
        density="comfortable"
      >
        <v-tab value="sales">객실 매출</v-tab>
        <v-tab value="rooms">예약 내역</v-tab>
        <v-tab value="fnb">F&B 매출</v-tab>
        <v-tab value="expenses">지출 내역</v-tab>
        <v-tab value="bank">입금 내역</v-tab>
      </v-tabs>

      <v-divider />

      <v-window v-model="tab">
        <!-- 객실 매출 -->
        <v-window-item value="sales">
          <div class="pa-4">
            <SectionHeader
              icon="mdi-bed-outline"
              title="객실 매출 업로드"
              hint="전면 매출(객실/조식 등) CSV 업로드 — 스냅샷 방식으로 기존 값이 교체됩니다."
            />
            <GridCards>
              <DatasetCard
                :dataset="'sales_front'"
                :bizDate="bizDate"
                :propertyCode="PROPERTY_CODE"
                :dayStatus="dayInfo.status"
                @done="refresh"
              />
            </GridCards>
          </div>
        </v-window-item>

        <!-- 예약 내역 -->
        <v-window-item value="rooms">
          <div class="pa-4">
            <SectionHeader
              icon="mdi-door-open"
              title="예약/객실 상태 업로드"
              hint="객실 상태(CLEAN/DIRTY/OOO 등) CSV 업로드 — append 방식(누적)."
            />
            <GridCards>
              <DatasetCard
                :dataset="'rooms_status'"
                :bizDate="bizDate"
                :propertyCode="PROPERTY_CODE"
                :dayStatus="dayInfo.status"
                @done="refresh"
              />
            </GridCards>
          </div>
        </v-window-item>

        <!-- F&B 매출 (Partition: pay/items) -->
        <v-window-item value="fnb">
          <div class="pa-4">
            <SectionHeader
              icon="mdi-silverware-fork-knife"
              title="F&B 매출 업로드"
              hint="품목/결제수단별 CSV 업로드 — 스냅샷 방식."
            />
            <GridCards>
              <!-- 품목별 매출 -->
              <DatasetCard
                :dataset="'fnb_items'"
                :bizDate="bizDate"
                :propertyCode="PROPERTY_CODE"
                :dayStatus="dayInfo.status"
                @done="refresh"
              />
              <!-- 결제수단별 매출 (기존 레거시 2파일 업로드를 part로 표현할 수도 있음) -->
              <DatasetCard
                :dataset="'fnb_tenders'"
                :bizDate="bizDate"
                :propertyCode="PROPERTY_CODE"
                :dayStatus="dayInfo.status"
                :partitionVisible="true"
                :partitionItems="['pay','items']"
                @done="refresh"
              />
            </GridCards>
          </div>
        </v-window-item>

        <!-- 지출 내역 -->
        <v-window-item value="expenses">
          <div class="pa-4">
            <SectionHeader
              icon="mdi-receipt-text-outline"
              title="지출 내역 업로드"
              hint="계정코드별 지출 CSV 업로드 — 스냅샷 방식."
            />
            <GridCards>
              <DatasetCard
                :dataset="'expenses'"
                :bizDate="bizDate"
                :propertyCode="PROPERTY_CODE"
                :dayStatus="dayInfo.status"
                @done="refresh"
              />
            </GridCards>
          </div>
        </v-window-item>

        <!-- 입금 내역 (Partition: 계좌별 in/out) -->
        <v-window-item value="bank">
          <div class="pa-4">
            <SectionHeader
              icon="mdi-bank-outline"
              title="입금/출금 내역 업로드"
              hint="은행 입출금 CSV 업로드 — append 방식, 누락은 무시(ignore). 계좌별/방향별 파티션 지원."
            />
            <GridCards>
              <DatasetCard
                :dataset="'bank_ledger'"
                :bizDate="bizDate"
                :propertyCode="PROPERTY_CODE"
                :dayStatus="dayInfo.status"
                :partitionVisible="true"
                :partitionItems="bankPartitions"
                @done="refresh"
              />
            </GridCards>
          </div>
        </v-window-item>
      </v-window>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
/* ============================================================================
  구현 원칙:
    • axios 사용 금지(fetch 기반 http.ts만)
    • Board.vue는 단일 <template>/<script setup>/<style> 구조 유지
    • 보조 컴포넌트는 외부 import 사용 (SFC 파서 오류 방지)
    • API 실패 시 콘솔 경고 및 토스트 메시지 표시
============================================================================ */

import { ref, computed, onMounted } from 'vue'
import http from '@/services/http'
import BizDatePicker from '@/ui/components/common/BizDatePicker.vue'
import DatasetCard from '@/ui/components/closing/DatasetCard.vue'
import SectionHeader from '@/ui/components/layout/SectionHeader.vue'
import GridCards from '@/ui/components/layout/GridCards.vue'
import { useToast } from '@/ui/composables/useToast'

/* ─────────────── 상수 / 헬퍼 ─────────────── */
const PROPERTY_CODE = 'MOP'
const { success, error } = useToast()

/* ─────────────── 타입 정의 ─────────────── */
type ClosingDayResp = {
  date?: string
  business_date?: string
  status?: string
  done?: number
  total?: number
  complete?: boolean
}

/* ─────────────── 상태 정의 ─────────────── */
const tab = ref<'sales' | 'rooms' | 'fnb' | 'expenses' | 'bank'>('sales')
const bizDate = ref<string>(new Date().toISOString().slice(0, 10))
const dayInfo = ref({
  date: bizDate.value,
  business_date: bizDate.value,
  status: 'OPEN',
  done: 0,
  total: 5,
  complete: false,
})

/* Bank 파티션(계좌별 in/out) — 필요 시 API로 대체 가능 */
const bankAccounts = ref<string[]>(['NH301', 'Woori', 'IBK'])
const bankPartitions = computed<string[]>(
  () => bankAccounts.value.flatMap(a => [`${a}_in`, `${a}_out`])
)

/* ─────────────── 상태 색상 ─────────────── */
const statusColor = computed(() => {
  const s = String(dayInfo.value.status || '').toUpperCase()
  if (s === 'CLOSED') return 'red'
  if (s === 'LOCKED') return 'warning'
  return 'primary'
})

/* ─────────────── API 호출 ─────────────── */
async function fetchClosingDay() {
  const url = `/closing/day?date=${encodeURIComponent(bizDate.value)}&property_code=${PROPERTY_CODE}`
  const res = await http.get<ClosingDayResp>(url)

  // ★ TS2339 방지: 안전한 optional 접근 + 기본값 주입
  const date = res?.date ?? bizDate.value
  const bdate = res?.business_date ?? date
  const status = String(res?.status ?? 'OPEN').toUpperCase()
  const done = Number(res?.done ?? 0)
  const total = Number(res?.total ?? 5)
  const complete = !!res?.complete

  dayInfo.value = { date, business_date: bdate, status, done, total, complete }
}

async function refresh() {
  try {
    await fetchClosingDay()
  } catch (e) {
    console.warn('refresh failed:', e)
  }
}

/* 날짜 이동 */
function shift(delta: number) {
  const d = new Date(bizDate.value)
  d.setDate(d.getDate() + delta)
  bizDate.value = d.toISOString().slice(0, 10)
  refresh()
}

/* 마감 상태 액션 */
async function act(kind: 'build' | 'approve' | 'lock' | 'unlock') {
  const urlMap = {
    build: '/closing/build',
    approve: '/closing/approve',
    lock: '/closing/lock',
    unlock: '/closing/unlock',
  } as const

  try {
    loading.value[kind] = true
    await http.post(urlMap[kind], { business_date: bizDate.value, property_code: PROPERTY_CODE })
    await refresh()
    if (kind === 'build') success('재계산 완료')
    if (kind === 'approve') success('승인(CLOSED) 완료')
    if (kind === 'lock') success('잠금(LOCKED) 완료')
    if (kind === 'unlock') success('잠금 해제(OPEN) 완료')
  } catch (e) {
    error('작업 실패')
    console.warn(`${kind} failed:`, e)
  } finally {
    loading.value[kind] = false
  }
}

/* 로딩 상태 */
const loading = ref<Record<'build' | 'approve' | 'lock' | 'unlock', boolean>>({
  build: false,
  approve: false,
  lock: false,
  unlock: false,
})

/* 초기 로드 */
onMounted(async () => {
  await refresh()
})
</script>

<style scoped>
/* ============================================================================
  Layout & Style
============================================================================ */
.page-shell { max-width: 1280px; margin: 0 auto; }
.brand-panel {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(16, 24, 40, 0.06);
}
.bizdate-picker { min-width: 260px; }
.btn-action { height: 40px; min-width: 96px; font-weight: 600; }
.d-grid { display: grid; }
</style>
