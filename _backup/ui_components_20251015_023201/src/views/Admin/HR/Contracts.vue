<template>
  <v-container fluid class="page-shell py-6">
    <div class="bar mb-6">
      <div class="bar-left">
        <v-icon color="primary" icon="mdi-file-document-outline" size="22" />
        <h2 class="text-h6 font-weight-bold">직원 계약 관리</h2>
        <span class="text-muted text-body-2">계약서 등록 · 버전 관리 · 종료 처리</span>
      </div>
      <div class="bar-right">
        <v-btn
          color="primary"
          prepend-icon="mdi-file-document-plus"
          variant="flat"
          class="btn-action"
          @click="openNewContract"
        >
          신규 계약
        </v-btn>
      </div>
    </div>

    <SmartFilterBar class="mb-4 brand-panel">
      <template #filters>
        <v-text-field
          v-model="filters.q"
          label="검색 (직원명 / 계약명 / 상태)"
          prepend-inner-icon="mdi-magnify"
          clearable
          hide-details
          density="comfortable"
          class="min-w-240"
          @keyup.enter="reload"
        />
        <v-select
          v-model="filters.status"
          :items="statusItems"
          label="계약 상태"
          clearable
          hide-details
          density="comfortable"
          style="max-width: 180px"
          @update:model-value="reload"
        />
        <v-btn
          color="primary"
          variant="flat"
          class="btn-action"
          :loading="loading"
          @click="reload"
        >
          검색
        </v-btn>
        <v-btn
          variant="outlined"
          color="grey"
          class="btn-action"
          :disabled="loading"
          @click="resetFilters"
        >
          초기화
        </v-btn>
      </template>
    </SmartFilterBar>

    <BoardList
      :headers="headers"
      :items="rows"
      :total="total"
      :loading="loading"
      :per-page="size"
      @update:page="(p) => { page = p; reload() }"
    >
      <template #cell.contract_type="{ item }">
        <v-chip
          size="small"
          color="primary"
          variant="flat"
          label
        >
          {{ item.contract_type }}
        </v-chip>
      </template>

      <template #cell.salary="{ item }">
        <div class="text-end font-weight-medium">
          ₩{{ (item.salary || 0).toLocaleString() }}
        </div>
      </template>

      <template #cell.status="{ item }">
        <v-chip
          size="small"
          :color="item.status === 'active' ? 'success' : 'grey-lighten-1'"
          :text-color="item.status === 'active' ? 'white' : 'grey-darken-1'"
          label
        >
          {{ statusLabel(item.status) }}
        </v-chip>
      </template>

      <template #cell.actions="{ item }">
        <v-btn
          size="small"
          icon="mdi-eye"
          variant="text"
          color="primary"
          @click="viewHistory(item)"
        />
        <v-btn
          size="small"
          icon="mdi-file-cog-outline"
          variant="text"
          color="error"
          @click="terminate(item)"
        />
      </template>

      <template #no-data>
        <NoDataBox
          icon="mdi-file-document-outline"
          title="계약 정보 없음"
          subtitle="검색 조건을 변경하거나 신규 계약을 등록해 보세요."
          @reset="resetFilters"
        />
      </template>
    </BoardList>

    <DialogContractForm
      v-model:open="dialogNew"
      :property-code="'MOP'"
      :biz-date="today"
      :initial="selectedContract"
      @saved="reload"
    />
    <DialogContractHistory
      v-model:open="dialogHistory"
      :contract-id="selectedId ?? ''"
    />
  </v-container>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useToast } from '@/ui/composables/useToast'
import * as ContractsApi from '@/services/contracts'
import SmartFilterBar from '@/ui/components/SmartFilterBar.vue'
import BoardList from '@/ui/components/BoardList.vue'
import NoDataBox from '@/ui/components/NoDataBox.vue'
import DialogContractForm from '@/ui/components/DialogContractForm.vue'
import DialogContractHistory from '@/ui/components/DialogContractHistory.vue'

const toast = useToast()

const today = new Date().toISOString().slice(0, 10)
const rows = ref<any[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const size = ref(20)

const filters = reactive({ q: '', status: '' })
const statusItems = [
  { title: '전체', value: '' },
  { title: '진행중', value: 'active' },
  { title: '종료', value: 'terminated' },
]

// 테이블 헤더 — 실제 DB 필드 매칭
const headers = [
  { title: 'ID', key: 'id', align: 'center' },
  { title: '직원ID', key: 'employee_id', align: 'center' },
  { title: '계약유형', key: 'contract_type' },
  { title: '시작일', key: 'start_date' },
  { title: '종료일', key: 'end_date' },
  { title: '급여형태', key: 'pay_type' },
  { title: '급여', key: 'salary', align: 'end' },
  { title: '통화', key: 'currency', align: 'center' },
  { title: '상태', key: 'status', align: 'center' },
  { title: '관리', key: 'actions', align: 'center' },
]

const dialogNew = ref(false)
const dialogHistory = ref(false)
const selectedContract = ref<any>(null)
const selectedId = ref<number | null>(null)

// 목록 로드
async function reload() {
  loading.value = true
  try {
    const res: any = await ContractsApi.list({
      page: page.value,
      size: size.value,
      q: filters.q,
      status: filters.status,
    })
    rows.value = res.items || []
    total.value = res.total || 0
  } catch {
    toast.error('계약 목록을 불러올 수 없습니다.')
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.q = ''
  filters.status = ''
  page.value = 1
  reload()
}

function statusLabel(s: string) {
  return s === 'active' ? '진행중' : '종료'
}

function openNewContract() {
  selectedContract.value = null
  dialogNew.value = true
}

function viewHistory(item: any) {
  selectedId.value = item.id
  dialogHistory.value = true
}

async function terminate(item: any) {
  if (!confirm(`'${item.contract_type}' 계약을 종료하시겠습니까?`)) return
  try {
    await ContractsApi.terminate(item.id)
    toast.success('계약이 종료되었습니다.')
    reload()
  } catch {
    toast.error('계약 종료 실패')
  }
}

onMounted(reload)
</script>

<style scoped src="@/styles/toolbar.scss"></style>
<style scoped>
.page-shell {
  max-width: 1280px;
  margin: 0 auto;
}
.brand-panel {
  background: rgb(var(--v-theme-surface));
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(16, 24, 40, 0.06);
  padding: 12px 16px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}
.btn-action {
  font-weight: 600;
  min-width: 90px;
  height: 40px;
}
</style>
