<!-- ============================================================================
  File    : src/ui/components/hr/DialogEmployeeForm.vue
  Version : 2.2 Final (2025-11-04 · Options-First · Fallback Safe · Monthly Salary Auto)
  Purpose : Hotel Admin — 신규 직원 등록 다이얼로그 (계약정보 통합 입력)
  ------------------------------------------------------------------------------
  변경 요약 (v2.2)
    ✅ v-select는 모두 /options 엔드포인트 우선 사용 (가벼운 payload/빠른 응답)
    ✅ /options 미구현/405 시 list() 기반으로 폴백 (운영/개발 안전)
    ✅ 급여등급(연봉) → 월급 자동 환산(salary = annual_salary / 12)
    ✅ Master API 캐시(1회 로드 후 재사용)로 재오픈 지연 최소화
    ✅ 주석 보강 및 오류 로그 최소화(사용자 노출 토스트만 유지)
============================================================================ -->
<template>
  <v-dialog
    :model-value="open"
    max-width="760"
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
            <!-- 사번 -->
            <v-col cols="12" md="4">
              <v-text-field
                label="사번"
                :model-value="form.emp_no || '자동 생성'"
                variant="outlined"
                density="comfortable"
                readonly
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
              />
            </v-col>

            <!-- 부서 (SSOT: /api/master/departments/options) -->
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
              />
            </v-col>

            <!-- 직책 (SSOT: /api/master/titles/options) -->
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
              />
            </v-col>

            <!-- 급여등급(연봉) → 월급 자동환산 -->
            <v-col cols="12" md="6">
              <v-select
                v-model="form.rank"
                :items="rankItems"
                label="직급(급여등급)"
                item-title="title"
                item-value="value"
                variant="outlined"
                density="comfortable"
                :rules="[req]"
                @update:model-value="onRankSelect"
              />
            </v-col>

            <!-- 은행 (SSOT: /api/master/banks/options) -->
            <v-col cols="12" md="6">
              <v-select
                v-model="form.bank_name"
                :items="bankItems"
                label="은행명"
                item-title="title"
                item-value="value"
                variant="outlined"
                density="comfortable"
              />
            </v-col>

            <!-- 계좌번호 -->
            <v-col cols="12" md="6">
              <v-text-field
                v-model.trim="form.account_mask"
                label="계좌번호"
                placeholder="예: 123-4567-8901"
                hint="계약서 자동주입용 (마스킹 저장)"
                persistent-hint
                variant="outlined"
                density="comfortable"
                @blur="form.account_last4 = form.account_mask.slice(-4)"
              />
            </v-col>

            <!-- 주민번호 -->
            <v-col cols="12" md="6">
              <v-text-field
                v-model.trim="form.rrn_mask"
                label="주민번호"
                placeholder="900101-1******"
                hint="계약서 자동주입용"
                persistent-hint
                variant="outlined"
                density="comfortable"
                @blur="form.rrn_mask = formatRrn(form.rrn_mask)"
              />
            </v-col>

            <!-- 연락처 -->
            <v-col cols="12" md="6">
              <v-text-field
                v-model.trim="form.phone"
                label="연락처"
                placeholder="010-1234-5678"
                variant="outlined"
                density="comfortable"
              />
            </v-col>

            <!-- 이메일 -->
            <v-col cols="12" md="6">
              <v-text-field
                v-model.trim="form.email"
                label="이메일"
                type="email"
                hint="로그인 계정용 (선택)"
                persistent-hint
                variant="outlined"
                density="comfortable"
              />
            </v-col>

            <!-- 주소 -->
            <v-col cols="12">
              <v-text-field
                v-model.trim="form.address"
                label="주소"
                variant="outlined"
                density="comfortable"
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
              />
            </v-col>

            <!-- ───── 계약정보 입력 ───── -->
            <v-col cols="12" class="mt-3">
              <h4 class="text-subtitle-2 font-weight-bold mb-2">계약 정보</h4>
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
              />
            </v-col>

            <!-- 계약 시작/종료 -->
            <v-col cols="12" md="6">
              <v-text-field
                v-model="form.contract_start"
                type="date"
                label="계약 시작일"
                variant="outlined"
                density="comfortable"
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="form.contract_end"
                type="date"
                label="계약 종료일(선택)"
                variant="outlined"
                density="comfortable"
              />
            </v-col>

            <!-- 급여(월급 자동 계산) -->
            <v-col cols="12" md="6">
              <v-text-field
                v-model.number="form.salary"
                label="급여(₩, 월 환산)"
                type="number"
                variant="outlined"
                density="comfortable"
                placeholder="예: 3000000"
                hint="급여등급(연봉)을 12로 나눈 값"
                persistent-hint
                readonly
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
   Script: DialogEmployeeForm (v2.2)
   ---------------------------------------------------------------------------
   • v-select → /options 엔드포인트 우선 사용 (경량/표준화)
   • /options 미구현/405 시 list() 폴백 (안전)
   • 급여등급 연봉 → 월급 자동환산 유지
   • 옵션 캐시(컴포넌트 정적 변수)로 재오픈 속도 개선
=========================================================================== */
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useToast } from '@/ui/composables/useToast'
import * as EmployeesApi from '@/services/employees'
import * as MasterApi from '@/services/master'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ (e:'update:open', v:boolean):void; (e:'saved'):void }>()
const { success, error } = useToast()

const formRef = ref()
const valid = ref(false)
const saving = ref(false)
const nameRef = ref<HTMLInputElement>()

/** v-select 옵션 — /options 우선, 실패 시 list() 폴백 */
const deptItems  = ref<{ title: string; value: string }[]>([])
const titleItems = ref<{ title: string; value: string }[]>([])
const rankItems  = ref<{ title: string; value: string; annual_salary?: number }[]>([])
const bankItems  = ref<{ title: string; value: string }[]>([])

/** 1회 캐시 플래그 */
let cached = false

/** 계약유형 (정적) */
const contractTypes = [
  { title: '정규직', value: 'MONTHLY' },
  { title: '시간제', value: 'HOURLY' },
  { title: '기타',  value: 'OTHER' },
]

/** property_code (SSOT: localStorage → .env → 기본 MOP) */
const propertyCode =
  localStorage.getItem('property_code') ||
  import.meta.env.VITE_DEFAULT_PROPERTY_CODE ||
  'MOP'

/** 폼 데이터 */
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
  hire_date: new Date().toISOString().slice(0,10),
  memo: '',
  property_code: propertyCode,
  contract_type: 'MONTHLY',
  contract_start: new Date().toISOString().slice(0,10),
  contract_end: '',
  salary: null as number | null,
})

/** 필수값 검증 */
const req = (v:any) => !!String(v ?? '').trim() || '필수 항목입니다.'

/** 주민번호 포맷 */
function formatRrn(val?: string) {
  if (!val) return ''
  const d = String(val).replace(/[^0-9]/g, '').slice(0, 13)
  return d.length <= 6 ? d : `${d.slice(0,6)}-${d.slice(6)}`
}

/** 급여등급 선택 시 → 월급 계산 */
function onRankSelect(code: string) {
  const sel = rankItems.value.find(r => r.value === code)
  form.salary = sel?.annual_salary ? Math.round(sel.annual_salary / 12) : null
}

/** 옵션 로드 — /options 우선, 실패 시 list() 폴백 */
async function loadOptions() {
  if (cached) return
  cached = true
  try {
    // 1) /options 가벼운 호출 우선
    const [deptOpt, titleOpt, bankOpt] = await Promise.all([
      MasterApi.departmentOptions?.() ?? Promise.reject('no-dept-options'),
      MasterApi.titleOptions?.()      ?? Promise.reject('no-title-options'),
      MasterApi.bankOptions?.()       ?? Promise.reject('no-bank-options'),
    ])

    deptItems.value  = Array.isArray(deptOpt)  ? deptOpt  : []
    titleItems.value = Array.isArray(titleOpt) ? titleOpt : []
    bankItems.value  = Array.isArray(bankOpt)  ? bankOpt  : []
  } catch (e) {
    console.warn('[DialogEmployeeForm] /options 호출 실패 → list() 폴백', e)
    // 2) 폴백: list()로 변환
    try {
      const [depts, titles, banks] = await Promise.all([
        MasterApi.listDepartments(),
        MasterApi.listTitles(),
        MasterApi.listBanks(),
      ])
      deptItems.value  = (depts  || []).map((d:any)=>({ title:d.name,  value:d.code }))
      titleItems.value = (titles || []).map((t:any)=>({ title:t.name,  value:t.code }))
      bankItems.value  = (banks  || []).map((b:any)=>({ title:b.name,  value:b.name }))
    } catch (err) {
      console.error('[DialogEmployeeForm] list() 폴백도 실패', err)
      deptItems.value = []
      titleItems.value = []
      bankItems.value = []
    }
  }

  // 급여등급은 연봉이 필요하므로 list() 고정
  try {
    const ranks = await MasterApi.listSalaryGrades()
    rankItems.value = (ranks || []).map((r:any)=>({
      title: r.name, value: r.code, annual_salary: r.annual_salary ?? r.base_salary ?? null,
    }))
  } catch (err) {
    console.error('[DialogEmployeeForm] 급여등급 로드 실패', err)
    rankItems.value = []
  }
}

/** 저장 처리 */
async function onSubmit() {
  const ok = await (formRef.value as any)?.validate?.()
  if (!ok?.valid) return
  try {
    saving.value = true
    await EmployeesApi.createEmployee({ ...form })
    success('직원이 등록되었습니다.')
    emit('saved')
    emit('update:open', false)
  } catch (e:any) {
    error('저장 실패: ' + (e?.message || '서버 오류'))
  } finally {
    saving.value = false
  }
}

/** 초기 로드 */
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
.v-card { background: rgb(var(--v-theme-surface)); }
</style>
