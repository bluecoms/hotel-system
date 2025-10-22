<!-- ============================================================================
  File    : src/ui/components/hr/DialogContractForm.vue
  Version : 1.6.3 (2025-10-23 · Final Stable / EmployeePicker Sync)
  Purpose : 신규 계약 등록 다이얼로그 (Hotel Admin HR 모듈)
  ------------------------------------------------------------------------------
  변경 요약:
    ✅ EmployeePicker 최신 구조 반영 (Property 자동 주입 + 즉시 fetch)
    ✅ 급여계좌 필드 제거 (meta.account 에서만 관리)
    ✅ 다이얼로그 열릴 때 Picker 재조회 보강 (watch isOpen)
    ✅ rank 선택 시 salary 자동 계산 (연봉/12)
    ✅ UI 여백, 밀도, 힌트 정돈
  ------------------------------------------------------------------------------
  연계 서비스:
    • EmployeesApi.getEmployee(id)
    • MasterApi.listSalaryGrades()
    • ContractsApi.create(payload)
============================================================================ -->
<template>
  <v-dialog
    :model-value="isOpen"
    max-width="720"
    persistent
    @update:model-value="setOpen"
  >
    <v-card class="rounded-2xl">
      <!-- ▣ 헤더 -->
      <v-card-title class="d-flex align-center justify-space-between py-3 px-5">
        <div class="d-flex align-center gap-2">
          <v-icon icon="mdi-file-document-edit-outline" size="20" class="text-primary" />
          <span class="text-h6 font-weight-medium">
            {{ form.id ? '계약 수정' : '신규 계약' }}
          </span>
        </div>
        <v-btn icon="mdi-close" variant="text" @click="setOpen(false)" />
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
                :only-active="true"
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
                hide-details
              />
            </v-col>

            <!-- 부서 / 직책 -->
            <v-col cols="12" md="6">
              <v-text-field
                :model-value="empContext.dept || '-'"
                label="부서"
                variant="outlined"
                density="comfortable"
                readonly
                hide-details
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                :model-value="empContext.title_name || '-'"
                label="직책"
                variant="outlined"
                density="comfortable"
                readonly
                hide-details
              />
            </v-col>

            <!-- 직급 -->
            <v-col cols="12" md="6">
              <v-select
                v-model="form.rank"
                :items="rankItems"
                label="직급"
                item-title="title"
                item-value="value"
                variant="outlined"
                density="comfortable"
                :rules="[req]"
                hide-details
              />
            </v-col>

            <!-- 월 급여 -->
            <v-col cols="12" md="6">
              <v-text-field
                v-model.number="form.salary"
                type="number"
                label="월 급여 (세전)"
                variant="outlined"
                density="comfortable"
                readonly
                hide-details
                hint="직급 기준 연봉에서 자동 계산됨"
                persistent-hint
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
                hide-details
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
                hide-details
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
                hide-details
              />
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>

      <v-divider />

      <!-- ▣ 푸터 -->
      <v-card-actions class="px-5 py-3 justify-end">
        <v-btn variant="text" color="grey" @click="setOpen(false)">취소</v-btn>
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
import { ref, reactive, watch, computed, onMounted, nextTick } from 'vue'
import { useToast } from '@/ui/composables/useToast'
import * as MasterApi from '@/services/master'
import * as ContractsApi from '@/services/contracts'
import * as EmployeesApi from '@/services/employees'
import EmployeePicker from '@/ui/components/hr/EmployeePicker.vue'

/* ===========================================================================
   Props / Emits
=========================================================================== */
const props = defineProps<{ modelValue?: boolean; open?: boolean }>()
const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'update:open', v: boolean): void
  (e: 'saved', payload: any): void
}>()

/* ===========================================================================
   상태
=========================================================================== */
const isOpen = computed({
  get: () => props.open ?? props.modelValue ?? false,
  set: (v: boolean) => {
    emit('update:open', v)
    emit('update:modelValue', v)
  },
})
function setOpen(v: boolean) {
  isOpen.value = v
}

const { success, error } = useToast()
const formRef = ref()
const valid = ref(false)
const saving = ref(false)

/* ===========================================================================
   직원 선택 / 컨텍스트 로드
=========================================================================== */
const employeeId = ref<number | null>(null)
const empContext = ref<any>({
  emp_no: '',
  name: '',
  dept: '',
  title_name: '',
  bank_name: '',
  account_mask: '',
})

async function onEmployeeSelected(row: any | null) {
  if (!row) {
    empContext.value = {}
    form.employee_id = null
    return
  }
  form.employee_id = row.id
  try {
    const emp = await EmployeesApi.getEmployee(row.id)
    empContext.value = {
      emp_no: emp.emp_no || '',
      name: emp.name || '',
      dept: emp.dept || '',
      title_name: emp.title_name || emp.title || '',
      bank_name: emp.bank_name || '',
      account_mask: emp.account_mask || '',
    }
  } catch (e) {
    console.error('[EmpLoad]', e)
  }
}

/* ===========================================================================
   폼 데이터 (property_code 자동 주입)
=========================================================================== */
const propertyCode =
  localStorage.getItem('property_code') ||
  import.meta.env.VITE_DEFAULT_PROPERTY_CODE ||
  'MOP'

const form = reactive<any>({
  employee_id: null,
  rank: null,
  salary: null,
  start_date: '',
  end_date: '',
  memo: '',
  property_code: propertyCode,
})

/* ===========================================================================
   급여등급 로드 & 자동 계산
=========================================================================== */
const rankItems = ref<{ title: string; value: string; annual_salary: number }[]>([])
async function loadSalaryGrades() {
  try {
    const list = await MasterApi.listSalaryGrades()
    rankItems.value = list.map((g: any) => ({
      title: g.name,
      value: g.code,
      annual_salary: g.annual_salary ?? g.base_salary ?? 0,
    }))
  } catch (err) {
    console.error('[loadSalaryGrades]', err)
  }
}

watch(
  () => form.rank,
  (code) => {
    const grade = rankItems.value.find((g) => g.value === code)
    form.salary = grade ? Math.round((grade.annual_salary || 0) / 12) : null
  }
)

/* ===========================================================================
   유효성 / 저장
=========================================================================== */
const req = (v: any) => !!String(v ?? '').trim() || '필수 항목입니다.'
const dateRangeRule = () =>
  !form.start_date ||
  !form.end_date ||
  new Date(form.end_date) >= new Date(form.start_date) ||
  '종료일은 시작일 이후여야 합니다.'

async function onSubmit() {
  const ok = await (formRef.value as any)?.validate?.()
  if (!ok?.valid) return
  if (!form.employee_id) {
    error('직원을 선택하세요.')
    return
  }

  try {
    saving.value = true
    const payload = {
      employee_id: form.employee_id,
      property_code: form.property_code,
      contract_type: 'MONTHLY',
      start_date: form.start_date,
      end_date: form.end_date || null,
      pay_type: 'MONTHLY',
      salary: form.salary,
      memo: form.memo || '',
      meta: {
        rank: form.rank,
        account: `${empContext.value.bank_name ?? ''} ${empContext.value.account_mask ?? ''}`.trim(),
      },
    }
    await ContractsApi.create(payload)
    success('계약이 저장되었습니다.')
    emit('saved', payload)
    setOpen(false)
  } catch (e: any) {
    error('저장 실패: ' + (e?.message || '서버 오류'))
  } finally {
    saving.value = false
  }
}

/* ===========================================================================
   초기 로드
=========================================================================== */
watch(isOpen, async (v) => {
  if (v) await nextTick() // Dialog가 열릴 때 EmployeePicker fetch 보장
})
onMounted(loadSalaryGrades)
</script>

<style scoped>
.v-card {
  background: rgb(var(--v-theme-surface));
}
</style>
