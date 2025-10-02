<template>
  <v-container class="py-6">
    <!-- 헤더 -->
    <v-row class="mb-4" align="center" justify="space-between">
      <v-col cols="auto">
        <h1 class="text-h5">OTA 채널 목록</h1>
        <div class="text-body-2 text-medium-emphasis">
          Phase 2 — 스켈레톤 유지, API 연결(READ 전용)
        </div>
      </v-col>
      <v-col cols="auto">
        <v-btn variant="tonal" :disabled="true">추가(준비중)</v-btn>
      </v-col>
    </v-row>

    <!-- 상태 블록 -->
    <StateBlock
      v-if="loading || error || items.length === 0"
      :loading="loading"
      :error="error"
    />

    <!-- 목록 -->
    <v-card v-else>
      <v-data-table
        :items="items"
        :headers="headers"
        class="elevation-0"
        :items-per-page="10"
        aria-label="OTA 채널 테이블"
      >
        <template #item.code="{ item }">
          <span>{{ item.code }}</span>
        </template>

        <template #item.name="{ item }">
          <span>{{ item.name }}</span>
        </template>

        <template #item.status="{ item }">
          <span>{{ item.status || '-' }}</span>
        </template>
      </v-data-table>
    </v-card>

    <v-snackbar v-model="toast.show" timeout="3500">
      {{ toast.message }}
    </v-snackbar>
  </v-container>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import http from '@/services/http'
import StateBlock from '@/ui/components/StateBlock.vue'

type Channel = { code: string; name: string; status?: string }

const { t } = useI18n()

const headers = [
  { title: '채널 코드', key: 'code' },
  { title: '채널 명', key: 'name' },
  { title: '상태', key: 'status' },
]

const items = ref<Channel[]>([])
const loading = ref(false)
const error = ref(false)
const toast = ref<{ show: boolean; message: string }>({ show: false, message: '' })

async function fetchChannels() {
  loading.value = true
  error.value = false
  try {
    const res: any = await http.get('/ota/channels')
    const body: any = res ?? {}
    const arr = Array.isArray(res) ? res : (Array.isArray(body.items) ? body.items : [])
    items.value = (arr as any[]).map((x) => ({
      code: x.code ?? x.channel_code ?? '',
      name: x.name ?? x.channel_name ?? '',
      status: x.status ?? '',
    }))
  } catch (e:any) {
    items.value = []
    error.value = true
    toast.value = { show: true, message: '채널 목록을 불러오지 못했습니다.' }
  } finally {
    loading.value = false
  }
}

onMounted(fetchChannels)
</script>
