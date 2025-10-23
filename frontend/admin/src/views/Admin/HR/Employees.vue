<!-- ============================================================================
  File    : src/views/Admin/HR/Employees.vue
  Version : 2025.10 Final Stable (v3.9.1 · 목록전용 컬럼정리 · 상세필드 비노출 · UI정비)
  Purpose : Hotel Admin — HR '직원 목록' 화면 (요약 전용 테이블 + 필터/등록/업로드)
  ------------------------------------------------------------------------------
  이번 패치 핵심 ( 상세 페이지 필드가 목록에 섞여 보이던 문제 해결)
    ✅ 목록 화면은 “요약 필드만” 노출: [ID, 사번, 이름, 부서(한글), 직책(한글), 입사일, 연락처, 계약상태]
    ✅ 상세용 원시 필드( Property_code / Dept / Title / Title_name 중복 / Dept_name 중복 / 계약기간 등 ) 목록에서 제거
    ✅ 테이블 rows 를 ‘요약전용 Shape’로 재구성하여 불필요 키 자체를 내려보내지 않음
    ✅ SmartFilterBar의 Property 선택 숨김(:show-property="false"), 조회/초기화 버튼 중복 제거
    ✅ 부서/직책 한글명 Fallback(옵션 맵) 유지
    ✅ 계약 종료 기능은 Contracts.vue 로 완전 이관(본 화면에서는 상태칩만 표시)
  ------------------------------------------------------------------------------
  연결 백엔드
    • GET    /api/employees?property_code=MOP  → 목록(요약필드만 추출)
    • POST   /api/employees                    → 신규 등록 (계약 필드 동시 전송 가능)
    • PUT    /api/employees/{id}               → 수정
    • DELETE /api/employees/{id}               → 삭제(Soft Delete)
  ------------------------------------------------------------------------------
  주의
    • 목록은 “요약” 전용입니다. 상세 필드는 UserDetail.vue/Employee 단건 API로 확인합니다.
    • 계약 등록/이력/종료/스캔업로드는 Contracts.vue에서 수행합니다.
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

    <!-- ───── SmartFilterBar (Property 숨김 + 조회/초기화 단일화) ───── -->
    <SmartFilterBar
      class="mb-4 brand-panel"
      :show-property="false"
      @search="onSearch"
      @reset="resetFilters"
    >
      <template #filters>
        <!-- 검색어 (이름/사번/부서코드) -->
        <v-text-field
          v-model="filters.q"
          label="검색 (이름 / 사번 / 부서코드)"
          prepend-inner-icon="mdi-magnify"
          clearable hide-details density="comfortable"
          class="min-w-240"
          @keyup.enter="reload"
        />
        <!-- 부서코드 선택: 서버 필터와 일치 (AD/MG/… 등 코드 기준) -->
        <v-select
          v-model="filters.dept"
          :items="deptItems"
          label="부서"
          item-title="title"
          item-value="value"
          clearable hide-details density="comfortable"
          style="max-width: 180px"
          @update:model-value="reload"
        />
        <!-- 계약 상태 필터 (none/active/terminated) -->
        <v-select
          vrazil="filters.status"
          v-model="filters.status"
          :items="statusItems"
          label="계약 상태"
          clearable hide-details density="comfortable"
          style="max-width: 180px"
          @update:model-value="reload"
        />
      </template>
    </SmartFilterBar>

    <!-- ───── 목록 테이블 (요약전용 컬럼만 렌더) ───── -->
    <BoardList
      title="직원 목록"
      :headers="headers"
      :items="rows"            <!-- rows 는 요약형 Shape로만 구성됨 -->
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
      <!-- ID -->
      <template #cell.id="{ item }">
        {{ item.id }}
      </template>

      <!-- 사번 -->
      <template #cell.emp_no="{ item }">
        <div class="d-flex align-center">
          <v-icon size="16" class="mr-2" color="primary">mdi-account</v-icon>
          <span class="font-weight-medium">{{ item.emp_no }}</span>
        </div>
      </template>

      <!-- 이름 -->
      <template #cell.name="{ item }">
        {{ item.name }}
      </template>

      <!-- 부서(한글명만) -->
      <template #cell.dept_name="{ item }">
        {{ item.dept_name || '-' }}
      </template>

      <!-- 직책(한글명만) -->
      <template #cell.title_name="{ item }">
        {{ item.title_name || '-' }}
      </template>

      <!-- 입사일(YYYY-MM-DD) -->
      <template #cell.hire_date="{ item }">
        {{ item.hire_date ? item.hire_date.slice(0,10) : '-' }}
      </template>

      <!-- 연락처 -->
      <template #cell.phone="{ item }">
        {{ item.phone || '-' }}
      </template>

      <!-- 계약 상태 (요약용 칩) -->
      <template #cell.contract_status="{ item }">
        <v-chip :color="contractColor(item.contract_status)"
                :text-color="contractTextColor(item.contract_status)"
                size="small" label>
          {{ contractLabel(item.contract_status) }}
        </v-chip>
      </template>

      <!-- 데이터 없음 -->
      <template #no-data>
        <StateBlock
          icon="mdi-account-search-outline"
          title="직원 정보 없음"
          :message="'검색 조건을 변경하거나 새로 등록해 보세요.'"
          @reset="resetFilters"
        />
      </template>
    </BoardList>

    <!-- ───── 직원 등록 / 업로드 다이얼로그 ───── -->
    <DialogEmployeeForm
      v-model:open="dialogCreate"
      :include-contract="true"
      @saved="onCreated"
    />
    <DialogUpload
      v-model:open="dialogUpload"
      title="직원 데이터 업로드"
      dataset="employees"
      :bizDate="today"
      :auto-refresh="true"
      :propertyCode="propertyCode"
      @done="onUploadDone"
      @uploaded="onUploadDone"
    />
  </v-container>
</template>

<script setup lang="ts">
/* ===========================================================================
   Script — 목록 전용 요약 화면
   ---------------------------------------------------------------------------
   • rows: 요약형 Shape만 담아 v-data-table에 전달 (상세필드는 제거)
   • headers: 요약 컬럼만 지정 → v-data-table 자동 컬럼생성 차단
   • dept/title 한글명은 옵션 맵으로 Fallback
   • 계약 종료/기간/Property 등은 본 화면에서 숨김
=========================================================================== */
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useToast } from '@/ui/composables/useToast'
import * as EmployeesApi from '@/services/employees'
import * as MasterApi from '@/services/master'
import SmartFilterBar from '@/ui/components/common/SmartFilterBar.vue'
import BoardList from '@/ui/components/common/BoardList.vue'
import StateBlock from '@/ui/components/common/StateBlock.vue'
import DialogUpload from '@/ui/components/closing/DialogUpload.vue'
import DialogEmployeeForm from '@/ui/components/hr/DialogEmployeeForm.vue'

const toast = useToast()

/** today: DialogUpload에 필요한 기본값(영업일) */
const today = new Date().toISOString().slice(0, 10)

/** 테이블 상태 (요약형 rows) */
const rows = ref<Array<{
  id: number
  emp_no: string
  name: string
  dept_name: string
  title_name: string
  hire_date: string | null
  phone: string | null
  contract_status: 'none' | 'active' | 'terminated'
}>>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const size = ref(20)
const sortBy = ref<{ key: string; order: 'asc' | 'desc' } | null>(null)
const sortByArr = computed(() => (sortBy.value ? [sortBy.value] : []))

/** property_code (조회 파라미터에만 사용, UI 노출은 SmartFilterBar에서 숨김) */
const propertyCode =
  localStorage.getItem('property_code') ||
  import.meta.env.VITE_DEFAULT_PROPERTY_CODE ||
  'MOP'

/** 필터 모델 (부서코드는 코드값, 한글표시는 옵션으로) */
const filters = ref<{ q: string; dept: string; status: 'none'|'active'|'terminated'|'' }>({
  q: '',
  dept: '',
  status: '',
})

/** 부/직 옵션과 Fallback 맵 */
const deptItems  = ref<{ title: string; value: string }[]>([])
const titleItems = ref<{ title: string; value: string }[]>([])
const deptMap = computed<Record<string,string>>(() => {
  const m: Record<string,string> = {}
  for (const it of deptItems.value) m[(it.value||'').toUpperCase()] = it.title || ''
  return m
})
const titleMap = computed<Record<string,string>>(() => {
  const m: Record<string,string> = {}
  for (const it of titleItems.value) m[(it.value||'').toUpperCase()] = it.title || ''
  return m
})

/** 상태 칩 사전 */
const statusItems = [
  { title: '전체',     value: ''          },
  { title: '미계약',   value: 'none'      },
  { title: '계약중',   value: 'active'    },
  { title: '계약만료', value: 'terminated'},
]

/** 테이블 헤더 — “요약 전용 컬럼”만 명시 (자동 컬럼 노출 차단) */
const headers = [
  { title: 'ID',        key: 'id',             sortable: true },
  { title: '사번',       key: 'emp_no',         sortable: true },
  { title: '이름',       key: 'name',           sortable: true },
  { title: '부서',       key: 'dept',           sortable: false },   // 슬롯에서 dept_name 렌더(아래 참고)
  { title: '직책',       key: 'title_name',     sortable: false },
  { title: '입사일',     key: 'hire_date',      sortable: true  },
  { title: '연락처',     key: 'phone',          sortable: false },
  { title: '계약 상태',  key: 'contract_status',sortable: false },
]
// NOTE: v-data-table는 headers에 정의된 key만 렌더합니다. slots에서 key 명과 동일하게 바인딩해야 하며,
//       dept_name은 표시용 슬롯에서 사용하므로 headers 키는 'dept'로 두고, 슬롯에서 r.dept_name을 출력합니다.

/** 부/직 옵션 로드 (실패 시 빈 배열로 안전하게) */
async function loadMasters() {
  try {
    const [deptOpt, titleOpt] = await Promise.all([
      MasterApi.departmentOptions(),   // [{ title, value }]
      MasterApi.titleOptions(),        // [{ title, value }]
    ])
    deptItems.value  = Array.isArray(deptOpt)  ? deptOpt  : []
    titleItems.value = Array.isArray(titleOpt) ? titleOpt : []
  } catch {
    deptItems.value = []
    titleItems.value = []
  }
}

/** 목록 재로딩 (서버 응답 → 요약형 Shape 로 변환 후 rows에 바인딩) */
async function reload() {
  loading.value = true
  try {
    const res = await EmployeesApi.list({
      page: page.value,
      size: size.value,
      q:     filters.value.q,
      dept:  filters.value.dept,                     // 서버는 코드기반 필터
      status:filters.value.status,                   // '', 'none', 'active', 'terminated'
      property_code: propertyCode,
      sort: sortBy.value ? `${sortBy.value.key}:${sortBy.value.order}` : '',
    })

    const raw = Array.isArray(res?.items) ? res.items : []
    // 서버가 내려준 데이터(대부분 snake_case) + Fallback 맵을 이용해 요약형으로 재구성
    const shaped = (raw as any[]).map((r) => {
      const deptCode  = (r.dept  || '').toString().toUpperCase()
      const titleCode = (r.title || '').toString().toUpperCase()
      const deptName  = (r.dept_name  ?? deptMap.value[deptCode]  ?? r.dept  ?? '')
      const titleName = (r.title_name ?? titleMap.value[titleCode]?? r.title ?? '')
      return {
        id:              Number(r.id) || 0,
        emp_no:          String(r.emp_no ?? ''),
        name:            String(r.name ?? ''),
        dept_name:       String(deptName),
        title_name:      String(titleName),
        hire_date:       r.hire_date ? String(r.hire_date) : null,
        phone:           r.phone ? String(r.phone) : null,
        contract_status: (['none','active','terminated'].includes(String(r.contract_status))) ? r.contract_status : 'none',
      }
    })

    // 목록 데이터/페이징 바인딩
    rows.value  = shaped
    total.value = Number(res?.total ?? shaped.length)
  } catch (e) {
    console.warn('[Employees.reload] failed:', e)
    toast.error('직원 목록을 불러올 수 없습니다.')
  } finally {
    loading.value = false
  }
}

/** SmartFilterBar → 조회 이벤트 */
function onSearch(payload: { property?: string; keyword?: string }) {
  filters.value.q = (payload?.keyword || '').trim()
  page.value = 1
  reload()
}

/** 필터 초기화 */
function resetFilters() {
  filters.value = { q: '', dept: '', status: '' }
  page.value = 1
  sortBy.value = null
  reload()
}

/** 정렬 변경 (알 수 없는 키는 id 기준으로 복귀) */
function onSortChange(sorts: any[]) {
    if (!Array.isArray(sorts) || !sorts.length) {
      sortBy.value = null
    } else {
      const k = String(sorts[0].key || 'id')
      const o = (String(sorts[0].order || 'desc') as 'asc'|'desc')
      const allowed = ['id','emp_no','name','dept_name','title_name','hire_date']
      sortBy.value = { key: (allowed.includes(k) ? k : 'id'), order: o }
    }
    page.value = 1
    reload()
}

/** 상태칩 텍스트/색상 */
function contractLabel(s?: string) {
  const v = (s || '').toLowerCase()
  if (v === 'active') return '계약중'
  if (v === 'terminated') return '계약만료'
  return '미계약'
}
function contractColor(s?: string) {
  const v = (s || '').toLowerCase()
  if (v === 'active') return 'primary'
  if (v === 'terminated') return 'black'
  return 'error'
}
function contractTextColor(s?: string) {
  const v = (s || '').toLowerCase()
  return (v === 'none') ? 'grey' : 'white'
}

/** 등록/업로드 다이얼로그 상태 */
const dialogUpload = ref(false)
const dialogCreate = ref(false)
function openUpload() { dialogUpload.value = true }
function openCreate() { dialogCreate.value = true }
function onCreated() { toast.success('직원이 등록되었습니다.'); reload() }
function onUploadDone() { reload() }

/** 마운트 시 옵션 & 목록 로드 */
onMounted(async () => {
  await loadMasters()
  await reload()
})
</script>

<style scoped src="@/styles/toolbar.scss"></style>
<style scoped>
/* 목록 전용 레이아웃 */
.page-shell { max-width: 1280px; margin: 0 auto; }
.brand-panel {
  background: rgb(var(--v-theme-surface));
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(16, 24, 40, 0.06);
  padding: 12px 16px;
  display: flex; align-items: center; flex-wrap: wrap; gap: 12px;
}
.btn-action { font-weight: 600; min-width: 90px; height: 40px; }

/* v-data-table 헤더 고정 */
:deep(.v-data-table__th) {
  white-space: nowrap;
  color: var(--color-muted);
  font-weight: 600;
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-line);
}
</style>
