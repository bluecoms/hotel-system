<template>
  <v-container fluid class="page-shell py-6">
    <div class="bar mb-6">
      <div class="bar-left">
        <v-icon color="primary" icon="mdi-account-multiple-outline" size="22" />
        <h2 class="text-h6 font-weight-bold">직원 관리</h2>
        <span class="text-muted text-body-2">직원 목록 조회 및 업로드</span>
      </div>
      <div class="bar-right">
        <v-btn
          color="primary"
          prepend-icon="mdi-tray-arrow-up"
          variant="flat"
          class="btn-action"
          @click="openUpload"
        >
          업로드
        </v-btn>
      </div>
    </div>

    <SmartFilterBar class="mb-4 brand-panel">
      <template #filters>
        <v-text-field
          v-model="filters.q"
          label="검색 (이름, 사번, 부서, 직책, 이메일)"
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
          label="재직 상태"
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
      <template #cell.name="{ item }">
        <div class="d-flex align-center">
          <v-icon size="16" class="mr-2" color="primary">mdi-account</v-icon>
          <div>
            <div class="font-weight-medium">{{ item.name }}</div>
            <div class="text-caption text-grey-darken-1">{{ item.emp_no }}</div>
          </div>
        </div>
      </template>

      <template #cell.status="{ item }">
        <v-chip
          size="small"
          :color="item.leave_date ? 'grey-lighten-2' : 'primary'"
          :text-color="item.leave_date ? 'grey-darken-2' : 'white'"
          label
        >
          {{ item.leave_date ? '퇴사' : '재직' }}
        </v-chip>
      </template>

      <template #no-data>
        <NoDataBox
          icon="mdi-account-search-outline"
          title="검색 결과가 없습니다"
          subtitle="검색 조건을 변경하거나 초기화해 보세요."
          @reset="resetFilters"
        />
      </template>
    </BoardList>

    <DialogUpload
      v-model="dialogUpload"
      title="직원 데이터 업로드"
      endpoint="/api/hr/employees/import"
      accept=".csv,.xlsx"
      sample-url="/api/templates/employees.csv"
      :auto-refresh="true"
      @uploaded="reload"
    />
  </v-container>
</template>

<script setup lang="ts">
/**
 * Employees.vue — HR 직원 관리 (SmartFilterBar 통합형)
 */
import { ref, reactive, onMounted } from 'vue'
import { useToast } from '@/ui/composables/useToast'
import * as EmployeesApi from '@/services/employees'
import SmartFilterBar from '@/ui/components/SmartFilterBar.vue'
import BoardList from '@/ui/components/BoardList.vue'
import NoDataBox from '@/ui/components/NoDataBox.vue'
import DialogUpload from '@/ui/components/DialogUpload.vue'

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
  { title: '재직', value: 'active' },
  { title: '퇴사', value: 'leaved' },
]

// 테이블 헤더
const headers = [
  { title: '직원명 / 사번', key: 'name', sortable: true },
  { title: '부서', key: 'dept', sortable: true },
  { title: '직책', key: 'title', sortable: true },
  { title: '입사일', key: 'hire_date', sortable: true },
  { title: '상태', key: 'status', sortable: false },
]

async function reload() {
  loading.value = true
  try {
    const res: any = await EmployeesApi.list({
      page: page.value,
      size: size.value,
      q: filters.q,
      dept: filters.dept,
      status: filters.status,
      sort: sortBy.value ? `${sortBy.value.key}:${sortBy.value.order}` : '',
      prefix: '/api/hr', // HR 모듈용 prefix 추가
    })
    rows.value = res.items || []
    total.value = res.total || 0
  } catch (err: any) {
    toast.error('직원 목록을 불러올 수 없습니다.')
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.q = ''
  filters.dept = ''
  filters.status = ''
  page.value = 1
  sortBy.value = null
  reload()
}

function onSortChange(sorts: any[]) {
  if (!sorts?.length) sortBy.value = null
  else sortBy.value = { key: sorts[0].key, order: sorts[0].order }
  page.value = 1
  reload()
}

// 업로드 다이얼로그
const dialogUpload = ref(false)
function openUpload() {
  dialogUpload.value = true
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

:deep(.v-data-table__th) {
  white-space: nowrap;
  color: var(--color-muted);
  font-weight: 600;
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-line);
}
</style>
