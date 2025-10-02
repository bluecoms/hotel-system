<template>
  <v-container class="py-6">
    <h1 class="text-h5 mb-1">Audit Logs</h1>
    <div class="text-body-2 text-medium-emphasis mb-4">
      최신 로그 먼저 표시됩니다.
    </div>

    <v-card class="pa-3 mb-3">
      <v-row dense>
        <v-col cols="12" md="3">
          <v-text-field
            v-model.number="limit"
            type="number"
            label="Limit"
            min="1"
            density="comfortable"
          />
        </v-col>
        <v-col cols="12" md="3">
          <v-text-field
            v-model.number="offset"
            type="number"
            label="Offset"
            min="0"
            density="comfortable"
          />
        </v-col>
        <v-col cols="12" md="3" class="d-flex align-center">
          <v-btn :loading="loading" @click="load" variant="flat">조회</v-btn>
        </v-col>
      </v-row>
    </v-card>

    <v-progress-linear v-if="loading" indeterminate class="mb-3" />

    <v-card>
      <v-data-table
        :items="rows"
        :headers="headers"
        :items-per-page="10"
        class="elevation-0"
      >
        <template #item.meta_json="{ item }">
          <span class="font-mono text-caption">{{ shortMeta(item.meta_json) }}</span>
        </template>
        <template #no-data>
          <div class="pa-6 text-medium-emphasis">표시할 로그 없음</div>
        </template>
      </v-data-table>
    </v-card>

    <v-snackbar v-model="toast.show" timeout="3000">
      {{ toast.message }}
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '@/services/http'

type Row = { id:number; ts:string; actor:string; action:string; target:string; meta_json?:string }

const rows = ref<Row[]>([])
const limit = ref<number>(10)
const offset = ref<number>(0)
const loading = ref(false)
const toast = ref({ show:false, message:'' })

const headers = [
  { title: 'ts', key: 'ts', width: 180 },
  { title: 'actor', key: 'actor', width: 160 },
  { title: 'action', key: 'action', width: 220 },
  { title: 'target', key: 'target' },
  { title: 'meta', key: 'meta_json' },
]

const shortMeta = (m?:string) => {
  if (!m) return ''
  return m.length > 140 ? (m.slice(0, 140) + '…') : m
}

async function load() {
  loading.value = true
  try {
    const q = http.qs({ limit: limit.value, offset: offset.value })
    const res = await http.get<Row[]>(`/audit/logs${q}`)
    rows.value = res ?? []
  } catch (e:any) {
    toast.value = { show:true, message:'로그를 불러올 수 없습니다.' }
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
