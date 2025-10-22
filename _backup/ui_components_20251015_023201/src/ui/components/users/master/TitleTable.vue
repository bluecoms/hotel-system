<template>
  <v-card flat>
    <v-card-title class="d-flex justify-space-between align-center">
      <span class="font-weight-bold">직책 목록</span>
      <v-btn color="primary" prepend-icon="mdi-plus" @click="add">추가</v-btn>
    </v-card-title>
    <v-divider />
    <v-data-table
      :headers="headers"
      :items="rows"
      :loading="loading"
      density="comfortable"
    />
  </v-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '@/services/http'
import { useToast } from '@/ui/composables/useToast'
const { success, error } = useToast()

const headers = [
  { title: '직책명', key: 'name' },
  { title: '순번', key: 'seq' },
]
const rows = ref<any[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const r: any = await http.get('/master/titles')
    rows.value = r.items || []
  } catch { error('불러오기 실패') }
  finally { loading.value = false }
}

async function add() {
  const name = prompt('직책명을 입력하세요 (예: 과장)')
  if (!name) return
  try {
    await http.post('/master/titles', { name })
    success('추가 완료')
    load()
  } catch { error('등록 실패') }
}

onMounted(load)
</script>

