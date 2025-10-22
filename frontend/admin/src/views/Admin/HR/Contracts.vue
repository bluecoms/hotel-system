<!-- ============================================================================
  File      : src/views/Admin/HR/Contracts.vue
  Version   : 2025.10 v4.2-Final (SSOT · Merge · Scan-Upload Activate)
  Purpose   : Hotel Admin — HR 직원 계약 관리 (미계약자 포함 + 스캔본 업로드 확정)
  ------------------------------------------------------------------------------
  변경 요약 (v4.2)
    ✅ 직원 목록과 계약 목록 병합 유지(LEFT JOIN 개념) — employees + contracts 병합
    ✅ 필터/정렬/페이지/사이즈 동기화 — BoardList 이벤트 표준 반영
    ✅ 액션 추가: "스캔본 업로드" → 업로드 성공 시 즉시 activate → Employee 동기화
    ✅ 계약 상태 chip 색상/라벨 정리 (none/active/terminated)
    ✅ 계약서 작성(스튜디오) 진입 시 현재 행의 id/employee_id 안전 전달
    ✅ 오류/토스트 메시지 일관화, 빈 데이터 상태 메시지 보강
  ------------------------------------------------------------------------------
  운영 플로우(권장):
    1) 신규 계약은 별도 화면/다이얼로그(DialogContractForm)에서 기본정보 입력(draft)
    2) 스캔본 업로드(날인본 PDF/JPG) → 업로드 성공 시 백엔드에서 계약 activate
    3) 필요시 "계약서 작성(온라인)"으로 PDF 인쇄 후 스캔, 이후 다시 업로드
  ------------------------------------------------------------------------------
  주의:
    • BoardList의 이벤트는 update:page / update:items-per-page / update:sort-by 를 사용
    • sort 파라미터는 "key:order" 문자열로 ContractsApi.list에 전달(백엔드 미지원 시 무시해도 무해)
    • employees 병합은 현재 페이지 기준 단순 매칭 — 대규모 데이터셋이면 백엔드에서 JOIN API 제공 권장
============================================================================ -->
<template>
  <v-container fluid class="page-shell py-6">
    <!-- ───── Toolbar ───── -->
    <div class="bar mb-6">
      <div class="bar-left">
        <v-icon color="primary" icon="mdi-file-document-outline" size="22" />
        <h2 class="text-h6 font-weight-bold">직원 계약 관리</h2>
        <span class="text-muted text-body-2">계약 등록 · 스캔본 업로드 확정 · 이력 관리</span>
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

    <!-- ───── SmartFilterBar ───── -->
    <SmartFilterBar class="mb-4 brand-panel">
      <template #filters>
        <v-text-field
          v-model="filters.q"
          label="검색 (직원명 / 사번 / 상태)"
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
          style="max-width: 160px"
          @update:model-value="reload"
        />
        <v-text-field
          v-model="filters.biz_date"
          label="Business Date"
          type="date"
          density="comfortable"
          hide-details
          style="max-width: 180px"
        />
        <v-btn color="primary" variant="flat" class="btn-action" :loading="loading" @click="reload">
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

    <!-- ───── 계약 목록 ───── -->
    <BoardList
      title="계약 목록"
      :headers="headers"
      :items="rowsView"
      :total="total"
      :loading="loading"
      :page="page"
      :size="size"
      :sort-by="sortByArr"
      @update:page="(p) => { page = p; reload() }"
      @update:items-per-page="(s) => { size = s; page = 1; reload() }"
      @update:sort-by="onSortChange"
    >
      <!-- 직원 -->
      <template #cell.emp="{ item }">
        <div class="d-flex align-center">
          <v-icon size="16" class="mr-2" color="primary">mdi-account</v-icon>
          <div>
            <div class="font-weight-medium">{{ item.emp_name || '직원' }}</div>
            <div class="text-caption text-grey-darken-1">
              {{ item.emp_no ? `사번 ${item.emp_no}` : `ID ${item.employee_id}` }}
            </div>
          </div>
        </div>
      </template>

      <!-- 계약유형 -->
      <template #cell.contract_type="{ item }">
        <v-chip size="small" color="primary" variant="flat" label>
          {{ contractTypeLabel(item.contract_type) }}
        </v-chip>
      </template>

      <!-- 계약 시작일 -->
      <template #cell.start_date="{ item }">
        {{ item.start_date ? fmtDate(item.start_date) : (item.contract_start ? fmtDate(item.contract_start) : '-') }}
      </template>

      <!-- 계약 종료일 -->
      <template #cell.end_date="{ item }">
        {{ item.end_date ? fmtDate(item.end_date) : (item.contract_end ? fmtDate(item.contract_end) : '-') }}
      </template>

      <!-- 급여 -->
      <template #cell.salary="{ item }">
        <div class="text-end font-weight-medium">
          ₩{{ fmtNum(item.salary || 0) }}
        </div>
      </template>

      <!-- 계약 상태 -->
      <template #cell.status="{ item }">
        <v-chip
          size="small"
          :color="statusColor(item.status)"
          :text-color="statusTextColor(item.status)"
          label
        >
          {{ statusLabel(item.status) }}
        </v-chip>
      </template>

      <!-- 관리 -->
      <template #cell.actions="{ item }">
        <!-- 계약서 작성(온라인 미리작성/인쇄) -->
        <v-tooltip text="계약서 작성 (온라인 템플릿)">
          <template #activator="{ props }">
            <v-btn
              v-bind="props"
              size="small"
              icon="mdi-file-document-edit-outline"
              color="primary"
              variant="text"
              @click="openStudio(item)"
            />
          </template>
        </v-tooltip>

        <!-- 계약 이력 -->
        <v-tooltip text="계약 이력 보기">
          <template #activator="{ props }">
            <v-btn
              v-bind="props"
              size="small"
              icon="mdi-history"
              color="info"
              variant="text"
              @click="viewHistory(item)"
            />
          </template>
        </v-tooltip>

        <!-- 스캔본 업로드 → 확정 -->
        <v-tooltip text="스캔본 업로드(날인본) 후 즉시 확정">
          <template #activator="{ props }">
            <v-btn
              v-bind="props"
              size="small"
              icon="mdi-file-upload-outline"
              color="success"
              variant="text"
              @click="triggerUpload(item)"
            />
          </template>
        </v-tooltip>

        <!-- 계약 종료 -->
        <v-tooltip text="계약 종료 처리">
          <template #activator="{ props }">
            <v-btn
              v-bind="props"
              size="small"
              icon="mdi-file-cog-outline"
              color="error"
              variant="text"
              @click="terminate(item)"
            />
          </template>
        </v-tooltip>
      </template>

      <!-- 데이터 없음 -->
      <template #no-data>
        <StateBlock
          icon="mdi-file-document-outline"
          title="계약 정보 없음"
          subtitle="검색 조건을 변경하거나 신규 계약을 등록해 보세요."
          @reset="resetFilters"
        />
      </template>
    </BoardList>

    <!-- ───── 다이얼로그 ───── -->
    <DialogContractForm v-model:open="dialogForm" @saved="onContractSaved" />
    <DialogContractStudio v-model:open="dialogStudio" :contract="selectedContract" @saved="onContractSaved" />
    <DialogContractHistory v-model:open="dialogHistory" :contract-id="selectedId ?? ''" />

    <!-- 숨김 파일 입력 (스캔본 업로드용) -->
    <input
      ref="fileInputRef"
      type="file"
      accept=".pdf,.jpg,.jpeg,.png"
      class="d-none"
      @change="onFilePicked"
    />
    <!-- 업로드 시 기간 받는 작은 다이얼로그 -->
    <v-dialog v-model="uploadDlg.open" max-width="420">
      <v-card>
        <v-card-title>스캔본 업로드</v-card-title>
        <v-card-text>
          <div class="text-body-2 mb-2">
            날인된 계약서 스캔본(PDF/JPG/PNG)을 업로드하면 <b>즉시 계약 확정</b>됩니다.
          </div>
          <v-text-field
            v-model="uploadDlg.start_date"
            type="date"
            label="계약 시작일"
            density="comfortable"
            hide-details
            class="mb-2"
          />
          <v-text-field
            v-model="uploadDlg.end_date"
            type="date"
            label="계약 종료일(선택)"
            density="comfortable"
            hide-details
          />
          <div class="text-caption text-grey mt-2">
            * 종료일 미입력 시 '진행중'으로 간주합니다.
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="uploadDlg.open=false">취소</v-btn>
          <v-btn color="primary" :loading="uploadDlg.loading" @click="pickFile">파일 선택</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
/* ===========================================================================
   Script: Contracts.vue
   핵심:
     • employees + contracts 병합 리스트
     • 필터/정렬/페이지 연동(BoardList 이벤트 표준)
     • 스캔본 업로드 → 업로드 성공 시 즉시 activate
     • 계약서 작성/이력/종료 액션
=========================================================================== */
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useToast } from '@/ui/composables/useToast'
import * as ContractsApi from '@/services/contracts'
import * as EmployeesApi from '@/services/employees'
import SmartFilterBar from '@/ui/components/common/SmartFilterBar.vue'
import BoardList from '@/ui/components/common/BoardList.vue'
import StateBlock from '@/ui/components/common/StateBlock.vue'
import DialogContractForm from '@/ui/components/hr/DialogContractForm.vue'
import DialogContractStudio from '@/ui/components/hr/DialogContractStudio.vue'
import DialogContractHistory from '@/ui/components/hr/DialogContractHistory.vue'

const toast = useToast()
const emit = defineEmits<{ (e: 'updated'): void }>()

/** 테이블 상태 */
const rows = ref<any[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const size = ref(20)

/** 정렬 상태 (BoardList는 배열로 내려줌 → 단일만 사용) */
const sortBy = ref<{ key: string; order: 'asc' | 'desc' } | null>(null)
const sortByArr = computed(() => (sortBy.value ? [sortBy.value] : []))
function onSortChange(sorts: any[]) {
  sortBy.value = (!Array.isArray(sorts) || !sorts.length)
    ? null
    : { key: sorts[0].key, order: sorts[0].order }
  page.value = 1
  reload()
}

/** property_code (상단 바/전역) */
const propertyCode =
  localStorage.getItem('property_code') ||
  import.meta.env.VITE_DEFAULT_PROPERTY_CODE ||
  'MOP'

/** 필터 */
const filters = reactive({
  q: '',
  status: '',
  biz_date: new Date().toISOString().slice(0, 10),
})
const statusItems = [
  { title: '전체', value: '' },
  { title: '진행중', value: 'active' },
  { title: '종료', value: 'terminated' },
  { title: '미계약', value: 'none' },
]

/** 테이블 헤더 */
const headers = [
  { title: '직원', key: 'emp', sortable: false },
  { title: '계약유형', key: 'contract_type', sortable: false },
  { title: '계약 시작일', key: 'start_date', sortable: true },
  { title: '계약 종료일', key: 'end_date', sortable: true },
  { title: '급여', key: 'salary', align: 'end', sortable: true },
  { title: '계약 상태', key: 'status', align: 'center', sortable: false },
  { title: '관리', key: 'actions', align: 'center', sortable: false },
]

/** 보기용 데이터 (계약 + 미계약 병합 뷰) */
const rowsView = computed(() =>
  (rows.value || []).map((r) => ({
    ...r,
    start_date: r.start_date || r.contract_start || null,
    end_date: r.end_date || r.contract_end || null,
  }))
)

/** 숫자/날짜 유틸 */
function fmtNum(n: number) {
  try { return n.toLocaleString() } catch { return String(n) }
}
function fmtDate(s?: string | null) {
  if (!s) return '-'
  return String(s).slice(0, 10)
}

/** 목록 로드 (employees + contracts 병합) */
async function reload() {
  loading.value = true
  try {
    const sort = sortBy.value ? `${sortBy.value.key}:${sortBy.value.order}` : ''
    const [contractsRes, employeesRes] = await Promise.all([
      ContractsApi.list({
        property_code: propertyCode,
        q: (filters.q || '').trim() || undefined,
        status: (filters.status || undefined),
        biz_date: (filters.biz_date || undefined),
        page: page.value,
        size: size.value,
        sort,
      }),
      EmployeesApi.list({ property_code: propertyCode }),
    ])

    const contracts = contractsRes?.items || []
    const employees = employeesRes?.items || []

    // 직원 기준 병합 — 동일 employee_id의 최신 계약을 테이블에 표시,
    // 없으면 미계약 행으로 채움.
    const merged = employees.map((emp: any) => {
      const c = contracts.find((x: any) => x.employee_id === emp.id)
      return c
        ? {
            ...c,
            emp_name: emp.name,
            emp_no: emp.emp_no,
            status: c.status || emp.contract_status || 'active',
          }
        : {
            id: `emp-${emp.id}`,
            employee_id: emp.id,
            emp_name: emp.name,
            emp_no: emp.emp_no,
            contract_type: '-',
            start_date: emp.contract_start || null,
            end_date: emp.contract_end || null,
            salary: 0,
            status: emp.contract_status || 'none',
          }
    })

    // 페이지네이션 일관성:
    // - 현재는 employees 전체를 기준으로 병합하므로 total은 merged 길이.
    // - 대량 데이터에서 서버 페이지네이션이 필요하면 백엔드 JOIN API 권장.
    rows.value = merged
    total.value = merged.length
  } catch (e) {
    console.error('[Contracts.reload]', e)
    toast.error('계약 목록을 불러올 수 없습니다.')
  } finally {
    loading.value = false
  }
}

/** 필터 초기화 */
function resetFilters() {
  filters.q = ''
  filters.status = ''
  filters.biz_date = new Date().toISOString().slice(0, 10)
  page.value = 1
  sortBy.value = null
  reload()
}

/** 상태 라벨/색상 */
function statusLabel(s?: string) {
  switch (s) {
    case 'active': return '계약중'
    case 'terminated': return '종료'
    case 'none': return '미계약'
    default: return '-'
  }
}
function statusColor(s?: string) {
  switch (s) {
    case 'active': return 'success'
    case 'terminated': return 'error'
    case 'none': return 'grey'
    default: return 'grey-lighten-1'
  }
}
function statusTextColor(s?: string) {
  return s === 'none' ? 'grey-darken-2' : 'white'
}

/** 계약유형 라벨 */
function contractTypeLabel(raw?: string) {
  return raw && raw !== '-' ? '정규직(월급제)' : '-'
}

/** 액션: 신규 계약 */
const dialogForm = ref(false)
function openNewContract() { dialogForm.value = true }

/** 액션: 계약서 스튜디오(온라인 작성) */
const dialogStudio = ref(false)
const selectedContract = ref<any>(null)
function openStudio(item: any) {
  const cid = item?.id ?? item?.contract_id
  selectedContract.value = { ...item, id: cid }
  dialogStudio.value = true
}

/** 액션: 계약 이력 */
const dialogHistory = ref(false)
const selectedId = ref<number | null>(null)
function viewHistory(item: any) {
  selectedId.value = typeof item?.id === 'number' ? item.id : null
  dialogHistory.value = true
}

/** 액션: 계약 종료 */
async function terminate(item: any) {
  if (!item?.id || String(item.id).startsWith('emp-')) {
    toast.error('종료할 계약이 없습니다.')
    return
  }
  if (!confirm(`'${item.emp_name || '직원'}' 계약을 종료하시겠습니까?`)) return
  try {
    await ContractsApi.terminate(item.id)
    toast.success('계약이 종료되었습니다.')
    reload()
  } catch (e: any) {
    toast.error('계약 종료 실패')
  }
}

/** 액션: 스캔본 업로드 → activate */
const fileInputRef = ref<HTMLInputElement | null>(null)
const uploadDlg = reactive({
  open: false,
  targetId: null as number | null,
  start_date: new Date().toISOString().slice(0, 10),
  end_date: '',
  loading: false,
})
function triggerUpload(item: any) {
  const cid = (typeof item?.id === 'number') ? item.id : (item?.contract_id ?? null)
  if (!cid) {
    toast.error('업로드할 계약이 없습니다. 먼저 계약을 생성하세요.')
    return
  }
  uploadDlg.targetId = cid
  uploadDlg.start_date = (item.start_date || item.contract_start || new Date().toISOString().slice(0,10))?.slice(0,10)
  uploadDlg.end_date = (item.end_date || item.contract_end || '')?.slice?.(0,10) || ''
  uploadDlg.open = true
}
function pickFile() {
  fileInputRef.value?.click()
}
async function onFilePicked(e: Event) {
  const el = e.target as HTMLInputElement
  const file = el.files?.[0]
  el.value = '' // 같은 파일 재선택 가능하도록 초기화
  if (!file || !uploadDlg.targetId) return
  try {
    uploadDlg.loading = true
    await ContractsApi.uploadScan(
      uploadDlg.targetId,
      file,
      {
        start_date: uploadDlg.start_date || null,
        end_date: uploadDlg.end_date || null,
      },
    )
    // 업로드에 성공하면 서버에서 activate까지 수행(권장).
    // 만약 서버에서 분리되어 있다면 아래 activate 호출 유지:
    // await ContractsApi.activate(uploadDlg.targetId)

    toast.success('스캔본 업로드 및 계약 확정이 완료되었습니다.')
    uploadDlg.open = false
    reload()
  } catch (err: any) {
    console.error('[uploadScan]', err)
    toast.error('업로드 실패: ' + (err?.message || '서버 오류'))
  } finally {
    uploadDlg.loading = false
  }
}

/** 공통: 저장/확정 후 동기화 */
function onContractSaved() {
  reload()
  emit?.('updated')
}

/** 초기 로드 */
onMounted(reload)
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
.d-none { display: none; }
</style>
