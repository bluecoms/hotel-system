<template>
  <v-card flat>
    <v-card-title class="d-flex justify-space-between align-center">
      <span class="font-weight-bold">사번 정책</span>
      <v-btn color="primary" prepend-icon="mdi-content-save" @click="save">저장</v-btn>
    </v-card-title>
    <v-divider />
    <v-card-text>
      <v-form ref="formRef">
        <v-text-field v-model="policy.prefix" label="사번 접두어" hint="예: EMP → EMP001" persistent-hint />
        <v-text-field v-model.number="policy.start_no" label="시작 번호" type="number" min="1" />
        <v-switch v-model="policy.auto_increment" label="자동 증가 사용" color="primary" />
        <v-textarea v-model="policy.memo" label="비고" rows="2" />
      </v-form>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '@/services/http'
import { useToast } from '@/ui/composables/useToast'
const { success, error } = useToast()

const policy = ref({
  prefix: 'EMP',
  start_no: 1,
  auto_increment: true,
  memo: '',
})

async function load() {
  try {
    const r = await http.get('/master/empno-policy')
    Object.assign(policy.value, r || {})
  } catch {
    /* 최초 빈 데이터 허용 */
  }
}

async function save() {
  try {
    await http.put('/master/empno-policy', policy.value)
    success('정책이 저장되었습니다.')
  } catch {
    error('저장 실패')
  }
}

onMounted(load)
</script>
