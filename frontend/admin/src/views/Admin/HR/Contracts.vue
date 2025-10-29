<!-- ============================================================================
# File      : src/views/Admin/HR/Contracts.vue
# Version   : 2025.11-10 · v4.6 (SSOT Final · Full Commented Edition)
# Purpose   : Hotel Admin — HR 직원 계약 관리 (미계약자 포함 + 확정/종료/스캔본)
# ----------------------------------------------------------------------------
# 주요 특징
#   • 직원(Employee) 기준 계약 목록/이력/종료/스캔본 업로드 관리
#   • 미계약자도 목록에 표시 (백엔드 LEFT JOIN)
#   • 스캔본(PDF/JPG) 업로드 시 즉시 계약 확정 (auto activate)
#   • 계약 종료 기능 Employees.vue에서 완전 이관
# ----------------------------------------------------------------------------
# 설계 의도
#   ✅ SSOT 규격 — /api/contracts 단일 엔드포인트 통합
#   ✅ 상태별 색상·문구 일관화 (brand theme 기반)
#   ✅ Vue3 + Pinia + Vuetify3 표준 구조 유지
#   ✅ HR 담당자 중심 UX: 간결한 종료/이력/확정 플로우
# ============================================================================ -->
<template>
  <v-container fluid class="page-shell py-6">
    <!-- ───────────── Toolbar ───────────── -->
    <div class="bar mb-6">
      <div class="bar-left">
        <v-icon color="primary" icon="mdi-file-document-outline" size="22" />
        <h2 class="text-h6 font-weight-bold">직원 계약 관리</h2>
        <span class="text-muted text-body-2">계약 등록 · 확정 · 이력 · 종료</span>
      </div>
      <div class="bar-right">
        <!-- 신규 계약 버튼 -->
        <v-btn color="primary" prepend-icon="mdi-file-document-plus" variant="flat"
               class="btn-action" @click="openNewContract">
          신규 계약
        </v-btn>
      </div>
    </div>

    <!-- ───────────── 필터 바 (SmartFilterBar) ───────────── -->
    <SmartFilterBar class="mb-4 brand-panel" :show-property="false"
                    @search="onSearch" @reset="resetFilters">
      <template #filters>
        <!-- 검색어 입력 -->
        <v-text-field v-model="filters.q" label="검색 (직원명 / 사번 / 상태)"
                      prepend-inner-icon="mdi-magnify" clearable hide-details
                      density="comfortable" class="min-w-240"
                      @keyup.enter="reload" />
        <!-- 계약 상태 선택 -->
        <v-select v-model="filters.status" :items="statusItems"
                  label="계약 상태" clearable hide-details
                  density="comfortable" style="max-width:160px"
                  @update:model-value="reload" />
      </template>
    </SmartFilterBar>

    <!-- ───────────── 계약 목록 테이블 ───────────── -->
    <BoardList title="계약 목록"
               :headers="headers" :items="rows"
               :total="total" :loading="loading"
               :page="page" :size="size" :sort-by="sortByArr"
               @update:page="(p)=>{page=p;reload()}"
               @update:items-per-page="(s)=>{size=s;page=1;reload()}"
               @update:sort-by="onSortChange">
      <!-- 직원 정보 칼럼 -->
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
      <template #cell.contract_start="{ item }">{{ fmtDate(item.contract_start) }}</template>
      <template #cell.contract_end="{ item }">{{ fmtDate(item.contract_end) }}</template>

      <!-- 급여 -->
      <template #cell.salary="{ item }">
        <div class="text-end font-weight-medium">₩{{ fmtNum(item.salary||0) }}</div>
      </template>

      <!-- 계약 상태 -->
      <template #cell.status="{ item }">
        <v-chip size="small" :color="statusColor(item.status)"
                :text-color="statusTextColor(item.status)" label>
          {{ statusLabel(item.status) }}
        </v-chip>
      </template>

      <!-- 관리 액션 버튼 -->
      <template #cell.actions="{ item }">
        <!-- 계약서 작성 -->
        <v-tooltip text="계약서 작성">
          <template #activator="{ props }">
            <v-btn v-bind="props" icon="mdi-file-document-edit-outline"
                   size="small" variant="text" color="primary"
                   @click="openStudio(item)" />
          </template>
        </v-tooltip>

        <!-- 계약 이력 보기 -->
        <v-tooltip text="계약 이력 보기">
          <template #activator="{ props }">
            <v-btn v-bind="props" icon="mdi-history" size="small" variant="text"
                   color="info" @click="viewHistory(item)" />
          </template>
        </v-tooltip>

        <!-- 스캔본 업로드 -->
        <v-tooltip text="스캔본 업로드 (확정)">
          <template #activator="{ props }">
            <v-btn v-bind="props" icon="mdi-file-upload-outline" size="small"
                   variant="text" color="success" @click="triggerUpload(item)" />
          </template>
        </v-tooltip>

        <!-- 계약 종료 -->
        <v-tooltip text="계약 종료">
          <template #activator="{ props }">
            <v-btn v-bind="props" icon="mdi-file-cog-outline" size="small"
                   variant="text" color="error"
                   :disabled="!isTerminatable(item)" @click="terminate(item)" />
          </template>
        </v-tooltip>
      </template>

      <!-- 데이터 없음 표시 -->
      <template #no-data>
        <StateBlock icon="mdi-file-document-outline"
                    title="계약 정보 없음"
                    subtitle="검색 조건을 변경하거나 신규 계약을 등록해 보세요."
                    @reset="resetFilters" />
      </template>
    </BoardList>

    <!-- ───────────── 하위 다이얼로그들 ───────────── -->
    <DialogContractForm v-model:open="dialogForm" @saved="reload" />
    <DialogContractStudio v-model:open="dialogStudio" :contract="selectedContract" @saved="reload" />
    <DialogContractHistory v-model:open="dialogHistory" :contract-id="selectedId ?? ''" />

    <!-- ───────────── 스캔본 업로드 다이얼로그 ───────────── -->
    <v-dialog v-model="uploadDlg.open" max-width="420">
      <v-card>
        <v-card-title>스캔본 업로드</v-card-title>
        <v-card-text>
          <div class="text-body-2 mb-2">
            스캔본(PDF/JPG/PNG)을 업로드하면 <b>즉시 계약 확정</b>됩니다.
          </div>
          <v-text-field v-model="uploadDlg.start_date" type="date" label="계약 시작일"
                        density="comfortable" hide-details class="mb-2" />
          <v-text-field v-model="uploadDlg.end_date" type="date" label="계약 종료일(선택)"
                        density="comfortable" hide-details />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="uploadDlg.open=false">취소</v-btn>
          <v-btn color="primary" :loading="uploadDlg.loading" @click="pickFile">파일 선택</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 실제 파일 선택 input -->
    <input ref="fileInputRef" type="file" accept=".pdf,.jpg,.jpeg,.png"
           class="d-none" @change="onFilePicked" />
  </v-container>
</template>

<script setup lang="ts">
/* ============================================================================
# Script Summary
#   • 계약 목록 로드 및 필터링
#   • 신규/이력/종료/스캔본 업로드 관리
#   • 상태 표시 및 토스트 알림 일원화
# ============================================================================ */
import { ref, reactive, computed, onMounted } from 'vue'
import { useToast } from '@/ui/composables/useToast'
import * as ContractsApi from '@/services/contracts'
import SmartFilterBar from '@/ui/components/common/SmartFilterBar.vue'
import BoardList from '@/ui/components/common/BoardList.vue'
import StateBlock from '@/ui/components/common/StateBlock.vue'
import DialogContractForm from '@/ui/components/hr/DialogContractForm.vue'
import DialogContractStudio from '@/ui/components/hr/DialogContractStudio.vue'
import DialogContractHistory from '@/ui/components/hr/DialogContractHistory.vue'

/* ───────────── 상태 변수 ───────────── */
const toast = useToast()
const rows = ref<any[]>([])             // 계약 목록 데이터
const total = ref(0)                    // 총 개수
const loading = ref(false)              // 로딩 상태
const page = ref(1)                     // 현재 페이지
const size = ref(20)                    // 페이지당 행 수
const sortBy = ref<{ key: string; order: 'asc' | 'desc' } | null>(null)
const sortByArr = computed(() => (sortBy.value ? [sortBy.value] : []))
const propertyCode = localStorage.getItem('property_code') ||
  import.meta.env.VITE_DEFAULT_PROPERTY_CODE || 'MOP'

/* ───────────── 필터 설정 ───────────── */
const filters = reactive({ q: '', status: '' })
const statusItems = [
  { title: '전체', value: '' },
  { title: '계약중', value: 'active' },
  { title: '만료', value: 'terminated' },
  { title: '미계약', value: 'none' },
]
const headers = [
  { title: '직원', key: 'emp', sortable: false },
  { title: '계약유형', key: 'contract_type' },
  { title: '시작일', key: 'contract_start' },
  { title: '종료일', key: 'contract_end' },
  { title: '급여', key: 'salary', align: 'end' },
  { title: '상태', key: 'status', align: 'center' },
  { title: '관리', key: 'actions', align: 'center' },
]

/* ───────────── 헬퍼: 포맷터 & 상태라벨 ───────────── */
function fmtNum(n:number){return n?.toLocaleString?.()||String(n)}
function fmtDate(s?:string|null){return s?String(s).slice(0,10):'-'}
function statusLabel(s?:string){const v=(s||'').toLowerCase();if(v==='active')return'계약중';if(v==='terminated')return'만료';if(v==='none')return'미계약';return'-'}
function statusColor(s?:string){const v=(s||'').toLowerCase();if(v==='active')return'primary';if(v==='terminated')return'black';if(v==='none')return'error';return'grey-lighten-1'}
function statusTextColor(s?:string){return (s==='none')?'grey-darken-2':'white'}
function contractTypeLabel(raw?:string){return raw&&raw!=='-'?'정규직(월급제)':'-'}

/* ───────────── 데이터 로드 ───────────── */
async function reload(){
  loading.value=true
  try{
    const res=await ContractsApi.list({
      property_code:propertyCode,
      q:filters.q||undefined,
      status:filters.status||undefined,
      page:page.value,size:size.value,
    })
    rows.value=res.items||[];total.value=res.total||rows.value.length
  }catch{
    toast.error('계약 목록을 불러올 수 없습니다.')
  }finally{
    loading.value=false
  }
}

/* ───────────── 필터/정렬/검색 이벤트 ───────────── */
function onSearch(payload:{property?:string;keyword?:string}){filters.q=(payload.keyword||'').trim();reload()}
function resetFilters(){filters.q='';filters.status='';page.value=1;reload()}
function onSortChange(s:any[]){sortBy.value=(s?.length)?{key:s[0].key,order:s[0].order}:null;reload()}

/* ───────────── 계약 종료 ───────────── */
function isTerminatable(item:any){return item?.status==='active'&&item?.id&&!String(item.id).startsWith('emp-')}
async function terminate(item:any){
  if(!isTerminatable(item))return toast.info('진행중인 계약만 종료할 수 있습니다.')
  try{
    await ContractsApi.terminate(item.id)
    toast.success('계약이 종료되었습니다.')
    reload()
  }catch{
    toast.error('계약 종료 실패')
  }
}

/* ───────────── 다이얼로그 컨트롤 ───────────── */
const dialogForm=ref(false)
const dialogStudio=ref(false)
const dialogHistory=ref(false)
const selectedContract=ref<any>(null)
const selectedId=ref<number|null>(null)
function openNewContract(){dialogForm.value=true}
function openStudio(item:any){selectedContract.value={...item,id:item?.id??item?.contract_id};dialogStudio.value=true}
function viewHistory(item:any){selectedId.value=typeof item?.id==='number'?item.id:null;dialogHistory.value=true}

/* ───────────── 스캔본 업로드 ───────────── */
const fileInputRef=ref<HTMLInputElement|null>(null)
const uploadDlg=reactive({open:false,targetId:null as number|null,start_date:new Date().toISOString().slice(0,10),end_date:'',loading:false})
function triggerUpload(item:any){
  const cid=typeof item?.id==='number'?item.id:(item?.contract_id??null)
  if(!cid)return toast.error('업로드할 계약이 없습니다.')
  uploadDlg.targetId=cid
  uploadDlg.start_date=(item.contract_start||new Date().toISOString().slice(0,10)).slice(0,10)
  uploadDlg.end_date=(item.contract_end||'')?.slice?.(0,10)||''
  uploadDlg.open=true
}
function pickFile(){fileInputRef.value?.click()}
async function onFilePicked(e:Event){
  const el=e.target as HTMLInputElement;const file=el.files?.[0];el.value=''
  if(!file||!uploadDlg.targetId)return
  try{
    uploadDlg.loading=true
    await ContractsApi.uploadScan(uploadDlg.targetId,file,{start_date:uploadDlg.start_date,end_date:uploadDlg.end_date})
    await ContractsApi.activate(uploadDlg.targetId)  // 업로드 후 자동 확정
    toast.success('스캔본 업로드 및 계약 확정 완료')
    uploadDlg.open=false;reload()
  }catch(err:any){
    toast.error('업로드 실패: '+(err?.message||'서버 오류'))
  }finally{
    uploadDlg.loading=false
  }
}

/* ───────────── 초기 실행 ───────────── */
onMounted(reload)
</script>

<!-- ───────────── 스타일 ───────────── -->
<style scoped src="@/styles/toolbar.scss"></style>
<style scoped>
.page-shell{max-width:1280px;margin:0 auto;}
.brand-panel{background:rgb(var(--v-theme-surface));border-radius:12px;
  box-shadow:0 2px 10px rgba(16,24,40,0.06);padding:12px 16px;
  display:flex;align-items:center;flex-wrap:wrap;gap:12px;}
.btn-action{font-weight:600;min-width:90px;height:40px;}
.d-none{display:none;}
</style>
