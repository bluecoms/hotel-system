<template>
  <v-container fluid class="page-shell py-6">
    <div class="bar mb-6">
      <div class="bar-left">
        <v-icon color="primary" icon="mdi-history" size="22" />
        <h2 class="text-h6 font-weight-bold">마감 히스토리</h2>
        <span class="text-muted text-body-2">
          업로드 버전 및 파일 이력 조회
        </span>
      </div>
      <div class="bar-right">
        <v-btn variant="tonal" prepend-icon="mdi-calendar" @click="goCalendar">
          마감 달력 열기
        </v-btn>
        <v-btn color="primary" prepend-icon="mdi-refresh" @click="reload">
          새로고침
        </v-btn>
      </div>
    </div>

    <v-alert type="info" variant="tonal" class="mb-4">
      Dataset: <strong>{{ dataset }}</strong> |
      Date: <strong>{{ bizDate }}</strong> |
      Property: <strong>{{ property }}</strong>
    </v-alert>

    <v-alert v-if="err" type="warning" class="mb-4">{{ err }}</v-alert>

    <v-card class="brand-panel">
      <v-card-title class="d-flex align-center justify-space-between">
        <div class="font-weight-bold">업로드 버전 이력</div>
        <v-chip
          size="small"
          :color="data?.exists ? 'green' : 'grey'"
          :text-color="data?.exists ? 'white' : 'black'"
          label
        >
          {{ data?.exists ? 'Uploaded' : 'Empty' }}
        </v-chip>
      </v-card-title>

      <v-divider />

      <v-table density="comfortable">
        <thead>
          <tr>
            <th style="width:90px">Version</th>
            <th>Filename</th>
            <th style="width:140px">Size</th>
            <th style="width:220px">UploadedAt (UTC)</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="v in data?.versions ?? []" :key="v.id">
            <td class="font-weight-medium">v{{ v.version_no }}</td>
            <td>{{ v.filename }}</td>
            <td>{{ formatBytes(v.size) }}</td>
            <td>{{ v.uploaded_at || 'N/A' }}</td>
          </tr>
          <tr v-if="!(data?.versions?.length)">
            <td colspan="4" class="text-center text-medium-emphasis py-6">
              No versions
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import http from '@/services/http'

type Version = {
  id: number
  version_no: number
  filename: string
  size: number
  mime: string
  stored_path: string
  uploaded_at: string | null
}
type Resp = {
  dataset: string
  property_code: string
  business_date: string
  session_id: number | null
  versions: Version[]
  exists: boolean
}

const route = useRoute()
const router = useRouter()

const dataset = computed(() => String(route.query.dataset || ''))
const bizDate = computed(() => String(route.query.date || ''))
const property = computed(() => String(route.query.property_code || 'MOP'))

const data = ref<Resp | null>(null)
const err = ref<string | null>(null)

function formatBytes(n: number) {
  if (!n && n !== 0) return 'N/A'
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / 1024 / 1024).toFixed(1)} MB`
}

async function reload() {
  err.value = null
  if (!dataset.value || !bizDate.value) {
    err.value = '쿼리 누락(dataset/date)'
    return
  }
  try {
    const path = `/api/admin/datasets/${encodeURIComponent(dataset.value)}/day?date=${encodeURIComponent(
      bizDate.value
    )}&property_code=${encodeURIComponent(property.value)}`
    data.value = await http.get<Resp>(path)
  } catch (e: any) {
    err.value = e?.detail ?? e?.message ?? '히스토리 조회 실패'
    data.value = null
  }
}

function goCalendar() {
  const ym = bizDate.value.slice(0, 7)
  router.push({ path: '/closing', query: { month: ym } })
}

onMounted(reload)
</script>

<style scoped src="@/styles/toolbar.scss"></style>

<style scoped>
.page-shell {
  max-width: 1280px;
  margin: 0 auto;
}

.brand-panel {
  background: rgb(var(--v-theme-surface));
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(16, 24, 40, 0.06);
  padding: 12px 16px;
}

:deep(.v-table th) {
  font-weight: 600;
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-line);
  color: var(--color-muted);
}
</style>
