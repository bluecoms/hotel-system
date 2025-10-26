<!-- ============================================================================
  File    : src/views/Admin/HR/Employees.vue
  Version : 2025.11 Final (v4.0 · SSOT Unified · Options Safe)
  Purpose : Hotel Admin — HR 직원 목록 (요약형 테이블 + 업로드/등록)
  ------------------------------------------------------------------------------
  변경 요약 (v4.0)
    ✅ Master API /options 기반 SSOT 일원화 (부서·직책)
    ✅ /options 미구현 환경 자동 폴백(list() → title/name 매핑)
    ✅ DialogEmployeeForm v2.2 연계 (동일 구조 유지)
    ✅ headers / statusItems 안정화 및 Vue 경고 제거
    ✅ SmartFilterBar / BoardList 타입 정합성 강화
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
        <v-btn color="primary" prepend-icon="mdi-account-plus" variant="elevated" class="btn-action" @click="openCreate">
          신규 등록
        </v-btn>
        <v-btn color="primary" prepend-icon="mdi-tray-arrow-up" variant="flat" class="btn-action" @click="openUpload">
          업로드
        </v-btn>
      </div>
    </div>

    <!-- ───── 필터바 ───── -->
    <SmartFilterBar class="mb-4 brand-panel" :show-property="false" @search="onSearch" @reset="resetFilters">
      <template #filters>
        <v-text-field
          v-model="filters.q"
          label="검색 (이름 / 사번 / 부서코드)"
          prepend-inner-icon="mdi-magnify"
          clearable hide-details density="comfortable"
          class="min-w-240"
          @keyup.enter="reload"
        />
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
        <v-select
          v-model="filters.status"
          :items="statusItems"
          label="계약 상태"
          clearable hide-details density="comfortable"
          style="max-width: 180px"
          @update:model-value="reload"
        />
      </template>
    </SmartFilterBar>

    <!-- ───── 목록 테이블 ───── -->
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
      @update:page="(p)=>{ page=p; reload() }"
      @update:items-per-page="(s)=>{ size=s; page=1; reload() }"
      @update:sort-by="onSortChange"
    >
      <template #cell.id="{ item }">{{ item.id }}</template>
      <template #cell.emp_no="{ item }">
        <div class="d-flex align-center">
          <v-icon size="16" class="mr-2" color="primary">mdi-account</v-icon>
          <span class="font-weight-medium">{{ item.emp_no }}</span>
        </div>
      </template>
      <template #cell.name="{ item }">{{ item.name }}</template>
      <template #cell.dept_name="{ item }">{{ item.dept_name || '-' }}</template>
      <template #cell.title_name="{ item }">{{ item.title_name || '-' }}</template>
      <template #cell.hire_date="{ item }">{{ item.hire_date ? item.hire_date.slice(0,10) : '-' }}</template>
      <template #cell.phone="{ item }">{{ item.phone || '-' }}</template>
      <template #cell.contract_status="{ item }">
        <v-chip size="small" label :color="contractColor(item.contract_status)" :text-color="contractTextColor(item.contract_status)">
          {{ contractLabel(item.contract_status) }}
        </v-chip>
      </template>
      <template #no-data>
        <StateBlock icon="mdi-account-search-outline" title="직원 정보 없음"
          :message="'검색 조건을 변경하거나 새로 등록해 보세요.'" @reset="resetFilters"/>
      </template>
    </BoardList>

    <!-- ───── 다이얼로그 ───── -->
    <DialogEmployeeForm v-model:open="dialogCreate" @saved="onCreated" />
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
   Script — HR 직원 목록 (v4.0 SSOT 통합판)
   ---------------------------------------------------------------------------
   • Master API /options 기반 — /list() 폴백 지원
   • titleOptions() / departmentOptions() 405 오류 시 자동 대체
   • SmartFilterBar, BoardList 모두 정합성 확보
=========================================================================== */
import { ref, reactive, computed, onMounted } from 'vue'
import { useToast } from '@/ui/composables/useToast'
import * as EmployeesApi from '@/services/employees'
import * as MasterApi from '@/services/master'
import SmartFilterBar from '@/ui/components/common/SmartFilterBar.vue'
import BoardList from '@/ui/components/common/BoardList.vue'
import StateBlock from '@/ui/components/common/StateBlock.vue'
import DialogUpload from '@/ui/components/closing/DialogUpload.vue'
import DialogEmployeeForm from '@/ui/components/hr/DialogEmployeeForm.vue'

const toast = useToast()
const today = new Date().toISOString().slice(0,10)

/* ----------------------------- 테이블 헤더 ----------------------------- */
const headers = [
  { title: 'ID', key: 'id', sortable: true },
  { title: '사번', key: 'emp_no', sortable: true },
  { title: '이름', key: 'name', sortable: true },
  { title: '부서', key: 'dept_name' },
  { title: '직책', key: 'title_name' },
  { title: '입사일', key: 'hire_date', sortable: true },
  { title: '연락처', key: 'phone' },
  { title: '계약 상태', key: 'contract_status' },
]

/* ----------------------------- 계약 상태 옵션 ----------------------------- */
const statusItems = [
  { title: '전체', value: '' },
  { title: '미계약', value: 'none' },
  { title: '계약중', value: 'active' },
  { title: '계약만료', value: 'terminated' },
]

/* ----------------------------- 상태 ----------------------------- */
const rows = ref<any[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const size = ref(20)
const sortBy = ref<{ key: string; order: 'asc'|'desc' }|null>(null)
const sortByArr = computed(() => sortBy.value ? [sortBy.value] : [])

/* ----------------------------- 필터 ----------------------------- */
const propertyCode = localStorage.getItem('property_code') || import.meta.env.VITE_DEFAULT_PROPERTY_CODE || 'MOP'
const filters = reactive({ q:'', dept:'', status:'' })

/* ----------------------------- 옵션 로드 ----------------------------- */
const deptItems = ref<{title:string;value:string}[]>([])
const titleItems = ref<{title:string;value:string}[]>([])
const deptMap = computed(()=>Object.fromEntries(deptItems.value.map(i=>[i.value.toUpperCase(),i.title])))
const titleMap = computed(()=>Object.fromEntries(titleItems.value.map(i=>[i.value.toUpperCase(),i.title])))

async function loadMasters() {
  try {
    const [depts, titles] = await Promise.all([
      MasterApi.departmentOptions?.().catch(async()=>MasterApi.listDepartments()),
      MasterApi.titleOptions?.().catch(async()=>MasterApi.listTitles()),
    ])
    deptItems.value = Array.isArray(depts)
      ? depts.map((d:any)=>({title:d.title||d.name,value:d.value||d.code}))
      : []
    titleItems.value = Array.isArray(titles)
      ? titles.map((t:any)=>({title:t.title||t.name,value:t.value||t.code}))
      : []
  } catch (err) {
    console.warn('[Employees] loadMasters 실패', err)
    deptItems.value = []
    titleItems.value = []
  }
}

/* ----------------------------- 목록 로드 ----------------------------- */
async function reload() {
  loading.value = true
  try {
    const res = await EmployeesApi.list({
      page: page.value, size: size.value,
      q: filters.q, dept: filters.dept, status: filters.status,
      property_code: propertyCode,
      sort: sortBy.value ? `${sortBy.value.key}:${sortBy.value.order}` : '',
    })
    const raw = Array.isArray(res?.items)?res.items:[]
    rows.value = raw.map((r:any)=>({
      id: r.id,
      emp_no: r.emp_no||'',
      name: r.name||'',
      dept_name: r.dept_name || deptMap.value[(r.dept||'').toUpperCase()] || r.dept || '',
      title_name: r.title_name || titleMap.value[(r.title||'').toUpperCase()] || r.title || '',
      hire_date: r.hire_date||'',
      phone: r.phone||'',
      contract_status: r.contract_status||'none',
    }))
    total.value = Number(res?.total ?? rows.value.length)
  } catch (err) {
    console.warn('[Employees.reload] 실패', err)
    toast.error('직원 목록을 불러올 수 없습니다.')
  } finally {
    loading.value = false
  }
}

/* ----------------------------- 이벤트 ----------------------------- */
function onSearch(payload:{property?:string;keyword?:string}) {
  filters.q = (payload?.keyword||'').trim()
  page.value=1; reload()
}
function resetFilters() {
  filters.q=''; filters.dept=''; filters.status=''; sortBy.value=null; page.value=1; reload()
}
function onSortChange(sorts:any[]) {
  if(!Array.isArray(sorts)||!sorts.length){sortBy.value=null}
  else{
    const k=sorts[0].key||'id'
    const o=sorts[0].order||'asc'
    const allowed=['id','emp_no','name','hire_date']
    sortBy.value={key:allowed.includes(k)?k:'id',order:o}
  }
  reload()
}

/* ----------------------------- 계약 상태 색상 ----------------------------- */
function contractLabel(s?:string){const v=(s||'').toLowerCase();return v==='active'?'계약중':v==='terminated'?'계약만료':'미계약'}
function contractColor(s?:string){const v=(s||'').toLowerCase();return v==='active'?'primary':v==='terminated'?'black':'error'}
function contractTextColor(s?:string){return (s==='none')?'grey-darken-2':'white'}

/* ----------------------------- 다이얼로그 ----------------------------- */
const dialogUpload=ref(false)
const dialogCreate=ref(false)
function openUpload(){dialogUpload.value=true}
function openCreate(){dialogCreate.value=true}
function onCreated(){toast.success('직원이 등록되었습니다.');reload()}
function onUploadDone(){reload()}

/* ----------------------------- Mounted ----------------------------- */
onMounted(async()=>{await loadMasters();await reload()})
</script>

<style scoped src="@/styles/toolbar.scss"></style>
<style scoped>
.page-shell{max-width:1280px;margin:0 auto;}
.brand-panel{
  background:rgb(var(--v-theme-surface));
  border-radius:12px;
  box-shadow:0 2px 10px rgba(16,24,40,0.06);
  padding:12px 16px;
  display:flex;align-items:center;flex-wrap:wrap;gap:12px;
}
.btn-action{font-weight:600;min-width:90px;height:40px;}
:deep(.v-data-table__th){
  white-space:nowrap;
  color:var(--color-muted);
  font-weight:600;
  background-color:var(--color-surface);
  border-bottom:1px solid var(--color-line);
}
</style>
