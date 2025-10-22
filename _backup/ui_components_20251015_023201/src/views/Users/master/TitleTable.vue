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
    >
      <template #item.actions="{ item }">
        <v-btn icon="mdi-delete" color="error" variant="text" size="small" @click="remove(item)" />
      </template>
    </v-data-table>
  </v-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '@/services/http'
import { useToast } from '@/ui/composables/useToast'
const { success, error } = useToast()

const headers = [
  { title: '코드', key: 'code' },
  { title: '직책명', key: 'name' },
  { title: '', key: 'actions', sortable: false },
]
const rows = ref<any[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    rows.value = await http.get('/master/titles')
  } catch {
    error('불러오기 실패')
  } finally {
    loading.value = false
  }
}

async function add() {
  const name = prompt('새 직책명을 입력하세요 (예: 과장)')
  if (!name) return
  try {
    await http.post('/master/titles', { name })
    success('등록 완료')
    await load()
  } catch {
    error('등록 실패')
  }
}

async function remove(item: any) {
  if (!confirm(`${item.name} 직책을 삭제하시겠습니까?`)) return
  try {
    await http.delete(`/master/titles/${item.id}`)
    success('삭제 완료')
    await load()
  } catch {
    error('삭제 실패')
  }
}

onMounted(load)
</script>
