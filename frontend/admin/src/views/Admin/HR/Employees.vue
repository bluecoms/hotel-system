<!-- ============================================================================
  File    : src/views/Admin/HR/Employees.vue
  Version : 2025.10 Final Stable (v3.7.0 · SSOT / Property Sync / EndGuard Fix)
  Purpose : Hotel Admin — HR 직원 목록/관리 화면 (Property 기반)
  ------------------------------------------------------------------------------
  연결 백엔드:
    • GET    /api/employees?property_code=MOP  → 직원 목록 조회 (계약상태/기간 포함)
    • POST   /api/employees                    → 신규 등록
    • PUT    /api/employees/{id}               → 수정
    • DELETE /api/employees/{id}               → 삭제(Soft Delete)
    • POST   /api/contracts/terminate/{id}     → 계약 종료 (날짜 지정 미지원)
  ------------------------------------------------------------------------------
  변경사항
    v3.7.0
      ✅ today 상수 누락 오류 수정 (DialogUpload에 전달)
      ✅ '계약 종료' 버튼 가드: contract_id 없거나 status≠active → 비활성 + title
      ✅ openEndDialog() 가드 시 조용히 리턴(불필요 토스트 제거)
    v3.6.2
      ✅ 부서 목록 로드: options 엔드포인트 사용(title/value)
      ✅ 계약 종료: ContractsApi.terminate(contract_id)로 교체
      ✅ 계약 상태 라벨/색상에 'none(미계약)' 반영
============================================================================ -->

<template>
  <v-container fluid class="page-shell py-6">
    <!-- ───── Toolbar ───── -->
    <div class="bar mb-6">
      <div class="bar-left">
        <v-icon color="primary" icon="mdi-account-multiple-outline" size="22" />
        <h2 class="text-h6 font-weight-bold">직원 관리</h2>
        <span class="text-muted text-body-2">직원 목록 조회, 등록 및 업로드</span>
      </div>
      <div class="bar-right d-flex align-center gap-3">
        <v-btn
          color="primary"
          prepend-icon="mdi-account-plus"
          variant="elevated"
          class="btn-action"
          @click="openCreate"
        >
          신규 등록
        </v-btn>
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

    <!-- ───── SmartFilterBar ───── -->
    <SmartFilterBar class="mb-4 brand-panel">
      <template #filters>
        <v-text-field
          v-model="filters.q"
          label="검색 (이름 / 사번 / 부서)"
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
          hide-details
          clearable
          density="comfortable"
          style="max-width: 180px"
          @update:model-value="reload"
        />
        <v-select
          v-model="filters.status"
          :items="statusItems"
          label="재직 상태"
          hide-details
          clearable
          density="comfortable"
          style="max-width: 180px"
          @update:model-value="reload"
        />
        <v-btn color="primary" variant="flat" class="btn-action" :loading="loading" @click="reload">
          검색
        </v-btn>
        <v-btn variant="outlined" color="grey" class="btn-action" @click="resetFilters">
          초기화
        </v-btn>
      </template>
    </SmartFilterBar>

    <!-- ───── 직원 목록 ───── -->
    <BoardList
      title="직원 목록"
      :headers="headers"
      :items="rows"
      :total="total"
      :loading="loading"
      :page="page"
      :size="size"
      :sort-by="sortByArr"
      :row-clickable="false"
      @update:page="(p) => { page = p; reload() }"
      @update:items-per-page="(s) => { size = s; page = 1; reload() }"
      @update:sort-by="onSortChange"
    >
      <!-- 직원명 / 사번 -->
      <template #cell.name="{ item }">
        <div class="d-flex align-center">
          <v-icon size="16" class="mr-2" color="primary">mdi-account</v-icon>
          <div>
            <div class="font-weight-medium">{{ item.name }}</div>
            <div class="text-caption text-grey-darken-1">{{ item.emp_no }}</div>
          </div>
        </div>
      </template>

      <!-- 부서 -->
      <template #cell.dept="{ item }">{{ item.dept_name || item.dept || '-' }}</template>

      <!-- 직책 -->
      <template #cell.title_name="{ item }">{{ item.title_name || '-' }}</template>

      <!-- 입사일 -->
      <template #cell.hire_date="{ item }">
        {{ item.hire_date ? item.hire_date.slice(0,10) : '-' }}
      </template>

      <!-- 계약 상태 -->
      <template #cell.contract_status="{ item }">
        <v-chip
          size="small"
          :color="contractColor(item.contract_status)"
          :text-color="contractTextColor(item.contract_status)"
          label
        >
          {{ contractLabel(item.contract_status) }}
        </v-chip>
      </template>

      <!-- 계약 시작일 -->
      <template #cell.contract_start="{ item }">
        {{ item.contract_start ? item.contract_start.slice(0,10) : '-' }}
      </template>

      <!-- 계약 종료일 -->
      <template #cell.contract_end="{ item }">
        <div class="d-flex align-center">
          <span v-if="item.contract_end">{{ item.contract_end.slice(0,10) }}</span>
          <v-btn
            v-else
            color="error"
            size="small"
            variant="tonal"
            :disabled="!item.contract_id || item.contract_status !== 'active'"
            :title="!item.contract_id ? '종료할 계약이 없습니다.' : (item.contract_status !== 'active' ? '진행중인 계약만 종료할 수 있습니다.' : '')"
            @click.stop="openEndDialog(item)"
          >
            계약 종료
          </v-btn>
        </div>
      </template>

      <!-- 재직 상태 -->
      <template #cell.status="{ item }">
        <v-chip
          size="small"
          :color="item.leave_date ? 'grey-lighten-2' : 'primary'"
          :text-color="item.leave_date ? 'grey-darken-2' : 'white'"
          label
        >
          {{ item.leave_date ? '퇴직' : '재직' }}
        </v-chip>
      </template>

      <!-- 데이터 없음 -->
      <template #no-data>
        <StateBlock
          icon="mdi-account-search-outline"
          title="직원 정보 없음"
          subtitle="검색 조건을 변경하거나 새로 등록해 보세요."
          @reset="resetFilters"
        />
      </template>
    </BoardList>

    <!-- ───── 직원 등록 / 업로드 다이얼로그 ───── -->
    <DialogEmployeeForm v-model:open="dialogCreate" @saved="onCreated" />
    <DialogUpload
      v-model:open="dialogUpload"
      title="직원 데이터 업로드"
      dataset="employees"
      :bizDate="today"
      :auto-refresh="true"
      :propertyCode="propertyCode"
    />

    <!-- 계약 종료 확인 -->
    <v-dialog v-model="endDlg.open" max-width="400">
      <v-card>
        <v-card-title>계약 종료</v-card-title>
        <v-card-text>선택한 직원의 현재 계약을 종료하시겠습니까?</v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="endDlg.open=false">취소</v-btn>
          <v-btn color="primary" @click="confirmEnd" :loading="endDlg.loading">종료</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
/* ===========================================================================
   직원 목록/관리 — Property Sync + SmartFilterBar 일원화
=========================================================================== */
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useToast } from '@/ui/composables/useToast'
import * as EmployeesApi from '@/services/employees'
import * as MasterApi from '@/services/master'
import * as ContractsApi from '@/services/contracts'
import SmartFilterBar from '@/ui/components/common/SmartFilterBar.vue'
import BoardList from '@/ui/components/common/BoardList.vue'
import StateBlock from '@/ui/components/common/StateBlock.vue'
import DialogUpload from '@/ui/components/closing/DialogUpload.vue'
import DialogEmployeeForm from '@/ui/components/hr/DialogEmployeeForm.vue'

const toast = useToast()

/** today: DialogUpload에 필요한 영업일(누락 보정) */
const today = new Date().toISOString().slice(0, 10)

const rows = ref<any[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const size = ref(20)
const sortBy = ref<{ key: string; order: 'asc' | 'desc' } | null>(null)
const sortByArr = computed(() => (sortBy.value ? [sortBy.value] : []))

/** property_code 자동 반영 */
const propertyCode =
  localStorage.getItem('property_code') ||
  import.meta.env.VITE_DEFAULT_PROPERTY_CODE ||
  'MOP'

/** 필터 */
const filters = reactive({ q: '', dept: '', status: '' })

/** 부서 목록 — options 엔드포인트 사용(title/value) */
const deptItems = ref<{ title: string; value: string }[]>([])
async function loadDepts() {
  try {
    const opts = await MasterApi.departmentOptions({ property_code: propertyCode })
    // opts: [{ title, value }]
    deptItems.value = Array.isArray(opts) ? opts : []
  } catch {
    deptItems.value = []
  }
}

const statusItems = [
  { title: '전체', value: '' },
  { title: '재직', value: 'active' },
  { title: '퇴직', value: 'leaved' },
]

/** 테이블 헤더 */
const headers = [
  { title: '직원명 / 사번', key: 'name', sortable: true },
  { title: '부서', key: 'dept', sortable: true },
  { title: '직책', key: 'title_name', sortable: true },
  { title: '입사일', key: 'hire_date', sortable: true },
  { title: '계약 상태', key: 'contract_status', sortable: false },
  { title: '계약 시작일', key: 'contract_start', sortable: false },
  { title: '계약 종료일', key: 'contract_end', sortable: false },
  { title: '상태', key: 'status', sortable: false },
]

/** 목록 재로드 */
async function reload() {
  loading.value = true
  try {
    const res = await EmployeesApi.list({
      page: page.value,
      size: size.value,
      q: filters.q,
      dept: filters.dept,
      status: filters.status,
      property_code: propertyCode,
      sort: sortBy.value ? `${sortBy.value.key}:${sortBy.value.order}` : '',
    })
    rows.value = []
    await nextTick()
    rows.value = res.items || []
    total.value = res.total || 0
  } catch {
    toast.error('직원 목록을 불러올 수 없습니다.')
  } finally {
    loading.value = false
  }
}

/** 필터 초기화 */
function resetFilters() {
  filters.q = filters.dept = filters.status = ''
  page.value = 1
  sortBy.value = null
  reload()
}

/** 정렬 변경 */
function onSortChange(sorts: any[]) {
  sortBy.value = (!Array.isArray(sorts) || !sorts.length)
    ? null
    : { key: sorts[0].key, order: sorts[0].order }
  page.value = 1
  reload()
}

/** 계약 상태 표기 */
function contractLabel(s?: string) {
  switch (s) {
    case 'active': return '계약중'
    case 'terminated': return '종료'
    case 'none': return '미계약'
    default: return '미계약'
  }
}
function contractColor(s?: string) {
  if (s === 'active') return 'primary'
  if (s === 'terminated') return 'error'
  if (s === 'none') return 'grey'
  return 'grey-lighten-2'
}
function contractTextColor(s?: string) {
  return (s === 'active' || s === 'terminated') ? 'white' : 'grey-darken-2'
}

/** 다이얼로그 제어 */
const dialogUpload = ref(false)
const dialogCreate = ref(false)
function openUpload() { dialogUpload.value = true }
function openCreate() { dialogCreate.value = true }
function onCreated() { toast.success('직원이 등록되었습니다.'); reload() }

/** 계약 종료 다이얼로그 */
const endDlg = reactive({ open: false, loading: false, target: null as any })
function openEndDialog(item: any) {
  // 직원 목록에서 최신 계약 id를 contract_id로 전달받는 구조.
  // 유효한 진행중 계약만 종료 가능하도록 가드.
  if (!item?.contract_id || item?.contract_status !== 'active') return
  endDlg.target = item
  endDlg.open = true
}
async function confirmEnd() {
  if (!endDlg.target?.contract_id) return
  try {
    endDlg.loading = true
    await ContractsApi.terminate(endDlg.target.contract_id)
    toast.success('계약이 종료되었습니다.')
    endDlg.open = false
    reload()
  } catch (e: any) {
    toast.error('종료 실패: ' + (e?.message || '서버 오류'))
  } finally {
    endDlg.loading = false
  }
}

/** 초기 로드 */
onMounted(async () => {
  await loadDepts()
  await reload()
})
</script>

<style scoped src="@/styles/toolbar.scss"></style>
<style scoped>
.page-shell { max-width: 1280px; margin: 0 auto; }
.brand-panel {
  background: rgb(var(--v-theme-surface));
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(16, 24, 40, 0.06);
  padding: 12px 16px;
  display: flex; align-items: center; flex-wrap: wrap; gap: 12px;
}
.btn-action { font-weight: 600; min-width: 90px; height: 40px; }
:deep(.v-data-table__th) {
  white-space: nowrap;
  color: var(--color-muted);
  font-weight: 600;
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-line);
}
</style>
