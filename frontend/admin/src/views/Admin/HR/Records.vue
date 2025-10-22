<!-- VIEW: HR-RECORDS (src/views/Admin/HR/Records.vue) -->
<template>
  <v-container fluid class="page-shell py-6">
    <div class="bar mb-6">
      <div class="bar-left">
        <v-icon color="primary" icon="mdi-clipboard-text-clock-outline" size="22" />
        <h2 class="text-h6 font-weight-bold">근태 기록 관리</h2>
        <span class="text-muted text-body-2">직원 근무기록 조회 · 수정 · 내보내기</span>
      </div>
      <div class="bar-right">
        <v-btn
          color="primary"
          prepend-icon="mdi-cloud-refresh"
          :loading="loading"
          variant="flat"
          class="btn-action"
          @click="reload"
        >
          새로고침
        </v-btn>
      </div>
    </div>

    <SmartFilterBar class="mb-4 brand-panel">
      <template #filters>
        <v-text-field
          v-model="filters.q"
          label="검색 (직원명 / 부서 / 날짜)"
          prepend-inner-icon="mdi-magnify"
          clearable
          hide-details
          density="comfortable"
          class="min-w-240"
          @keyup.enter="reload"
        />

        <v-select
          v-model="filters.dept"
          :items="deptItems"
          label="부서"
          clearable
          hide-details
          density="comfortable"
          style="max-width: 160px"
          @update:model-value="reload"
        />

        <v-select
          v-model="filters.status"
          :items="statusItems"
          label="근무 상태"
          clearable
          hide-details
          density="comfortable"
          style="max-width: 160px"
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
      :page="page"
      :size="size"
      @update:page="(p) => { page = p; reload() }"
      @update:items-per-page="(s) => { size = s; page = 1; reload() }"
      @update:sort-by="onSortChange"
    >
      <template #cell.employee_name="{ item }">
        <div class="d-flex align-center">
          <v-icon size="16" class="mr-2" color="primary">mdi-account</v-icon>
          {{ item.employee_name }}
        </div>
      </template>

      <template #cell.work_date="{ item }">
        <div>{{ item.work_date }}</div>
      </template>

      <template #cell.status="{ item }">
        <v-chip
          size="small"
          :color="item.status === 'present' ? 'success' : item.status === 'absent' ? 'error' : 'grey-lighten-2'"
          :text-color="item.status === 'present' ? 'white' : 'grey-darken-2'"
          label
        >
          {{ statusLabel(item.status) }}
        </v-chip>
      </template>

      <template #cell.actions="{ item }">
        <v-btn
          size="small"
          icon="mdi-pencil"
          variant="text"
          color="primary"
          @click="editRecord(item)"
        />
        <v-btn
          size="small"
          icon="mdi-delete-outline"
          variant="text"
          color="error"
          @click="removeRecord(item)"
        />
      </template>

      <template #no-data>
        <StateBlock
          icon="mdi-clipboard-text-outline"
          title="근태 기록 없음"
          subtitle="검색 조건을 변경하거나 새로고침해 보세요."
          @reset="resetFilters"
        />
      </template>
    </BoardList>

    <DialogRecordEdit
      v-model="dialogEdit"
      :record="selectedRecord"
      @saved="reload"
    />
  </v-container>
</template>

<script setup lang="ts">
/**
 * Records.vue — HR 근태 기록 관리 (SmartFilterBar + BoardList 기반)
 */
import { ref, reactive, onMounted } from 'vue'
import { useToast } from '@/ui/composables/useToast'
import * as RecordsApi from '@/services/records'

// 공통 UI 컴포넌트
import SmartFilterBar from '@/ui/components/common/SmartFilterBar.vue'
import BoardList from '@/ui/components/common/BoardList.vue'
import StateBlock from '@/ui/components/common/StateBlock.vue'
import DialogRecordEdit from '@/ui/components/users/DialogRecordEdit.vue'

const toast = useToast()

// 상태
const rows = ref<any[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const size = ref(20)
const sortBy = ref<{ key: string; order: 'asc' | 'desc' } | null>(null)

// 필터
const filters = reactive({
  q: '',
  dept: '',
  status: '',
})
const deptItems = ['FRONT', 'FNB', 'ENG', 'HK', 'SUPPORT']
const statusItems = [
  { title: '전체', value: '' },
  { title: '출근', value: 'present' },
  { title: '결근', value: 'absent' },
  { title: '휴무', value: 'off' },
]

// 테이블 헤더
const headers = [
  { title: '직원명', key: 'employee_name', sortable: true },
  { title: '부서', key: 'dept', sortable: true },
  { title: '근무일자', key: 'work_date', sortable: true },
  { title: '상태', key: 'status', sortable: true },
  { title: '관리', key: 'actions', sortable: false },
]

// 상태 라벨
function statusLabel(s: string) {
  const map: any = { present: '출근', absent: '결근', off: '휴무' }
  return map[s] || '-'
}

// 데이터 로드
async function reload() {
  loading.value = true
  try {
    const res: any = await RecordsApi.list({
      page: page.value,
      size: size.value,
      q: filters.q,
      dept: filters.dept,
      status: filters.status,
      sort: sortBy.value ? `${sortBy.value.key}:${sortBy.value.order}` : '',
    })
    rows.value = res.items || []
    total.value = res.total || 0
  } catch (e: any) {
    toast.error('근태 기록을 불러올 수 없습니다.')
  } finally {
    loading.value = false
  }
}

// 필터 초기화
function resetFilters() {
  filters.q = ''
  filters.dept = ''
  filters.status = ''
  page.value = 1
  reload()
}

// 정렬 변경
function onSortChange(sorts: any[]) {
  if (!sorts?.length) sortBy.value = null
  else sortBy.value = { key: sorts[0].key, order: sorts[0].order }
  page.value = 1
  reload()
}

// 다이얼로그 관리
const dialogEdit = ref(false)
const selectedRecord = ref<any>(null)

function editRecord(item: any) {
  selectedRecord.value = item
  dialogEdit.value = true
}

async function removeRecord(item: any) {
  if (!confirm(`'${item.employee_name}'의 근태 기록을 삭제하시겠습니까?`)) return
  try {
    await RecordsApi.remove(item.id)
    toast.success('기록이 삭제되었습니다.')
    reload()
  } catch (e: any) {
    toast.error('삭제 실패')
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

/* SmartFilterBar 일원화 스타일 */
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

/* 버튼 */
.btn-action {
  font-weight: 600;
  min-width: 90px;
  height: 40px;
}

/* 테이블 헤더 */
:deep(.v-data-table__th) {
  white-space: nowrap;
  color: var(--color-muted);
  font-weight: 600;
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-line);
}
</style>
