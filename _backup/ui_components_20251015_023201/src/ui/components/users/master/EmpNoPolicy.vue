<template>
  <v-card flat>
    <v-card-title class="font-weight-bold">사번 자동 부여 정책</v-card-title>
    <v-card-text>
      <v-text-field v-model="form.prefix" label="Prefix" />
      <v-text-field v-model="form.next_no" label="다음 번호" type="number" />
      <v-text-field v-model="form.format" label="형식 (%03d)" />
    </v-card-text>
    <v-card-actions class="justify-end">
      <v-btn color="primary" variant="flat" :loading="saving" @click="save">저장</v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '@/services/http'
import { useToast } from '@/ui/composables/useToast'
const { success, error } = useToast()

const form = ref({ prefix: 'MOP-', next_no: 1, format: '%03d' })
const saving = ref(false)

async function load() {
  try {
    const r: any = await http.get('/master/empno-policy')
    Object.assign(form.value, r)
  } catch { error('불러오기 실패') }
}

async function save() {
  try {
    saving.value = true
    await http.put('/master/empno-policy', form.value)
    success('저장 완료')
  } catch { error('저장 실패') }
  finally { saving.value = false }
}

onMounted(load)
</script>
