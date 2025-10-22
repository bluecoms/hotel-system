<template>
  <v-container fluid class="page-shell py-6">
    <div class="bar brand-panel d-flex align-center justify-space-between flex-wrap mb-4">
      <div class="bar-left d-flex align-center flex-wrap gap8">
        <v-breadcrumbs :items="crumbs" class="pa-0 ma-0" />
        <v-divider vertical class="mx-2" />
        <v-chip
          :color="dayStatus==='CLOSED' ? 'red' : 'primary'"
          label
          size="small"
          variant="flat"
        >
          {{ dayStatus }}
        </v-chip>
      </div>

      <div class="bar-right d-flex align-center gap8 mt-2 mt-sm-0">
        <v-btn variant="text" icon="mdi-chevron-left" class="btn-40" @click="shift(-1)" />
        <v-text-field
          v-model="bizDate"
          label="Business Date (YYYY-MM-DD)"
          variant="outlined"
          density="comfortable"
          class="date-input"
          hide-details
          @keyup.enter="refreshDay"
        />
        <v-btn variant="text" icon="mdi-chevron-right" class="btn-40" @click="shift(1)" />
        <v-btn color="primary" :loading="loading" class="btn-action" @click="refreshDay">
          불러오기
        </v-btn>

        <v-btn
          v-if="isSuper"
          :color="dayStatus==='OPEN' ? 'red' : 'green'"
          prepend-icon="mdi-lock"
          class="btn-action"
          @click="toggleDay"
        >
          {{ dayStatus==='OPEN' ? '마감' : '재오픈' }}
        </v-btn>
      </div>
    </div>

    <v-alert
      v-if="dayStatus==='CLOSED'"
      type="warning"
      variant="tonal"
      border="start"
      class="mb-4"
    >
      <strong>CLOSED</strong> 상태에서는 업로드가 차단됩니다.
    </v-alert>

    <v-tabs v-model="activeTab" color="primary" class="mb-4">
      <v-tab v-for="ds in datasets" :key="ds" :value="ds">
        <v-icon :icon="iconMap[ds].icon" size="small" class="mr-2" />
        {{ labelMap[ds] }}
      </v-tab>
    </v-tabs>

    <v-window v-model="activeTab">
      <v-window-item
        v-for="ds in datasets"
        :key="ds"
        :value="ds"
      >
        <DatasetCard
          :dataset="ds"
          :label="labelMap[ds]"
          :bizDate="bizDate"
          :propertyCode="propertyCode"
          :dayStatus="dayStatus"
          :dryRun="dryRun"
          :globalDryRun="globalDryRun"
          @refresh="refreshDay"
        />
      </v-window-item>
    </v-window>

    <NoTxnModal
      :open="dlgNoTxn"
      :businessDate="bizDate"
      :propertyCode="propertyCode"
      @update:open="(v:boolean)=> dlgNoTxn=v"
      @done="onNoTxnDone"
    />
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import DatasetCard from '@/ui/components/DatasetCard.vue'
import NoTxnModal from '@/ui/components/NoTxnModal.vue'
import { useToast } from '@/ui/composables/useToast'
import http from '@/services/http'

const route = useRoute()
const auth = useAuthStore()
const { success, error } = useToast()

const isSuper = computed(() =>
  auth.hasRole?.('SUPERADMIN') || auth.user?.roles?.includes('SUPERADMIN')
)

const propertyCode = 'MOP'
const bizDate = ref(new Date().toISOString().slice(0, 10))
const dayStatus = ref<'OPEN'|'CLOSED'>('OPEN')
const activeTab = ref('sales_front')
const dlgNoTxn = ref(false)
const loading = ref(false)

/* ✅ 드라이런 전역 상태 */
const globalDryRun = ref(false)
const dryRun = reactive<Record<string, boolean>>({
  sales_front: false,
  rooms_status: false,
  fnb_sales: false,
  expenses: false,
  pay_settlement: false,
})

const datasets = ['sales_front','rooms_status','fnb_sales','expenses','pay_settlement'] as const

const labelMap: Record<string,string> = {
  sales_front: '프런트 매출',
  rooms_status: '객실 상태',
  fnb_sales: 'F&B 매출',
  expenses: '지출 내역',
  pay_settlement: '입금 내역',
}

const iconMap: Record<string, { icon: string; color: string }> = {
  sales_front: { icon: 'mdi-cash-register', color: 'primary' },
  rooms_status: { icon: 'mdi-bed-outline', color: 'primary' },
  fnb_sales: { icon: 'mdi-silverware-fork-knife', color: 'primary' },
  expenses: { icon: 'mdi-receipt-text-outline', color: 'primary' },
  pay_settlement: { icon: 'mdi-credit-card-outline', color: 'primary' },
}

const crumbs = [
  { title: '마감 관리', disabled: true },
  { title: '마감 보드', disabled: true },
]

function shift(delta: number) {
  const d = new Date(bizDate.value)
  d.setDate(d.getDate() + delta)
  bizDate.value = d.toISOString().slice(0, 10)
  refreshDay()
}

async function refreshDay() {
  loading.value = true
  try {
    const day = await http.get<{ status: 'OPEN'|'CLOSED' }>(
      `/closing/day?date=${bizDate.value}&property_code=${propertyCode}`
    )
    dayStatus.value = day.status
  } catch {
    dayStatus.value = 'OPEN'
    error('마감 상태 로드 실패')
  } finally {
    loading.value = false
  }
}

async function toggleDay() {
  try {
    const next = dayStatus.value === 'OPEN' ? 'CLOSED' : 'OPEN'
    await http.put('/closing/day', { date: bizDate.value, property_code: propertyCode, status: next })
    await refreshDay()
    success(`Day → ${next}`)
  } catch {
    error('상태 변경 실패')
  }
}

async function onNoTxnDone() {
  success('무거래 등록 완료')
  dlgNoTxn.value = false
  await refreshDay()
}

onMounted(() => {
  const qDate = typeof route.query.date === 'string' ? route.query.date : ''
  if (qDate) bizDate.value = qDate
  refreshDay()
})
</script>

<style src="@/styles/toolbar.scss"></style>

<style scoped>
.page-shell {
  max-width: 1280px;
  margin: 0 auto;
}

/* ✅ 통일된 brand-panel */
.brand-panel {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(16, 24, 40, 0.06);
}

/* 입력 필드 */
.date-input {
  width: 240px;
  --ctl-h: 40px;
}
.date-input :deep(.v-field) {
  height: var(--ctl-h);
}
.date-input :deep(input) {
  text-align: center;
}

/* 버튼 크기 통일 */
.btn-40 {
  height: 40px;
  width: 40px;
  min-width: 40px;
  padding: 0;
}
.btn-action {
  height: 40px;
  min-width: 90px;
  font-weight: 600;
}

/* 반응형 */
@media (max-width: 960px) {
  .date-input {
    width: 200px;
  }
}
</style>
