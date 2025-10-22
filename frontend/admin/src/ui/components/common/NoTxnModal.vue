# /ui/components/common/NoTxnModal.vue
<template>
  <v-dialog v-model="openLocal" max-width="640">
    <v-card>
      <v-card-title class="text-h6">무거래일 표시 (입출금)</v-card-title>
      <v-card-text>
        <div class="d-flex flex-wrap" style="gap: 12px;">
          <v-text-field v-model="bizDate" label="영업일(YYYY-MM-DD)" type="date" />
          <v-text-field v-model="reason" label="사유(옵션)" clearable />
        </div>

        <div class="mt-2 text-body-2">계좌(파트) 선택</div>
        <v-combobox
          v-model="parts"
          :items="suggestions"
          multiple
          chips
          closable-chips
          clearable
          label="예: kb-1234, nh-1234 … (여러 개 선택 가능)"
          density="comfortable"
        />

        <v-alert type="info" variant="tonal" class="mt-3">
          파일 없이 업로드되며, 선택한 계좌에 대해 해당 영업일을 <strong>무거래</strong>로 기록합니다.
        </v-alert>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="close">닫기</v-btn>
        <v-btn color="primary" :loading="loading" @click="apply">무거래 저장</v-btn>
      </v-card-actions>
    </v-card>

    <v-snackbar v-model="snack.show" :timeout="2200">{{ snack.text }}</v-snackbar>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  open: boolean
  businessDate: string
  propertyCode?: string
  suggestions?: string[]
}>()
const emit = defineEmits<{
  (e:'update:open', v:boolean): void
  (e:'done'): void
}>()

const openLocal = ref(props.open)
watch(() => props.open, v => openLocal.value = v)
function close(){ openLocal.value = false; emit('update:open', false) }

const bizDate = ref(props.businessDate)
watch(() => props.businessDate, v => bizDate.value = v)

const parts = ref<string[]>([])
const reason = ref('')
const loading = ref(false)
const snack = ref({ show:false, text:'' })

const suggestions = props.suggestions || []

function authHeaders() {
  const h: Record<string,string> = {}
  // @ts-ignore
  if (import.meta.env.VITE_INTERNAL_TOKEN) {
    // @ts-ignore
    h['X-Internal-Token'] = import.meta.env.VITE_INTERNAL_TOKEN as string
  }
  return h
}

async function postNoTxn(part_key?: string){
  const fd = new FormData()
  fd.append('business_date', bizDate.value)
  fd.append('property_code', props.propertyCode || 'MOP')
  fd.append('no_tx', '1')
  if (part_key) fd.append('part_key', part_key)
  if (reason.value) fd.append('note', reason.value)

  const resp = await fetch('/api/upload/pay_settlement', {
    method: 'POST',
    headers: { ...authHeaders() },
    body: fd,
  })
  if (!resp.ok) throw new Error(await resp.text() || '무거래 저장 실패')
}

async function apply(){
  if (!bizDate.value) { snack.value={show:true,text:'영업일을 입력하세요'}; return }
  try{
    loading.value = true
    // 선택한 계좌가 있으면 각각 처리, 없으면 파트 없이 1건(백엔드가 default 파트 해석)
    if (parts.value.length) {
      for (const p of parts.value) { await postNoTxn((p||'').trim()) }
    } else {
      await postNoTxn()
    }
    snack.value = { show:true, text:'무거래 저장 완료' }
    emit('done'); close()
  }catch(e:any){
    snack.value = { show:true, text:`무거래 저장 실패: ${e?.message || e}` }
  }finally{
    loading.value = false
  }
}
</script>
