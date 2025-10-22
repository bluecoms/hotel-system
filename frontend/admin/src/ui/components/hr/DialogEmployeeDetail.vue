<!-- ============================================================================
# src/ui/components/hr/DialogEmployeeDetail.vue
───────────────────────────────────────────────────────────────
Version : 1.0.0 | Date : 2025-10-17 | Owner : Hotel Admin (HR)
Purpose : 직원 상세 보기 다이얼로그 (기본정보 + 계약정보)
───────────────────────────────────────────────────────────────
[핵심 기능]
- 직원 정보를 props로 받아서 읽기 전용으로 표시
- 기본정보(사번, 이름, 부서, 직책, 이메일, 입사일)
- 계약정보(상태, 계약시작일, 종료일)
- 닫기 버튼으로 상위 v-model 제어
───────────────────────────────────────────────────────────────
[API & 계약]
- API 호출 없음 (상위에서 employee 객체 주입)
- 인증: X-Internal-Token (상위 화면에서 처리됨)
───────────────────────────────────────────────────────────────
[변경 이력]
- 1.0.0: 최초 작성 (Employee 타입 확장 반영)
============================================================================ -->
<template>
  <v-dialog v-model="open" max-width="640" persistent>
    <v-card class="rounded-2xl">
      <!-- 헤더 -->
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

      <!-- 본문 -->
      <v-card-text class="px-5 py-3">
        <v-row dense>
          <v-col cols="12" md="6"><strong>사번:</strong> {{ employee?.emp_no || '-' }}</v-col>
          <v-col cols="12" md="6"><strong>이메일:</strong> {{ employee?.email || '-' }}</v-col>
          <v-col cols="12" md="6"><strong>부서:</strong> {{ employee?.dept || '-' }}</v-col>
          <v-col cols="12" md="6"><strong>직책:</strong> {{ employee?.title || '-' }}</v-col>
          <v-col cols="12" md="6"><strong>입사일:</strong> {{ employee?.hire_date || '-' }}</v-col>
          <v-col cols="12" md="6"><strong>계약상태:</strong> {{ employee?.contract_status || '미계약' }}</v-col>
          <v-col cols="12" md="6"><strong>계약시작일:</strong> {{ employee?.contract_start || '-' }}</v-col>
          <v-col cols="12" md="6"><strong>계약종료일:</strong> {{ employee?.contract_end || '-' }}</v-col>
          <v-col cols="12"><strong>비고:</strong> {{ employee?.memo || '-' }}</v-col>
        </v-row>
      </v-card-text>

      <v-divider />

      <v-card-actions class="justify-end px-5 py-3">
        <v-btn color="primary" variant="flat" @click="close">닫기</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Employee } from '@/services/employees'

const props = defineProps<{
  modelValue: boolean
  employee: Employee | null
}>()

const emit = defineEmits(['update:modelValue'])

const open = ref(props.modelValue)
watch(() => props.modelValue, v => (open.value = v))
watch(open, v => emit('update:modelValue', v))

function close() {
  emit('update:modelValue', false)
}
</script>

<style scoped>
.v-card-text strong {
  display: inline-block;
  width: 100px;
  color: var(--v-theme-on-surface);
}
</style>
