<!-- ============================================================================
# File      : src/ui/components/hr/DialogContractForm.vue
# Version   : 2025-11-10 · v2.1 (SSOT Final · Full Commented Edition)
# Purpose   : Hotel Admin — 신규 계약 등록 다이얼로그 (HR 모듈 / append-only)
# ----------------------------------------------------------------------------
# 목적:
#   • 직원별 신규 계약 등록(append-only 방식)
#   • ContractsApi.create() 호출로 DB 신규 버전 추가
#   • 등록 후 부모 컴포넌트에 emit('saved') → reload() 동기화
# ----------------------------------------------------------------------------
# 설계 원칙:
#   ✅ HR 전용 컴포넌트 (Employees.vue → Contracts.vue 완전 분리)
#   ✅ 필수 최소 필드 유지 (직원, 기간, 급여, 유형)
#   ✅ Validation / UX 일관화 (SSOT 규약 준수)
#   ✅ append-only: 기존 계약은 수정하지 않고 신규 버전으로만 추가
# ============================================================================ -->
<template>
  <v-dialog
    :model-value="open"
    max-width="720"
    persistent
    @update:model-value="v => emit('update:open', v)"
  >
    <v-card class="rounded-2xl">

      <!-- ▣ 헤더 영역 -->
      <v-card-title class="d-flex align-center justify-space-between py-3 px-5">
        <div class="d-flex align-center gap-2">
          <v-icon icon="mdi-file-document-edit-outline" size="20" class="text-primary" />
          <span class="text-h6 font-weight-medium">신규 계약 등록</span>
        </div>
        <v-btn icon="mdi-close" variant="text" @click="emit('update:open', false)" />
      </v-card-title>

      <v-divider />

      <!-- ▣ 본문 영역 -->
      <v-card-text class="px-5 py-4">
        <v-form ref="formRef" v-model="valid">
          <v-row dense>

            <!-- 직원 선택 -->
            <v-col cols="12" md="8">
              <EmployeePicker
                v-model="employeeId"
                label="직원 선택"
                :rules="[req]"
                @selected="onEmployeeSelected"
              />
            </v-col>

            <!-- 사번 표시 -->
            <v-col cols="12" md="4">
              <v-text-field
                :model-value="empContext.emp_no || ''"
                label="사번"
                variant="outlined"
                density="comfortable"
                readonly
              />
            </v-col>

            <!-- 부서 / 직책 -->
            <v-col cols="12" md="6">
              <v-text-field
                :model-value="empContext.dept_name || '-'"
                label="부서"
                variant="outlined"
                density="comfortable"
                readonly
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                :model-value="empContext.title_name || '-'"
                label="직책"
                variant="outlined"
                density="comfortable"
                readonly
              />
            </v-col>

            <!-- 계약유형 -->
            <v-col cols="12" md="6">
              <v-select
                v-model="form.contract_type"
                :items="contractTypes"
                label="계약유형"
                item-title="title"
                item-value="value"
                variant="outlined"
                density="comfortable"
                :rules="[req]"
              />
            </v-col>

            <!-- 급여 입력 -->
            <v-col cols="12" md="6">
              <v-text-field
                v-model.number="form.salary"
                type="number"
                label="월 급여(₩)"
                variant="outlined"
                density="comfortable"
                :rules="[req]"
                placeholder="예: 3000000"
              />
            </v-col>

            <!-- 계약 기간 -->
            <v-col cols="12" md="6">
              <v-text-field
                v-model="form.start_date"
                type="date"
                label="시작일"
                variant="outlined"
                density="comfortable"
                :rules="[req]"
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="form.end_date"
                type="date"
                label="종료일(선택)"
                variant="outlined"
                density="comfortable"
                :rules="[dateRangeRule]"
              />
            </v-col>

            <!-- 메모 -->
            <v-col cols="12">
              <v-textarea
                v-model.trim="form.memo"
                label="메모 (선택)"
                variant="outlined"
                rows="2"
                auto-grow
              />
            </v-col>

          </v-row>
        </v-form>
      </v-card-text>

      <v-divider />

      <!-- ▣ 푸터 영역 -->
      <v-card-actions class="px-5 py-3 justify-end">
        <v-btn variant="text" color="grey" @click="emit('update:open', false)">취소</v-btn>
        <v-btn color="primary" variant="flat"
               prepend-icon="mdi-content-save"
               :loading="saving" @click="onSubmit">
          저장
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
/* ============================================================================
# Script — 신규 계약 등록 다이얼로그
# ----------------------------------------------------------------------------
# 기능 요약:
#   • 직원 선택 후 계약 정보 입력
#   • ContractsApi.create() → 신규 버전 생성
#   • 성공 시 toast + 부모 reload() 트리거
# ============================================================================ */
import { ref, reactive, watch, nextTick } from 'vue'
import { useToast } from '@/ui/composables/useToast'
import * as EmployeesApi from '@/services/employees'
import * as ContractsApi from '@/services/contracts'
import EmployeePicker from '@/ui/components/hr/EmployeePicker.vue'

/* Props / Emits 정의 */
const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ (e:'update:open',v:boolean):void; (e:'saved'):void }>()

/* Toast / 상태 변수 */
const { success, error } = useToast()
const formRef = ref()
const valid = ref(false)
const saving = ref(false)

/* ───────────── 직원 선택 관련 ───────────── */
const employeeId = ref<number|null>(null)
const empContext = ref<any>({ emp_no:'', name:'', dept_name:'', title_name:'' })

/** 직원 선택 시 상세 정보 로드 */
async function onEmployeeSelected(row:any|null){
  if(!row){empContext.value={};form.employee_id=null;return}
  form.employee_id=row.id
  try{
    const emp=await EmployeesApi.getEmployee(row.id)
    empContext.value={
      emp_no: emp.emp_no||'',
      name: emp.name||'',
      dept_name: emp.dept_name||emp.dept||'-',
      title_name: emp.title_name||emp.title||'-'
    }
  }catch(e){console.error('[EmpLoad]',e)}
}

/* ───────────── 폼 데이터 구조 ───────────── */
const propertyCode = localStorage.getItem('property_code') ||
  import.meta.env.VITE_DEFAULT_PROPERTY_CODE || 'MOP'

const form = reactive({
  employee_id:null as number|null,
  contract_type:'MONTHLY',
  salary:null as number|null,
  start_date:'',
  end_date:'',
  memo:'',
  property_code:propertyCode,
})

/* 계약유형 선택지 */
const contractTypes=[
  { title:'정규직 (월급제)', value:'MONTHLY' },
  { title:'시간제 (시급)', value:'HOURLY' },
  { title:'기타', value:'OTHER' },
]

/* ───────────── 유효성 검사 ───────────── */
const req=(v:any)=>!!String(v??'').trim()||'필수 항목입니다.'
const dateRangeRule=()=>!form.start_date||!form.end_date||
  new Date(form.end_date)>=new Date(form.start_date)||
  '종료일은 시작일 이후여야 합니다.'

/* ───────────── 저장 로직 ───────────── */
async function onSubmit(){
  const ok=await(formRef.value as any)?.validate?.()
  if(!ok?.valid)return
  if(!form.employee_id)return error('직원을 선택하세요.')

  try{
    saving.value=true
    await ContractsApi.create({
      employee_id:form.employee_id,
      property_code:form.property_code,
      contract_type:form.contract_type,
      start_date:form.start_date,
      end_date:form.end_date||null,
      pay_type:form.contract_type,
      salary:form.salary,
      memo:form.memo||'',
    })
    success('계약이 등록되었습니다.')
    emit('saved')                 // 부모 reload()
    emit('update:open',false)     // 다이얼로그 닫기
  }catch(e:any){
    error('저장 실패: '+(e?.message||'서버 오류'))
  }finally{saving.value=false}
}

/* ───────────── 오픈 시 초기화 ───────────── */
watch(()=>props.open,v=>{
  if(v){
    form.employee_id=null
    form.contract_type='MONTHLY'
    form.salary=null
    form.start_date=''
    form.end_date=''
    form.memo=''
  }
  nextTick(()=>formRef.value?.resetValidation?.())
})
</script>

<style scoped>
.v-card { background: rgb(var(--v-theme-surface)); }
</style>
