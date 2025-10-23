<!-- ============================================================================
  File      : src/views/Admin/HR/Contracts.vue
  Version   : 2025.10.30 Final Stable (v4.4 · HR 간소화 3차 · 종료관리 완전이관 / UX 개선)
  Purpose   : Hotel Admin — HR 직원 계약 관리 (미계약자 포함 + 스캔본 업로드 확정)
  ------------------------------------------------------------------------------
  목적:
    • HR 직원별 계약 목록/이력/스캔본 업로드 관리 화면
    • 직원 등록과 계약이 분리되어도 미계약자 표시 유지
    • 스캔본 업로드 시 즉시 계약 확정(Auto Activate)
    • 계약 종료 기능을 Employees.vue에서 완전 이관하여 통합 관리
  ------------------------------------------------------------------------------
  개선 요약 (v4.4)
    ✅ 계약 종료 기능 완전 이관: Employees.vue → Contracts.vue
       - 진행중(active) 상태에서만 종료 버튼 활성
       - 종료 후 toast + 목록 리로드
    ✅ SmartFilterBar showProperty=false 대응 (Property 숨김)
    ✅ 상태 칩 색상/텍스트 통일(brand token 기반)
    ✅ 스캔본 업로드 시 auto activate 유지
    ✅ 코드 정돈 및 상세 주석 추가
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
    <SmartFilterBar
      class="mb-4 brand-panel"
      :show-property="false"
      @search="onSearch"
      @reset="resetFilters"
    >
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
      @update:page="(p)=>{page=p;reload()}"
      @update:items-per-page="(s)=>{size=s;page=1;reload()}"
      @update:sort-by="onSortChange"
    >
      <!-- 직원 정보 -->
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

      <!-- 계약 시작/종료일 -->
      <template #cell.start_date="{ item }">{{ fmtDate(item.start_date||item.contract_start) }}</template>
      <template #cell.end_date="{ item }">{{ fmtDate(item.end_date||item.contract_end) }}</template>

      <!-- 급여 -->
      <template #cell.salary="{ item }">
        <div class="text-end font-weight-medium">₩{{ fmtNum(item.salary||0) }}</div>
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

      <!-- 관리 액션 -->
      <template #cell.actions="{ item }">
        <!-- 계약서 작성 -->
        <v-tooltip text="계약서 작성">
          <template #activator="{ props }">
            <v-btn v-bind="props" icon="mdi-file-document-edit-outline" size="small" variant="text" color="primary" @click="openStudio(item)" />
          </template>
        </v-tooltip>

        <!-- 계약 이력 -->
        <v-tooltip text="계약 이력 보기">
          <template #activator="{ props }">
            <v-btn v-bind="props" icon="mdi-history" size="small" variant="text" color="info" @click="viewHistory(item)" />
          </template>
        </v-tooltip>

        <!-- 스캔본 업로드 -->
        <v-tooltip text="스캔본 업로드 (날인본)">
          <template #activator="{ props }">
            <v-btn v-bind="props" icon="mdi-file-upload-outline" size="small" variant="text" color="success" @click="triggerUpload(item)" />
          </template>
        </v-tooltip>

        <!-- 계약 종료 -->
        <v-tooltip text="계약 종료">
          <template #activator="{ props }">
            <v-btn
              v-bind="props"
              icon="mdi-file-cog-outline"
              size="small"
              variant="text"
              color="error"
              :disabled="!isTerminatable(item)"
              @click="terminate(item)"
            />
          </template>
        </v-tooltip>
      </template>

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

    <!-- 스캔본 업로드 다이얼로그 -->
    <v-dialog v-model="uploadDlg.open" max-width="420">
      <v-card>
        <v-card-title>스캔본 업로드</v-card-title>
        <v-card-text>
          <div class="text-body-2 mb-2">
            스캔본(PDF/JPG/PNG)을 업로드하면 <b>즉시 계약 확정</b>됩니다.
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
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="uploadDlg.open=false">취소</v-btn>
          <v-btn color="primary" :loading="uploadDlg.loading" @click="pickFile">파일 선택</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 숨김 파일 입력 -->
    <input ref="fileInputRef" type="file" accept=".pdf,.jpg,.jpeg,.png" class="d-none" @change="onFilePicked" />
  </v-container>
</template>

<script setup lang="ts">
/* ===========================================================================
   Script — Contracts.vue (v4.4)
   ---------------------------------------------------------------------------
   • 미계약자 포함 계약 목록/이력/스캔본 업로드
   • 계약 종료/확정/작성/이력 등 액션 통합
   • 상태별 색상·문구 통일
=========================================================================== */
import { ref, reactive, computed, onMounted } from 'vue'
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

/* 상태 변수 */
const rows = ref<any[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const size = ref(20)
const sortBy = ref<{ key: string; order: 'asc' | 'desc' } | null>(null)
const sortByArr = computed(() => (sortBy.value ? [sortBy.value] : []))
const propertyCode = localStorage.getItem('property_code') || import.meta.env.VITE_DEFAULT_PROPERTY_CODE || 'MOP'

/* 필터 */
const filters = reactive({ q: '', status: '' })
const statusItems = [
  { title: '전체', value: '' },
  { title: '계약중', value: 'active' },
  { title: '만료', value: 'terminated' },
  { title: '미계약', value: 'none' },
]

/* 헤더 정의 */
const headers = [
  { title: '직원', key: 'emp', sortable: false },
  { title: '계약유형', key: 'contract_type', sortable: false },
  { title: '시작일', key: 'start_date', sortable: true },
  { title: '종료일', key: 'end_date', sortable: true },
  { title: '급여', key: 'salary', align: 'end', sortable: true },
  { title: '상태', key: 'status', align: 'center', sortable: false },
  { title: '관리', key: 'actions', align: 'center', sortable: false },
]

/* 데이터 포맷터 */
const rowsView = computed(() => (rows.value||[]).map(r=>({
  ...r,
  start_date: r.start_date||r.contract_start||null,
  end_date: r.end_date||r.contract_end||null,
})))
function fmtNum(n:number){return n?.toLocaleString?.()||String(n)}
function fmtDate(s?:string|null){return s?String(s).slice(0,10):'-'}

/* 목록 로드 */
async function reload(){
  loading.value=true
  try{
    const sort=sortBy.value?`${sortBy.value.key}:${sortBy.value.order}`:''
    const [contractsRes, employeesRes]=await Promise.all([
      ContractsApi.list({property_code:propertyCode,q:filters.q||undefined,status:filters.status||undefined,page:page.value,size:size.value,sort}),
      EmployeesApi.list({property_code:propertyCode})
    ])
    const contracts=contractsRes?.items||[]
    const employees=employeesRes?.items||[]
    rows.value=employees.map((emp:any)=>{
      const c=contracts.find((x:any)=>x.employee_id===emp.id)
      return c?{...c,emp_name:emp.name,emp_no:emp.emp_no,status:c.status||'active'}:{
        id:`emp-${emp.id}`,employee_id:emp.id,emp_name:emp.name,emp_no:emp.emp_no,
        contract_type:'-',salary:0,status:'none'
      }
    })
    total.value=rows.value.length
  }catch(e){toast.error('계약 목록을 불러올 수 없습니다.')}finally{loading.value=false}
}

/* 검색/초기화 이벤트 */
function onSearch(payload:{property?:string;keyword?:string}){filters.q=(payload.keyword||'').trim();reload()}
function resetFilters(){filters.q='';filters.status='';page.value=1;sortBy.value=null;reload()}
function onSortChange(s:any[]){sortBy.value=(!Array.isArray(s)||!s.length)?null:{key:s[0].key,order:s[0].order};reload()}

/* 상태 칩 표기 */
function statusLabel(s?:string){const v=(s||'').toLowerCase();if(v==='active')return'계약중';if(v==='terminated')return'만료';if(v==='none')return'미계약';return'-'}
function statusColor(s?:string){const v=(s||'').toLowerCase();if(v==='active')return'primary';if(v==='terminated')return'black';if(v==='none')return'error';return'grey-lighten-1'}
function statusTextColor(s?:string){return (s==='none')?'grey-darken-2':'white'}
function contractTypeLabel(raw?:string){return raw&&raw!=='-'?'정규직(월급제)':'-'}

/* 계약 종료 가능 여부 */
function isTerminatable(item:any){return item?.status==='active'&&item?.id&&!String(item.id).startsWith('emp-')}

/* 액션 정의 */
const dialogForm=ref(false);const dialogStudio=ref(false);const dialogHistory=ref(false)
const selectedContract=ref<any>(null);const selectedId=ref<number|null>(null)
function openNewContract(){dialogForm.value=true}
function openStudio(item:any){selectedContract.value={...item,id:item?.id??item?.contract_id};dialogStudio.value=true}
function viewHistory(item:any){selectedId.value=typeof item?.id==='number'?item.id:null;dialogHistory.value=true}

/* 계약 종료 */
async function terminate(item:any){
  if(!isTerminatable(item))return toast.info('진행중인 계약만 종료할 수 있습니다.')
  try{
    await ContractsApi.terminate(item.id)
    toast.success('계약이 종료되었습니다.')
    reload()
  }catch{toast.error('계약 종료 실패')}
}

/* 스캔본 업로드 */
const fileInputRef=ref<HTMLInputElement|null>(null)
const uploadDlg=reactive({open:false,targetId:null as number|null,start_date:new Date().toISOString().slice(0,10),end_date:'',loading:false})
function triggerUpload(item:any){
  const cid=typeof item?.id==='number'?item.id:(item?.contract_id??null)
  if(!cid)return toast.error('업로드할 계약이 없습니다.')
  uploadDlg.targetId=cid;uploadDlg.start_date=(item.start_date||new Date().toISOString().slice(0,10)).slice(0,10)
  uploadDlg.end_date=(item.end_date||'')?.slice?.(0,10)||'';uploadDlg.open=true
}
function pickFile(){fileInputRef.value?.click()}
async function onFilePicked(e:Event){
  const el=e.target as HTMLInputElement;const file=el.files?.[0];el.value=''
  if(!file||!uploadDlg.targetId)return
  try{
    uploadDlg.loading=true
    await ContractsApi.uploadScan(uploadDlg.targetId,file,{start_date:uploadDlg.start_date,end_date:uploadDlg.end_date})
    await ContractsApi.activate(uploadDlg.targetId)  // 자동 활성화
    toast.success('스캔본 업로드 및 계약 확정 완료')
    uploadDlg.open=false;reload()
  }catch(err:any){toast.error('업로드 실패: '+(err?.message||'서버 오류'))}finally{uploadDlg.loading=false}
}
function onContractSaved(){reload()}

/* 초기 로드 */
onMounted(reload)
</script>

<style scoped src="@/styles/toolbar.scss"></style>
<style scoped>
.page-shell{max-width:1280px;margin:0 auto;}
.brand-panel{background:rgb(var(--v-theme-surface));border-radius:12px;box-shadow:0 2px 10px rgba(16,24,40,0.06);padding:12px 16px;display:flex;align-items:center;flex-wrap:wrap;gap:12px;}
.btn-action{font-weight:600;min-width:90px;height:40px;}
.d-none{display:none;}
</style>
