<!-- ============================================================================
# File      : src/ui/components/hr/DialogEmployeeDetail.vue
# Version   : 1.1 (2025-11-10 · SSOT Stable · UI 정비 + 한글 주석 강화)
# Purpose   : 직원 상세 보기 다이얼로그 (기본정보 + 계약정보)
# ----------------------------------------------------------------------------
# 주요 개선:
#   ✅ 기본정보 / 계약정보 구역 분리 (시각적 가독성 향상)
#   ✅ 날짜 포맷터(fmtDate) 추가 (YYYY-MM-DD)
#   ✅ 계약상태 한글 표기 통일 (active→계약중, terminated→만료)
#   ✅ 스타일/라벨 정비 (Vuetify theme 기반)
# ----------------------------------------------------------------------------
# 목적:
#   • 직원 객체(props.employee) 정보를 읽기 전용으로 표시
#   • 상위에서 이미 데이터를 주입하므로 별도 API 호출 없음
#   • 닫기 버튼으로 부모 v-model 제어
# ----------------------------------------------------------------------------
# 연계:
#   • src/views/Admin/HR/Employees.vue
#   • src/views/Admin/HR/Contracts.vue
# ============================================================================
-->
<template>
  <v-dialog v-model="open" max-width="640" persistent>
    <v-card class="rounded-2xl">
      <!-- ▣ 헤더 -->
      <v-card-title class="d-flex align-center justify-space-between py-3 px-5">
        <div class="d-flex align-center gap-2">
          <v-icon icon="mdi-account" color="primary" />
          <span class="text-h6 font-weight-medium">
            {{ employee?.name || '직원 상세정보' }}
          </span>
        </div>
        <v-btn icon="mdi-close" variant="text" @click="close" />
      </v-card-title>

      <v-divider />

      <!-- ▣ 본문 -->
      <v-card-text class="px-5 py-4">
        <!-- ─── 기본 정보 ─── -->
        <div class="mb-3">
          <div class="text-subtitle-2 text-grey-darken-1 mb-1 font-weight-medium">
            기본 정보
          </div>
          <v-row dense>
            <v-col cols="12" md="6"><strong>사번</strong> {{ employee?.emp_no || '-' }}</v-col>
            <v-col cols="12" md="6"><strong>이메일</strong> {{ employee?.email || '-' }}</v-col>
            <v-col cols="12" md="6"><strong>부서</strong> {{ employee?.dept_name || employee?.dept || '-' }}</v-col>
            <v-col cols="12" md="6"><strong>직책</strong> {{ employee?.title_name || employee?.title || '-' }}</v-col>
            <v-col cols="12" md="6"><strong>입사일</strong> {{ fmtDate(employee?.hire_date) }}</v-col>
            <v-col cols="12" md="6"><strong>상태</strong> {{ employee?.is_active ? '재직' : '퇴직' }}</v-col>
          </v-row>
        </div>

        <v-divider class="my-3" />

        <!-- ─── 계약 정보 ─── -->
        <div>
          <div class="text-subtitle-2 text-grey-darken-1 mb-1 font-weight-medium">
            계약 정보
          </div>
          <v-row dense>
            <v-col cols="12" md="6">
              <strong>계약 상태</strong> {{ statusLabel(employee?.contract_status) }}
            </v-col>
            <v-col cols="12" md="6">
              <strong>월 급여(₩)</strong>
              {{ employee?.salary ? fmtCurrency(employee.salary) : '-' }}
            </v-col>
            <v-col cols="12" md="6">
              <strong>계약 시작일</strong> {{ fmtDate(employee?.contract_start) }}
            </v-col>
            <v-col cols="12" md="6">
              <strong>계약 종료일</strong> {{ fmtDate(employee?.contract_end) }}
            </v-col>
            <v-col cols="12">
              <strong>비고</strong> {{ employee?.memo || '-' }}
            </v-col>
          </v-row>
        </div>
      </v-card-text>

      <v-divider />

      <!-- ▣ 푸터 -->
      <v-card-actions class="justify-end px-5 py-3">
        <v-btn color="primary" variant="flat" @click="close">닫기</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
/* ============================================================================
   Script — DialogEmployeeDetail (v1.1)
   ---------------------------------------------------------------------------
   - props: modelValue(boolean), employee(Employee|null)
   - emits: update:modelValue
   - 기능: 직원 상세 정보 읽기 전용 표시 (기본/계약 구분)
============================================================================ */
import { ref, watch } from 'vue'
import type { Employee } from '@/services/employees'

/* ▣ Props / Emits */
const props = defineProps<{
  modelValue: boolean
  employee: Employee | null
}>()
const emit = defineEmits(['update:modelValue'])

/* ▣ 상태 */
const open = ref(props.modelValue)
watch(() => props.modelValue, v => (open.value = v))
watch(open, v => emit('update:modelValue', v))

/* ▣ 유틸 함수 */
function close() {
  emit('update:modelValue', false)
}

function fmtDate(v?: string | null) {
  if (!v) return '-'
  return String(v).slice(0, 10)
}

function fmtCurrency(n?: number | null) {
  if (!n) return '-'
  try { return n.toLocaleString('ko-KR') } catch { return String(n) }
}

function statusLabel(s?: string | null) {
  const v = (s || '').toLowerCase()
  if (v === 'active') return '계약중'
  if (v === 'terminated') return '만료'
  if (v === 'none' || !v) return '미계약'
  return s || '-'
}
</script>

<style scoped>
.v-card-text strong {
  display: inline-block;
  width: 110px;
  color: var(--v-theme-on-surface);
  font-weight: 600;
}
.text-subtitle-2 {
  letter-spacing: 0.2px;
}
</style>
