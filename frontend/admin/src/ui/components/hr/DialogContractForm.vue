<!-- ============================================================================
  File    : src/ui/components/hr/DialogContractForm.vue
  Version : 2.0 Final (2025-10-23 · HR 간소화 7차 · 단순화 & SSOT 통합)
  Purpose : 신규 계약 등록 다이얼로그 (HR 모듈 / append-only 구조)
  ------------------------------------------------------------------------------
  변경 요약:
    ✅ 직원 선택 → 기간/급여/유형 최소 필드로 단순화
    ✅ ContractsApi.create() 사용 (append-only)
    ✅ 계약유형: MONTHLY / HOURLY / OTHER 옵션 통일
    ✅ 저장 후 emit('saved') → 부모 reload() 완전 동기화
============================================================================ -->
<template>
  <v-dialog
    :model-value="open"
    max-width="720"
    persistent
    @update:model-value="v => emit('update:open', v)"
  >
    <v-card class="rounded-2xl">
      <!-- ▣ 헤더 -->
      <v-card-title class="d-flex align-center justify-space-between py-3 px-5">
        <div class="d-flex align-center gap-2">
          <v-icon icon="mdi-file-document-edit-outline" size="20" class="text-primary" />
          <span class="text-h6 font-weight-medium">신규 계약 등록</span>
        </div>
        <v-btn icon="mdi-close" variant="text" @click="emit('update:open', false)" />
      </v-card-title>

      <v-divider />

      <!-- ▣ 본문 -->
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

            <!-- 사번 -->
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

            <!-- 계약 유형 -->
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

            <!-- 급여 -->
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

      <!-- ▣ 푸터 -->
      <v-card-actions class="px-5 py-3 justify-end">
        <v-btn variant="text" color="grey" @click="emit('update:open', false)">취소</v-btn>
        <v-btn
          color="primary"
          variant="flat"
          prepend-icon="mdi-content-save"
          :loading="saving"
          @click="onSubmit"
        >
          저장
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, nextTick } from 'vue'
import { useToast } from '@/ui/composables/useToast'
import * as EmployeesApi from '@/services/employees'
import * as ContractsApi from '@/services/contracts'
import EmployeePicker from '@/ui/components/hr/EmployeePicker.vue'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ (e:'update:open',v:boolean):void; (e:'saved'):void }>()

const { success, error } = useToast()
const formRef = ref()
const valid = ref(false)
const saving = ref(false)

/* 직원 선택 및 컨텍스트 로드 */
const employeeId = ref<number|null>(null)
const empContext = ref<any>({ emp_no:'', name:'', dept_name:'', title_name:'' })

async function onEmployeeSelected(row:any|null){
  if(!row){empContext.value={};form.employee_id=null;return}
  form.employee_id=row.id
  try{
    const emp=await EmployeesApi.getEmployee(row.id)
    empContext.value={
      emp_no: emp.emp_no||'',
      name: emp.name||'',
      dept_name: emp.dept_name||emp.dept||'',
      title_name: emp.title_name||emp.title||'-'
    }
  }catch(e){console.error('[EmpLoad]',e)}
}

/* 폼 데이터 */
const propertyCode =
  localStorage.getItem('property_code') ||
  import.meta.env.VITE_DEFAULT_PROPERTY_CODE ||
  'MOP'

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

/* 유효성 */
const req=(v:any)=>!!String(v??'').trim()||'필수 항목입니다.'
const dateRangeRule=()=>!form.start_date||!form.end_date||
  new Date(form.end_date)>=new Date(form.start_date)||
  '종료일은 시작일 이후여야 합니다.'

/* 저장 */
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
    emit('saved')
    emit('update:open',false)
  }catch(e:any){
    error('저장 실패: '+(e?.message||'서버 오류'))
  }finally{saving.value=false}
}

/* 오픈 시 리셋 */
watch(()=>props.open,v=>{
  if(v){form.employee_id=null;form.contract_type='MONTHLY';form.salary=null;form.start_date='';form.end_date='';form.memo=''}
  nextTick(()=>formRef.value?.resetValidation?.())
})
</script>

<style scoped>
.v-card { background: rgb(var(--v-theme-surface)); }
</style>
