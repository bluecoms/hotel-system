<!-- ============================================================================
  File    : src/ui/components/hr/DialogEmployeeForm.vue
  Version : 1.6.1 (2025-10-22 Final Stable · Property Sync)
  Purpose : Hotel Admin — 신규 직원 등록 다이얼로그
  ------------------------------------------------------------------------------
  주요 기능:
    • 신규 직원 등록 (사번 자동 생성)
    • 부서/직책/직급 → 기준정보(Master)에서 자동 로드
    • 주민번호, 연락처, 급여계좌, 이메일까지 등록
    • ✅ property_code 자동 주입 (localStorage → .env → MOP)
    • ✅ contract 연동 대비 (계좌/주민번호/입사일 자동 포함)
============================================================================ -->
<template>
  <v-dialog
    :model-value="open"
    max-width="720"
    persistent
    @update:model-value="v => emit('update:open', v)"
  >
    <v-card class="rounded-2xl">
      <!-- ───── 헤더 ───── -->
      <v-card-title class="d-flex align-center justify-space-between py-3 px-5">
        <div class="d-flex align-center gap-2">
          <v-icon icon="mdi-account-plus-outline" size="20" class="text-primary" />
          <span class="text-h6 font-weight-medium">신규 직원 등록</span>
        </div>
        <v-btn icon="mdi-close" variant="text" @click="emit('update:open', false)" />
      </v-card-title>

      <v-divider />

      <!-- ───── 본문 ───── -->
      <v-card-text class="px-5 py-4">
        <v-form ref="formRef" v-model="valid">
          <v-row dense>
            <!-- 사번 (자동 생성) -->
            <v-col cols="12" md="4">
              <v-text-field
                label="사번"
                :model-value="form.emp_no || '자동 생성'"
                variant="outlined"
                density="comfortable"
                readonly
                hide-details
              />
            </v-col>

            <!-- 성명 -->
            <v-col cols="12" md="8">
              <v-text-field
                ref="nameRef"
                v-model.trim="form.name"
                label="성명"
                variant="outlined"
                density="comfortable"
                :rules="[req]"
                hide-details="auto"
              />
            </v-col>

            <!-- 부서 -->
            <v-col cols="12" md="6">
              <v-select
                v-model="form.dept"
                :items="deptItems"
                label="부서"
                item-title="title"
                item-value="value"
                variant="outlined"
                density="comfortable"
                :rules="[req]"
                hide-details="auto"
              />
            </v-col>

            <!-- 직책 -->
            <v-col cols="12" md="6">
              <v-select
                v-model="form.title"
                :items="titleItems"
                label="직책"
                item-title="title"
                item-value="value"
                variant="outlined"
                density="comfortable"
                :rules="[req]"
                hide-details="auto"
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
                hide-details="auto"
              />
            </v-col>

            <!-- 주민번호 -->
            <v-col cols="12" md="6">
              <v-text-field
                v-model.trim="form.rrn_mask"
                label="주민번호"
                placeholder="예: 900101-1******"
                hint="계약서 자동주입용 (생년월일 변환)"
                persistent-hint
                variant="outlined"
                density="comfortable"
                hide-details="auto"
                @blur="form.rrn_mask = formatRrn(form.rrn_mask)"
              />
            </v-col>

            <!-- 연락처 -->
            <v-col cols="12" md="6">
              <v-text-field
                v-model.trim="form.phone"
                label="연락처"
                placeholder="예: 010-1234-5678"
                variant="outlined"
                density="comfortable"
                hide-details="auto"
              />
            </v-col>

            <!-- 이메일 -->
            <v-col cols="12" md="6">
              <v-text-field
                v-model.trim="form.email"
                label="이메일"
                type="email"
                hint="입력 시 로그인 아이디로 사용됩니다."
                persistent-hint
                variant="outlined"
                density="comfortable"
                hide-details="auto"
              />
            </v-col>

            <!-- 급여계좌 -->
            <v-col cols="12" md="6">
              <v-text-field
                v-model.trim="form.bank_name"
                label="은행명"
                placeholder="예: 국민은행"
                variant="outlined"
                density="comfortable"
                hide-details="auto"
              />
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model.trim="form.account_mask"
                label="계좌번호"
                placeholder="예: 123-4567-8901"
                hint="계약서 자동주입용 (마스킹 저장)"
                persistent-hint
                variant="outlined"
                density="comfortable"
                hide-details="auto"
                @blur="form.account_last4 = form.account_mask.slice(-4)"
              />
            </v-col>

            <!-- 주소 -->
            <v-col cols="12">
              <v-text-field
                v-model.trim="form.address"
                label="주소"
                variant="outlined"
                density="comfortable"
                hide-details="auto"
              />
            </v-col>

            <!-- 입사일 -->
            <v-col cols="12" md="6">
              <v-text-field
                v-model="form.hire_date"
                type="date"
                label="입사일"
                variant="outlined"
                density="comfortable"
                :rules="[req]"
                hide-details="auto"
              />
            </v-col>

            <!-- 메모 -->
            <v-col cols="12">
              <v-textarea
                v-model.trim="form.memo"
                label="메모(선택)"
                rows="2"
                variant="outlined"
                density="comfortable"
                hide-details="auto"
              />
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>

      <v-divider />

      <!-- ───── 푸터 ───── -->
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
/* ===========================================================================
   신규 직원 등록 (Employee Create)
   ---------------------------------------------------------------------------
   주요 흐름:
     1. 기준정보 로드 → 부서/직책/직급 선택지 생성
     2. 사번 자동 생성 (getNextEmpNo)
     3. property_code 자동 주입 (localStorage → .env → MOP)
     4. 주민번호/계좌번호 마스킹 및 검증 처리
     5. EmployeesApi.createEmployee() 호출 후 저장 완료 토스트
=========================================================================== */
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useToast } from '@/ui/composables/useToast'
import * as EmployeesApi from '@/services/employees'
import * as MasterApi from '@/services/master'

/* Props / Emits */
const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ (e:'update:open', v:boolean):void; (e:'saved'):void }>()

/* 상태 */
const { success, error } = useToast()
const formRef = ref()
const valid = ref(false)
const saving = ref(false)
const nameRef = ref<HTMLInputElement>()

/* 기준정보 선택지 */
const deptItems  = ref<{ title: string; value: string }[]>([])
const titleItems = ref<{ title: string; value: string }[]>([])
const rankItems  = ref<{ title: string; value: string }[]>([])

/* 폼 데이터 */
const propertyCode =
  localStorage.getItem('property_code') ||
  import.meta.env.VITE_DEFAULT_PROPERTY_CODE ||
  'MOP'

const form = reactive({
  emp_no: '',
  name: '',
  dept: '',
  title: '',
  rank: '',
  rrn_mask: '',
  phone: '',
  email: '',
  address: '',
  bank_name: '',
  account_mask: '',
  account_last4: '',
  hire_date: new Date().toISOString().slice(0, 10),
  memo: '',
  property_code: propertyCode,   // ✅ property_code 자동 주입
})

/* 필수값 검증 */
const req = (v: any) => !!String(v ?? '').trim() || '필수 항목입니다.'

/* 주민번호 포맷 */
function formatRrn(val?: string) {
  if (!val) return ''
  const digits = String(val).replace(/[^0-9]/g, '').slice(0, 13)
  if (digits.length <= 6) return digits
  return `${digits.slice(0, 6)}-${digits.slice(6)}`
}

/* 기준정보 로드 */
async function loadOptions() {
  try {
    const depts = await MasterApi.listDepartments()
    deptItems.value = depts.map((d: any) => ({ title: d.name, value: d.code }))
  } catch { deptItems.value = [] }

  try {
    const titles = await MasterApi.listTitles()
    titleItems.value = titles.map((t: any) => ({ title: t.name, value: t.code }))
  } catch { titleItems.value = [] }

  try {
    const ranks = await MasterApi.listRanks()
    rankItems.value = ranks.map((r: any) => ({ title: r.name, value: r.code }))
  } catch { rankItems.value = [] }
}

/* 저장 */
async function onSubmit() {
  const ok = await (formRef.value as any)?.validate?.()
  if (!ok?.valid) return

  try {
    saving.value = true
    await EmployeesApi.createEmployee({
      emp_no: form.emp_no || '',
      name: form.name,
      dept: form.dept,
      title: form.title,
      rank: form.rank,
      rrn_mask: form.rrn_mask,
      phone: form.phone,
      email: form.email,
      address: form.address,
      bank_name: form.bank_name,
      account_mask: form.account_mask,
      account_last4: form.account_last4,
      hire_date: form.hire_date || null,
      memo: form.memo || '',
      property_code: form.property_code,   // ✅ 전송 포함
    })
    success('직원이 등록되었습니다.')
    emit('saved')
    emit('update:open', false)
  } catch (e: any) {
    error('저장 실패: ' + (e?.message || '서버 오류'))
  } finally {
    saving.value = false
  }
}

/* 다이얼로그 오픈 시: 옵션 + 사번 로드 + 포커스 */
onMounted(async () => {
  await loadOptions()
  try {
    const res = await MasterApi.getNextEmpNo()
    form.emp_no = res?.next_emp_no || '자동 생성'
  } catch {
    form.emp_no = '자동 생성'
  }
  nextTick(() => nameRef.value?.focus())
})
</script>

<style scoped>
.v-card {
  background: rgb(var(--v-theme-surface));
}
</style>
