<template>
  <v-dialog
    :model-value="open"
    max-width="880"
    :persistent="loading"
    @update:model-value="v => emit('update:open', v)"
  >
    <v-card>
      <v-card-title class="d-flex align-center justify-space-between py-3">
        <div class="d-flex align-center gap-2">
          <v-icon icon="mdi-file-document-edit-outline" class="mr-1" />
          <div>
            <div class="text-subtitle-1 font-weight-bold">
              {{ isEdit ? '계약 수정' : '새 계약 등록' }} · {{ tLabel }}
            </div>
            <div class="text-caption text-grey-darken-1">
              계약 유형에 따라 필요한 입력만 보입니다.
            </div>
          </div>
        </div>
        <v-btn
          :disabled="loading"
          icon="mdi-close"
          variant="text"
          @click="emit('update:open', false)"
        />
      </v-card-title>

      <v-divider />

      <v-card-text class="pt-4">
        <v-alert
          v-if="dayClosed"
          type="warning"
          variant="tonal"
          class="mb-4"
        >
          오늘은 마감 상태입니다. 저장이 제한될 수 있어요.
        </v-alert>

        <div class="d-flex flex-wrap gap-2 mb-4">
          <v-chip size="small" variant="outlined">지점: {{ propertyCode }}</v-chip>
          <v-chip size="small" variant="tonal">{{ form.contract_date || bizDate }}</v-chip>
          <v-chip size="small" variant="tonal" v-if="form.status">{{ form.status }}</v-chip>
        </div>

        <v-form ref="formRef" v-model="valid" @submit.prevent="onSubmit">
          <div class="section-title">기본 정보</div>
          <v-row dense class="mb-4">
            <v-col cols="12" md="4">
              <v-select
                v-model="form.contract_type"
                :items="typeItems"
                label="계약 유형"
                :rules="[req]"
                hide-details="auto"
              />
            </v-col>
            <v-col cols="12" md="4">
              <v-text-field
                v-model="form.employee_name"
                label="근로자 성명"
                :rules="[req]"
                hide-details="auto"
                placeholder="예: 김OO"
              />
            </v-col>
            <v-col cols="12" md="4">
              <v-text-field
                v-model="form.phone"
                label="연락처"
                hide-details="auto"
                placeholder="숫자만 입력"
                inputmode="numeric"
              />
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model="form.department"
                label="부서"
                hide-details="auto"
                placeholder="예: 객실팀 / F&B / 관리"
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="form.position"
                label="직책"
                hide-details="auto"
                placeholder="예: 사원, 주임, 대리…"
              />
            </v-col>
          </v-row>

          <div class="section-title">지급/계좌 정보</div>
          <v-row dense class="mb-4">
            <v-col cols="12" md="6">
              <v-text-field
                v-model="form.address"
                label="주소"
                hide-details="auto"
              />
            </v-col>
            <v-col cols="12" md="3">
              <v-text-field
                v-model="form.bank_name"
                label="은행명"
                hide-details="auto"
                placeholder="예: 농협"
              />
            </v-col>
            <v-col cols="12" md="3">
              <v-text-field
                v-model="form.account_no"
                label="계좌번호"
                hide-details="auto"
                inputmode="numeric"
              />
            </v-col>
          </v-row>

          <div class="section-title">기간</div>
          <v-row dense class="mb-4">
            <v-col cols="12" md="4">
              <v-text-field
                v-model="form.start_date"
                type="date"
                label="시작일"
                :rules="[req]"
                hide-details="auto"
              />
            </v-col>
            <v-col cols="12" md="4">
              <v-text-field
                v-model="form.end_date"
                type="date"
                label="종료일(선택)"
                :rules="[endAfterStart]"
                hide-details="auto"
              />
            </v-col>
            <v-col cols="12" md="4">
              <v-text-field
                v-model="form.contract_date"
                type="date"
                label="계약일"
                hide-details="auto"
              />
            </v-col>
          </v-row>

          <div class="section-title">보수</div>
          <v-row dense class="mb-1">
            <v-col cols="12" md="4" v-if="form.contract_type === 'MONTHLY'">
              <v-text-field
                v-model.number="form.salary_monthly"
                type="number"
                inputmode="numeric"
                min="0"
                label="월 급여총액(세전)"
                prefix="₩"
                placeholder="예: 2,700,000"
                hide-details="auto"
              />
            </v-col>

            <v-col cols="12" md="4" v-else>
              <v-text-field
                v-model.number="form.hourly_wage"
                type="number"
                inputmode="numeric"
                min="0"
                label="시급"
                prefix="₩"
                placeholder="예: 10,030"
                hide-details="auto"
              />
            </v-col>

            <v-col cols="12" md="4">
              <v-text-field
                v-model.number="form.business_expense_limit"
                type="number"
                inputmode="numeric"
                min="0"
                label="업무추진비 한도(월)"
                prefix="₩"
                placeholder="선택입력"
                hide-details="auto"
              />
            </v-col>

            <v-col cols="12" md="4">
              <v-switch
                v-model="form.is_manager_52h"
                inset
                color="primary"
                :label="'팀장 직책(주52시간 포괄 적용)'"
                hide-details
              />
            </v-col>
          </v-row>

          <v-expand-transition>
            <v-alert
              v-if="minWageWarn"
              type="warning"
              variant="tonal"
              class="mt-2"
            >
              {{ minWageWarn }}
            </v-alert>
          </v-expand-transition>

          <div class="section-title mt-5">기타</div>
          <v-row dense>
            <v-col cols="12" md="8">
              <v-text-field
                v-model="form.tags"
                label="태그"
                hint="#로 구분 (예: #프론트 #야간)"
                persistent-hint
                hide-details="auto"
              />
            </v-col>
            <v-col cols="12">
              <v-textarea
                v-model="form.memo"
                label="메모"
                rows="3"
                hide-details="auto"
              />
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>

      <v-divider />

      <v-card-actions class="justify-end">
        <v-btn :disabled="loading" variant="text" @click="emit('update:open', false)">
          닫기
        </v-btn>
        <v-btn color="primary" :loading="loading" @click="onSubmit">
          {{ isEdit ? '수정' : '저장' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import http from '@/services/http'
import { useToast } from '@/ui/composables/useToast'

type ContractType = 'MONTHLY' | 'PARTTIME' | 'DAILY'
type Status = 'DRAFT' | 'ACTIVE' | 'ENDED'

type ContractForm = {
  id?: string
  contract_type: ContractType
  employee_name: string
  phone?: string
  department?: string
  position?: string
  address?: string
  bank_name?: string
  account_no?: string
  start_date: string
  end_date?: string
  contract_date?: string
  salary_monthly?: number
  hourly_wage?: number
  business_expense_limit?: number
  is_manager_52h?: boolean
  tags?: string
  memo?: string
  status?: Status
}

const props = defineProps<{
  open: boolean
  propertyCode: string
  bizDate: string
  dayStatus?: 'OPEN' | 'CLOSED'
  id?: string | null
  initial?: Partial<ContractForm> | null
}>()

const emit = defineEmits<{
  (e: 'update:open', v: boolean): void
  (e: 'saved', payload: { id: string; data: any }): void
}>()

const { success, error } = useToast()

const formRef = ref()
const valid = ref(false)
const loading = ref(false)

const dayClosed = computed(() => props.dayStatus === 'CLOSED')
const isEdit = computed(() => !!(props.id || props.initial?.id))

const form = reactive<ContractForm>({
  id: props.initial?.id,
  contract_type: (props.initial?.contract_type as ContractType) ?? 'MONTHLY',
  employee_name: props.initial?.employee_name ?? '',
  phone: props.initial?.phone ?? '',
  department: props.initial?.department ?? '',
  position: props.initial?.position ?? '',
  address: props.initial?.address ?? '',
  bank_name: props.initial?.bank_name ?? '',
  account_no: props.initial?.account_no ?? '',
  start_date: props.initial?.start_date ?? props.bizDate,
  end_date: props.initial?.end_date ?? '',
  contract_date: props.initial?.contract_date ?? props.bizDate,
  salary_monthly: props.initial?.salary_monthly ?? undefined,
  hourly_wage: props.initial?.hourly_wage ?? undefined,
  business_expense_limit: props.initial?.business_expense_limit ?? undefined,
  is_manager_52h: props.initial?.is_manager_52h ?? false,
  tags: props.initial?.tags ?? '',
  memo: props.initial?.memo ?? '',
  status: (props.initial?.status as Status) ?? 'DRAFT',
})

/** 다이얼로그 열릴 때 초기값 싱크/리셋 */
watch(() => props.open, (v) => {
  if (!v) return
  // 열린 순간 최신 initial로 동기화
  if (props.initial) {
    Object.assign(form, {
      id: props.initial.id,
      contract_type: (props.initial.contract_type as ContractType) ?? 'MONTHLY',
      employee_name: props.initial.employee_name ?? '',
      phone: props.initial.phone ?? '',
      department: props.initial.department ?? '',
      position: props.initial.position ?? '',
      address: props.initial.address ?? '',
      bank_name: props.initial.bank_name ?? '',
      account_no: props.initial.account_no ?? '',
      start_date: props.initial.start_date ?? props.bizDate,
      end_date: props.initial.end_date ?? '',
      contract_date: props.initial.contract_date ?? props.bizDate,
      salary_monthly: props.initial.salary_monthly ?? undefined,
      hourly_wage: props.initial.hourly_wage ?? undefined,
      business_expense_limit: props.initial.business_expense_limit ?? undefined,
      is_manager_52h: !!props.initial.is_manager_52h,
      tags: props.initial.tags ?? '',
      memo: props.initial.memo ?? '',
      status: (props.initial.status as Status) ?? 'DRAFT',
    })
  } else {
    // 신규 모드 기본값
    Object.assign(form, {
      id: undefined,
      contract_type: 'MONTHLY',
      employee_name: '',
      phone: '',
      department: '',
      position: '',
      address: '',
      bank_name: '',
      account_no: '',
      start_date: props.bizDate,
      end_date: '',
      contract_date: props.bizDate,
      salary_monthly: undefined,
      hourly_wage: undefined,
      business_expense_limit: undefined,
      is_manager_52h: false,
      tags: '',
      memo: '',
      status: 'DRAFT',
    })
  }
})

const typeItems = [
  { title: '월급(정규직)', value: 'MONTHLY' },
  { title: '아르바이트', value: 'PARTTIME' },
  { title: '일용직', value: 'DAILY' },
]

const tLabel = computed(() => {
  switch (form.contract_type) {
    case 'PARTTIME': return '아르바이트 근로계약'
    case 'DAILY': return '일일 근로계약'
    default: return '월급 근로계약'
  }
})

const MINIMUM_WAGE_2025 = 10030
const MONTHLY_WORK_HOURS = 209

const minWageWarn = computed(() => {
  if (form.contract_type === 'MONTHLY' && form.salary_monthly) {
    const baseMin = MONTHLY_WORK_HOURS * MINIMUM_WAGE_2025
    if (form.salary_monthly < baseMin) {
      return `경고: 월급 총액이 2025년 기준 최저월급(약 ${Math.round(baseMin).toLocaleString()}원) 미만입니다.`
    }
  }
  if (form.contract_type !== 'MONTHLY' && form.hourly_wage) {
    if (form.hourly_wage < MINIMUM_WAGE_2025) {
      return `경고: 시급이 2025년 최저시급(${MINIMUM_WAGE_2025.toLocaleString()}원) 미만입니다.`
    }
  }
  return ''
})

const req = (v: any) => !!String(v ?? '').trim() || '필수값입니다.'
const endAfterStart = (v: any) => {
  if (!v) return true
  if (!form.start_date) return true
  try {
    return new Date(v) >= new Date(form.start_date) || '시작일 이후여야 합니다.'
  } catch { return true }
}

async function onSubmit() {
  if (dayClosed.value) { error('마감일에는 저장할 수 없어요.'); return }
  const ok = await formRef.value?.validate?.()
  if (!ok?.valid) return

  const payload = {
    property_code: props.propertyCode,
    ...form,
  }

  try {
    loading.value = true
    const url = isEdit.value ? `/contracts/${form.id}` : `/contracts`
    const method = isEdit.value ? http.put : http.post
    const res: any = await method(url, payload)
    success(isEdit.value ? '수정되었습니다.' : '저장되었습니다.')
    emit('saved', { id: String(res?.id ?? form.id ?? ''), data: res })
    emit('update:open', false)
  } catch (e: any) {
    error('저장 실패')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.section-title {
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 8px;
}
</style>
