<template>
  <v-container class="py-6">
    <h1 class="text-h5 mb-1">Sales Upload — sales_front</h1>
    <div class="text-body-2 text-medium-emphasis mb-4">
      CSV 업로드 (headers: <code>business_date, tag, amount</code>)
    </div>

    <v-card class="pa-4 mb-4">
      <v-row dense>
        <v-col cols="12" md="6">
          <v-file-input
            v-model="file"
            label="CSV 파일"
            accept=".csv,text/csv"
            prepend-icon="mdi-file-delimited"
            variant="outlined"
            :disabled="loading"
          />
        </v-col>

        <v-col cols="12" md="3" class="d-flex align-center">
          <v-switch
            v-model="dryRun"
            inset
            color="primary"
            hide-details
            :disabled="loading"
            :label="`드라이런 ${dryRun ? 'ON' : 'OFF'}`"
          />
        </v-col>

        <v-col cols="12" md="3" class="d-flex align-center">
          <v-btn
            :loading="loading"
            :disabled="!file"
            @click="submit"
            variant="flat"
          >
            {{ dryRun ? '검증(드라이런)' : '업로드' }}
          </v-btn>
        </v-col>
      </v-row>

      <v-alert
        v-if="summary && dryRun && (summary.errors?.length ?? 0) === 0"
        type="success" variant="tonal" class="mt-4"
      >
        드라이런 성공! <b>{{ summary.received }}</b>행 파싱되었습니다.
        <v-btn
          size="small"
          class="ml-3"
          :loading="loadingApply"
          color="primary"
          @click="apply"
        >
          적용(실제 업로드)
        </v-btn>
      </v-alert>

      <v-alert
        v-else-if="summary && dryRun && (summary.errors?.length ?? 0) > 0"
        type="warning" variant="tonal" class="mt-4"
      >
        드라이런 결과: 총 <b>{{ summary.received }}</b>행 / 오류
        <b>{{ summary.errors.length }}</b>건. 오류를 먼저 해결해주세요.
      </v-alert>

      <v-alert
        v-else-if="summary && !dryRun"
        type="success" variant="tonal" class="mt-4"
      >
        업로드 완료: 총 {{ summary.received }} 행 / 실제 반영 {{ summary.inserted }} 행
      </v-alert>
    </v-card>

    <v-card v-if="summary && (summary.errors?.length ?? 0) > 0">
      <v-data-table
        :items="summary.errors"
        :headers="errHeaders"
        :items-per-page="10"
        class="elevation-0"
      >
        <template #item.row="{ item }">{{ item.row }}</template>
        <template #item.message="{ item }">
          <span class="font-mono">{{ item.message }}</span>
        </template>
        <template #no-data>
          <div class="pa-6 text-medium-emphasis">오류 없습니다.</div>
        </template>
      </v-data-table>
    </v-card>

    <v-snackbar v-model="toast.show" timeout="3500">
      {{ toast.message }}
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import http from '@/services/http'

type UploadSummary = {
  dry_run: boolean
  received: number
  inserted: number
  errors: Array<{ row:number; message:string }>
}

const file = ref<File | null>(null)
const dryRun = ref(true)
const loading = ref(false)
const loadingApply = ref(false)
const summary = ref<UploadSummary | null>(null)
const toast = ref({ show:false, message:'' })

const errHeaders = [
  { title: '행번호', key: 'row', width: 100 },
  { title: '메시지', key: 'message' },
]

function showError(e:any, fallback:string) {
  const detail = e?.detail || e?.message || fallback
  toast.value = { show:true, message:String(detail) }
}

async function callUpload(runDry: boolean) {
  if (!file.value) return
  const fd = new FormData()
  fd.append('file', file.value)
  fd.append('dry_run', runDry ? '1' : '0')

  const res = await http.post<UploadSummary>('/upload/sales_front', fd)
  summary.value = res
}

async function submit() {
  summary.value = null
  loading.value = true
  try {
    await callUpload(dryRun.value)
  } catch (e:any) {
    showError(e, dryRun.value ? '드라이런 실패' : '업로드 실패')
  } finally {
    loading.value = false
  }
}

async function apply() {
  // 드라이런이 성공했을 때만 사용자가 누를 수 있음
  loadingApply.value = true
  try {
    await callUpload(false)
    toast.value = { show:true, message:'업로드 완료' }
  } catch (e:any) {
    showError(e, '업로드 실패')
  } finally {
    loadingApply.value = false
  }
}
</script>
