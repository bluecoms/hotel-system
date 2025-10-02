<template>
  <v-container class="py-6">
    <h1 class="text-h5 mb-1">OTA 커미션</h1>
    <div class="text-body-2 text-medium-emphasis mb-4">
      Phase 3 — 스켈레톤 유지, API 연결(READ/CREATE/UPDATE/DELETE)
    </div>

    <v-row class="mb-3" align="center" dense>
      <v-col cols="12" md="3">
        <v-text-field v-model="channel" label="채널 코드(BKG 등)" density="comfortable" />
      </v-col>
      <v-col cols="12" md="3">
        <v-text-field v-model="dateFrom" label="From (YYYY-MM-DD)" density="comfortable" />
      </v-col>
      <v-col cols="12" md="3">
        <v-text-field v-model="dateTo" label="To (YYYY-MM-DD)" density="comfortable" />
      </v-col>
      <v-col cols="12" md="3" class="d-flex gap-2">
        <v-btn @click="refresh" :loading="loading" variant="flat">조회</v-btn>
        <v-btn color="primary" @click="openNew" variant="flat">{{ t('cta.new') }}</v-btn>
      </v-col>
    </v-row>

    <!-- 상태 블록 -->
    <StateBlock v-if="loading || rows.length === 0 || listError"
      :loading="loading"
      :error="listError" />

    <!-- 목록 -->
    <v-card v-if="!loading && !listError && rows.length > 0">
      <v-data-table
        :items="rows"
        :headers="headers"
        class="elevation-0"
        :items-per-page="10"
        aria-label="커미션 테이블"
      >
        <template #item.actions="{ item }">
          <v-btn size="small" variant="text" @click="openEdit(item)">{{ t('cta.update') }}</v-btn>
          <v-tooltip :text="`${t('cta.delete')}는 추후 지원 예정입니다.`">
            <template #activator="{ props }">
              <span v-bind="props">
                <v-btn size="small" variant="text" color="error" :disabled="true">{{ t('cta.delete') }}</v-btn>
              </span>
            </template>
          </v-tooltip>
        </template>

        <template #no-data>
          <div class="pa-6 text-medium-emphasis">{{ t('state.empty') }}</div>
        </template>
      </v-data-table>
    </v-card>

    <!-- 편집/신규 다이얼로그 -->
    <v-dialog v-model="dialog" max-width="560"
      @keydown.esc="closeDialog"
      @keydown.enter.stop.prevent="save">
      <v-card>
        <v-card-title>{{ editItem?.id ? '커미션 수정' : '커미션 생성' }}</v-card-title>
        <v-card-text class="d-flex flex-column ga-3">
          <v-text-field v-model="form.channel" label="채널 코드" />
          <v-text-field v-model="form.valid_from" label="유효 시작(YYYY-MM-DD)" />
          <v-text-field v-model="form.valid_to" label="유효 종료(YYYY-MM-DD)" />
          <v-text-field v-model.number="form.rate" label="커미션(%) 0~100" type="number" />
          <v-text-field v-model="form.note" label="비고" />
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn variant="text" @click="closeDialog">취소</v-btn>
          <v-btn color="primary" variant="flat" :loading="saving" :disabled="saving" @click="save">
            {{ editItem?.id ? t('cta.update') : t('cta.save') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 에러/안내 토스트 1종 -->
    <v-snackbar v-model="toast.show" timeout="3500">{{ toast.message }}</v-snackbar>
  </v-container>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import http from '@/services/http'
import StateBlock from '@/ui/components/StateBlock.vue'

type Commission = {
  id?: number
  channel: string
  valid_from: string
  valid_to: string
  rate: number
  note?: string
}

const { t } = useI18n()

const headers: { title: string; key: string; sortable?: boolean }[] = [
  { title: '채널', key: 'channel' },
  { title: '숙박일자(From)', key: 'valid_from' },
  { title: '숙박일자(To)', key: 'valid_to' },
  { title: '커미션(%)', key: 'rate' },
  { title: '비고', key: 'note' },
  { title: '작업', key: 'actions', sortable: false },
]

const channel = ref<string>('')
const dateFrom = ref<string>('')
const dateTo = ref<string>('')
const rows = ref<Commission[]>([])
const loading = ref(false)
const listError = ref(false)
const saving  = ref(false)
const toast = ref<{show:boolean; message:string}>({ show:false, message:'' })

const dialog = ref(false)
const editItem = ref<Commission | null>(null)
const form = ref<Commission>({ channel:'', valid_from:'', valid_to:'', rate:0, note:'' })

// === list / create / update / delete ===
const list = async (channelCode: string, from?: string, to?: string) => {
  const q = new URLSearchParams()
  if (channelCode) q.set('channel', channelCode)
  if (from) q.set('date_from', from)
  if (to) q.set('date_to', to)
  const res: any = await http.get(`/ota/commissions?${q}`)
  return Array.isArray(res) ? res : (Array.isArray(res?.items) ? res.items : [])
}

const create = (p: any) => http.post('/ota/commissions', p)
const update = (id: number, p: any) => http.put(`/ota/commissions/${id}`, p)
const remove = (id: number) => http.delete(`/ota/commissions/${id}`) // BE에 DELETE 없으면 405

// === validation & flows ===
function validate(p: Commission): string | null {
  const r = Number(p.rate ?? 0)
  if (isNaN(r) || r < 0 || r > 100) return 'rate는 0~100 사이여야 합니다.'
  if (!p.valid_from || !p.valid_to) return '기간(From/To)을 입력하세요.'
  if (p.valid_from > p.valid_to) return '기간이 역전되었습니다.'
  if (!p.channel) return '채널을 선택하세요.'
  return null
}

function overlaps(aFrom: string, aTo: string, bFrom: string, bTo: string) {
  return (aFrom <= bTo) && (bFrom <= aTo)
}
function precheckOverlap(p: Commission): string | null {
  const same = rows.value.filter(r => r.channel === p.channel && (editItem.value?.id ? r.id !== editItem.value.id : true))
  const hit = same.find(r => overlaps(p.valid_from, p.valid_to, r.valid_from, r.valid_to))
  return hit ? `기간 겹침: ${hit.valid_from} ~ ${hit.valid_to}` : null
}

async function refresh() {
  loading.value = true
  listError.value = false
  try {
    rows.value = await list(channel.value, dateFrom.value, dateTo.value)
  } catch {
    rows.value = []
    listError.value = true
    toast.value = { show: true, message: '커미션 목록을 불러오지 못했습니다.' }
  } finally {
    loading.value = false
  }
}

function openNew() {
  editItem.value = null
  form.value = {
    channel: channel.value || '',
    valid_from: dateFrom.value || '',
    valid_to: dateTo.value || '',
    rate: 0,
    note: ''
  }
  dialog.value = true
}

function openEdit(item: Commission) {
  editItem.value = item
  form.value = { ...item }
  dialog.value = true
}

function closeDialog() {
  dialog.value = false
  form.value = { channel:'', valid_from:'', valid_to:'', rate:0, note:'' }
  editItem.value = null
  saving.value = false
}

async function save() {
  let msg = validate(form.value)
  if (msg) { toast.value = { show:true, message: msg }; return }

  msg = precheckOverlap(form.value)
  if (msg) { toast.value = { show:true, message: msg }; return }

  if (saving.value) return
  saving.value = true
  try {
    if (editItem.value?.id) {
      await update(editItem.value.id, form.value)
      toast.value = { show:true, message:'저장되었습니다.' }
    } else {
      await create(form.value)
      toast.value = { show:true, message:'생성되었습니다.' }
    }
    dialog.value = false
    await refresh()
  } catch (e:any) {
    const status = e?.status ?? e?.response?.status
    const detail = e?.message ?? e?.detail ?? e?.response?.data?.detail ?? ''
    if (status === 409) {
      toast.value = { show: true, message: detail || 'Overlapping period for the channel' }
    } else if (status === 400 || status === 422) {
      toast.value = { show: true, message: detail || '요청 값이 올바르지 않습니다.' }
    } else {
      toast.value = { show: true, message: (detail || '저장에 실패했습니다.') }
    }
  } finally {
    saving.value = false
  }
}

async function removeOne(item: Commission) {
  if (!item.id) return
  try {
    await remove(item.id) // BE에서 405면 FE 토스트만
    toast.value = { show:true, message:'삭제되었습니다.' }
    await refresh()
  } catch {
    toast.value = { show:true, message:'삭제에 실패했습니다.' }
  }
}

onMounted(refresh)
</script>
