<template>
  <v-container fluid class="py-6" style="max-width:1280px">
    <div class="bar brand-panel d-flex align-center justify-space-between mb-5">
      <div class="d-flex align-center gap10 flex-wrap">
        <v-breadcrumbs :items="crumbs" class="pa-0 ma-0" />
        <v-divider vertical class="mx-2" />
        <h2 class="text-h6 font-weight-bold">병합 배치 이력</h2>
      </div>
      <v-btn color="primary" :loading="loading" @click="load">새로고침</v-btn>
    </div>

    <v-card class="brand-panel pa-4 mb-4">
      <div class="d-flex align-center flex-wrap gap12">
        <v-text-field
          v-model="dataset"
          label="Dataset (예: sales_front)"
          variant="outlined"
          density="comfortable"
          hide-details
          clearable
          class="flex-grow-1"
          @keyup.enter="load"
        />
        <v-text-field
          v-model="propertyCode"
          label="Property Code"
          variant="outlined"
          density="comfortable"
          hide-details
          clearable
          style="width:160px"
          @keyup.enter="load"
        />
        <v-btn color="primary" :loading="loading" @click="load">조회</v-btn>
      </div>
    </v-card>

    <v-data-table
      :headers="headers"
      :items="batches"
      :loading="loading"
      density="compact"
      class="brand-panel elevation-0"
      hover
      item-value="id"
    >
      <template #item.status="{ item }">
        <v-chip
          :color="item.status==='DONE' ? 'success' : (item.status==='RUNNING' ? 'warning' : 'grey')"
          size="small"
          label
          variant="flat"
        >
          {{ item.status }}
        </v-chip>
      </template>

      <template #item.actions="{ item }">
        <v-btn
          size="small"
          variant="text"
          color="primary"
          prepend-icon="mdi-file-document-outline"
          @click="openLogs(item)"
        >
          로그
        </v-btn>
      </template>

      <template #no-data>
        <v-alert type="info" variant="tonal" border="start" class="ma-3">
          데이터 없음
        </v-alert>
      </template>
    </v-data-table>

    <v-dialog v-model="showLogs" max-width="900px">
      <v-card>
        <v-card-title class="d-flex justify-space-between align-center">
          <div>
            <strong>배치 #{{ currentBatch?.id }}</strong> — {{ currentBatch?.dataset }}
          </div>
          <v-btn icon="mdi-close" variant="text" @click="showLogs=false" />
        </v-card-title>

        <v-divider />

        <v-card-text>
          <v-expansion-panels v-if="logs.length">
            <v-expansion-panel v-for="(log,i) in logs" :key="i">
              <v-expansion-panel-title>
                <v-icon size="small" class="mr-2">mdi-clipboard-text-outline</v-icon>
                {{ log.action }} — {{ log.business_date }}
                <v-spacer />
                <code class="text-caption text-grey">{{ log.key_hash }}</code>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <pre class="json-block">{{ pretty(log) }}</pre>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
          <v-alert v-else type="info" variant="tonal" border="start">로그 없음</v-alert>
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { getMergeBatches, getMergeLogs } from '@/services/merge'

interface MergeBatch {
  id: number
  dataset: string
  property_code: string
  business_date: string
  record_count: number
  status: string
  mode: string
  created_at: string
}
interface MergeLog {
  business_date: string
  action: string
  key_hash: string
  reason?: string
  [key: string]: any
}

const crumbs = [
  { title: '마감 관리', disabled: true },
  { title: '병합 이력', disabled: true },
]

const dataset = ref('')
const propertyCode = ref('MOP')
const loading = ref(false)
const batches = ref<MergeBatch[]>([])
const showLogs = ref(false)
const currentBatch = ref<MergeBatch | null>(null)
const logs = ref<MergeLog[]>([])

const headers = [
  { text: 'ID', value: 'id', width: 60 },
  { text: 'Dataset', value: 'dataset' },
  { text: 'Property', value: 'property_code' },
  { text: 'Business Date', value: 'business_date' },
  { text: 'Records', value: 'record_count', align: 'end' },
  { text: 'Status', value: 'status' },
  { text: 'Mode', value: 'mode' },
  { text: 'Created', value: 'created_at' },
  { text: 'Actions', value: 'actions', sortable: false },
]

/** ✅ 병합 배치 목록 로드 */
async function load() {
  loading.value = true
  try {
    const res = await getMergeBatches({
      dataset: dataset.value || undefined,
      property_code: propertyCode.value || undefined,
      order: 'desc',
      limit: 50,
    })
    batches.value = Array.isArray(res) ? res : []
  } catch (e) {
    console.error(e)
    batches.value = []
  } finally {
    loading.value = false
  }
}

/** ✅ 로그 조회 */
async function openLogs(item: MergeBatch) {
  try {
    const res = await getMergeLogs(item.id)
    currentBatch.value = item
    logs.value = Array.isArray((res as any)?.changes)
      ? (res as any).changes
      : []
    showLogs.value = true
  } catch (e) {
    logs.value = []
    showLogs.value = true
  }
}

/** ✅ JSON 포매터 */
function pretty(obj: any) {
  return JSON.stringify(obj, null, 2)
}

load()
</script>

<style scoped>
.brand-panel {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(16, 24, 40, 0.06);
}

.json-block {
  background: #f9fafb;
  padding: 12px;
  border-radius: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  white-space: pre-wrap;
  overflow-x: auto;
  border: 1px solid #e5e7eb;
}
</style>
