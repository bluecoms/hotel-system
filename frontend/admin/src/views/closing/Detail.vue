<template>
  <v-container class="py-6">
    <div class="d-flex align-center justify-space-between mb-4" style="gap:12px">
      <h2 class="text-h5">Closing</h2>
      <div class="d-flex align-center" style="gap:8px">
        <v-btn variant="text" @click="shift(-1)">◀</v-btn>
        <v-text-field v-model="month" label="Month (YYYY-MM)" density="comfortable" style="max-width:140px" />
        <v-btn color="primary" @click="load">LOAD</v-btn>
        <v-btn variant="text" @click="shift(1)">▶</v-btn>
      </div>
    </div>

    <v-alert v-if="err" type="warning" class="mb-4">{{ err }}</v-alert>

    <v-table density="comfortable">
      <thead>
        <tr>
          <th style="width:110px">Date</th>
          <th>Uploaded datasets (versions)</th>
          <th style="width:120px" class="text-right">Progress</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="d in days" :key="d.date">
          <td>{{ d.date }}</td>
          <td>
            <v-chip
              v-for="ds in required"
              :key="ds"
              class="ma-1"
              :color="d.uploaded.includes(ds) ? 'green' : undefined"
              variant="outlined"
              size="small"
              label
            >
              {{ label(ds) }}
              <span v-if="d.counts?.[ds]" class="ml-1">v{{ d.counts[ds] }}</span>
            </v-chip>
          </td>
          <td class="text-right">
            <v-progress-linear :model-value="d.total ? Math.round(d.done * 100 / d.total) : 0" height="10" rounded/>
          </td>
        </tr>
        <tr v-if="!days.length">
          <td colspan="3" class="text-center text-medium-emphasis py-6">No data</td>
        </tr>
      </tbody>
    </v-table>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '@/services/http'

type DayRow = {
  date: string
  uploaded: string[]
  counts: Record<string, number>
  done: number
  total: number
  complete: boolean
}

const month = ref(new Date().toISOString().slice(0,7)) // YYYY-MM
const days  = ref<DayRow[]>([])
const required = ref<string[]>([])
const err = ref<string | null>(null)

const labels: Record<string,string> = {
  rooms_status: 'Rooms',
  sales_front:  'Front',
  fnb_sales:    'F&B',
  expenses:     'Expenses',
  pay_settlement:'Settlement',
}
const label = (k:string) => labels[k] ?? k

function shift(delta:number){
  const [y,m] = month.value.split('-').map(n=>+n)
  const d = new Date(y, m-1+delta, 1)
  month.value = d.toISOString().slice(0,7)
  load()
}

async function load(){
  err.value = null
  try{
    const data = await http.get<{from:string;to:string;required:string[];days:DayRow[]}>(
      `closing/calendar?month=${encodeURIComponent(month.value)}&property_code=MOP`
    )
    days.value = data?.days ?? []
    required.value = data?.required ?? []
  }catch{
    err.value = '캘린더 로드 실패'
    days.value = []
    required.value = []
  }
}

onMounted(load)
</script>
