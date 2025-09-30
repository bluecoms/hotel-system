<template>
  <v-container class="py-6" style="max-width: 980px">
    <div class="d-flex align-center justify-space-between mb-3" style="gap:12px">
      <div>
        <h2 class="text-h5 mb-1">Upload History</h2>
        <div class="text-caption">
          Dataset: <strong>{{ dataset }}</strong> • Date: <strong>{{ bizDate }}</strong> • Property: <strong>{{ property }}</strong>
        </div>
      </div>
      <div class="d-flex align-center" style="gap:8px">
        <v-btn variant="tonal" @click="goCalendar">Open Closing Calendar</v-btn>
        <v-btn color="primary" @click="reload">Reload</v-btn>
      </div>
    </div>

    <v-alert v-if="err" type="warning" class="mb-3">{{ err }}</v-alert>

    <v-card>
      <v-card-title class="d-flex align-center justify-space-between">
        <span>Versions</span>
        <v-chip size="small" :color="data?.exists ? 'green' : 'grey'">{{ data?.exists ? 'Uploaded' : 'Empty' }}</v-chip>
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
            <td>v{{ v.version_no }}</td>
            <td>{{ v.filename }}</td>
            <td>{{ formatBytes(v.size) }}</td>
            <td>{{ v.uploaded_at || 'N/A' }}</td>
          </tr>
          <tr v-if="!(data?.versions?.length)">
            <td colspan="4" class="text-center text-medium-emphasis py-6">No versions</td>
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
  id: number; version_no: number; filename: string; size: number; mime: string;
  stored_path: string; uploaded_at: string | null;
}
type Resp = {
  dataset: string; property_code: string; business_date: string;
  session_id: number | null; versions: Version[]; exists: boolean;
}

const route = useRoute()
const router = useRouter()

const dataset = computed(() => String(route.query.dataset || ''))
const bizDate = computed(() => String(route.query.date || ''))
const property = computed(() => String(route.query.property_code || 'MOP'))

const data = ref<Resp | null>(null)
const err  = ref<string | null>(null)

function formatBytes(n:number){
  if(!n && n !== 0) return 'N/A'
  if(n < 1024) return `${n} B`
  if(n < 1024*1024) return `${(n/1024).toFixed(1)} KB`
  return `${(n/1024/1024).toFixed(1)} MB`
}

async function reload(){
  err.value = null
  if(!dataset.value || !bizDate.value){ err.value = 'query 누락(dataset/date)'; return }
  try{
    const path = `admin/datasets/${encodeURIComponent(dataset.value)}/day?date=${encodeURIComponent(bizDate.value)}&property_code=${encodeURIComponent(property.value)}`
    data.value = await http.get<Resp>(path)
  }catch(e:any){
    err.value = e?.detail ?? e?.message ?? '히스토리 조회 실패'
    data.value = null
  }
}

function goCalendar(){
  const ym = bizDate.value.slice(0,7)
  router.push({ path:'/closing', query:{ month: ym }})
}

onMounted(reload)
</script>
