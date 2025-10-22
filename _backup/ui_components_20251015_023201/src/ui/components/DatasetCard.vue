<!-- src/components/closing/DatasetCard.vue -->
<template>
  <v-card class="dataset-card mb-6">
    <v-card-title class="card-header">
      <div class="header-left">
        <v-icon :icon="safeIcon" color="primary" size="22" />
        <span class="title-text">{{ label }}</span>
      </div>
      <div class="header-right">
        <div class="dryrun-wrap">
          <v-switch v-model="localDryRun" color="primary" inset hide-details class="toggle-strong" />
          <v-chip
            :color="localDryRun ? 'primary' : 'grey-lighten-2'"
            :text-color="localDryRun ? 'white' : undefined"
            label
            size="small"
          >
            {{ localDryRun ? '드라이런: 켜짐 (검증만)' : '드라이런: 꺼짐 (적용)' }}
          </v-chip>
        </div>
        <v-select
          v-model="selectedVersion"
          :items="versionItems"
          item-title="label"
          item-value="value"
          class="ver-select"
          variant="outlined"
          density="comfortable"
          hide-details
        />
        <v-chip v-if="version > 0" size="x-small" color="grey" label>v{{ version }}</v-chip>
      </div>
    </v-card-title>

    <v-divider class="card-sep" />

    <v-card-text class="card-body">
      <div v-if="showPartition" class="part-block">
        <label class="part-label">파티션</label>

        <v-chip-group
          v-if="dataset==='fnb_sales'"
          v-model="downloadPart"
          column
          class="part-chips"
        >
          <v-chip
            v-for="p in fnbParts"
            :key="p"
            :value="p"
            label
            filter
            variant="tonal"
            class="part-chip"
          >
            <span class="ellipsis">{{ p==='pay' ? '결제수단별' : '상품별' }}</span>
          </v-chip>
        </v-chip-group>

        <v-chip-group
          v-else-if="dataset==='bank_ledger'"
          v-model="bankPart"
          column
          class="part-chips"
        >
          <v-chip
            v-for="acc in bankParts"
            :key="acc"
            :value="acc"
            label
            filter
            variant="tonal"
            class="part-chip"
          >
            <span class="ellipsis">{{ acc }}</span>
          </v-chip>
        </v-chip-group>
      </div>

      <template v-if="dataset==='fnb_sales'">
        <div class="dz-grid">
          <div class="dz-card" @dragover.prevent @drop.prevent="onDropTo('fnb1',$event)">
            <div class="dz-line">
              <v-icon icon="mdi-tray-arrow-up" size="20" class="mr-2" />
              ① 결제수단별 매출 파일 드래그
            </div>
            <v-btn variant="tonal" size="small" class="dz-btn" @click="openPick('fnb1')">파일 선택</v-btn>
            <input ref="fnb1El" type="file" accept=".csv,.xlsx" class="hidden" @change="pickTo('fnb1',$event)" />
          </div>

          <div class="dz-card" @dragover.prevent @drop.prevent="onDropTo('fnb2',$event)">
            <div class="dz-line">
              <v-icon icon="mdi-tray-arrow-up" size="20" class="mr-2" />
              ② 상품별 매출현황 파일 드래그
            </div>
            <v-btn variant="tonal" size="small" class="dz-btn" @click="openPick('fnb2')">파일 선택</v-btn>
            <input ref="fnb2El" type="file" accept=".csv,.xlsx" class="hidden" @change="pickTo('fnb2',$event)" />
          </div>
        </div>
      </template>

      <template v-else-if="dataset==='bank_ledger'">
        <div class="dz-card single" @dragover.prevent @drop.prevent="onDropTo('bank',$event)">
          <div class="dz-line">
            <v-icon icon="mdi-tray-arrow-up" size="20" class="mr-2" />
            은행 입출금(CSV) 파일을 드래그 앤 드롭
          </div>
          <v-btn variant="tonal" size="small" class="dz-btn" @click="openPick('bank')">파일 선택</v-btn>
          <input ref="bankEl" type="file" accept=".csv" class="hidden" @change="pickTo('bank',$event)" />
        </div>
      </template>

      <template v-else>
        <div class="dz-card single" @dragover.prevent @drop.prevent="onDropTo('general',$event)">
          <div class="dz-line">
            <v-icon icon="mdi-tray-arrow-up" size="20" class="mr-2" />
            파일을 드래그 앤 드롭하세요
          </div>
          <v-btn variant="tonal" size="small" class="dz-btn" @click="openPick('general')">파일 선택</v-btn>
          <input ref="generalEl" type="file" accept=".csv,.xlsx" class="hidden" @change="pickTo('general',$event)" />
        </div>
      </template>

      <v-alert
        v-if="dayStatus==='CLOSED'"
        type="warning"
        density="comfortable"
        variant="tonal"
        class="mt-3"
      >
        마감 상태에서는 업로드가 차단됩니다. 날짜를 변경하거나 재오픈한 뒤 다시 시도하세요.
      </v-alert>
    </v-card-text>

    <v-divider />

    <v-card-actions class="card-footer">
      <v-spacer />
      <v-menu location="bottom end">
        <template #activator="{ props:menu }">
          <v-btn v-bind="menu" class="btn-same" variant="tonal" prepend-icon="mdi-download">다운로드</v-btn>
        </template>
        <v-list density="comfortable">
          <v-list-item :href="rawHref" target="_blank" rel="noopener" prepend-icon="mdi-file-download-outline">
            원본 다운로드
          </v-list-item>
          <v-list-item :href="canonHref" target="_blank" rel="noopener" prepend-icon="mdi-table-arrow-down">
            정규화 CSV 다운로드
          </v-list-item>
        </v-list>
      </v-menu>

      <v-btn
        class="btn-same"
        color="primary"
        variant="flat"
        :disabled="!canUpload || dayStatus==='CLOSED'"
        :loading="loading"
        prepend-icon="mdi-upload"
        @click="onUpload"
      >
        업로드
      </v-btn>

      <v-btn
        class="btn-same"
        variant="tonal"
        prepend-icon="mdi-history"
        :disabled="!history.length"
        @click="openHistory"
      >
        이력 보기
      </v-btn>
    </v-card-actions>

    <v-dialog v-model="dlgHistory" max-width="720">
      <v-card>
        <v-card-title class="d-flex align-center gap8">
          <v-icon icon="mdi-history" /> {{ label }} 이력
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-table density="comfortable">
            <thead>
              <tr><th>Ver</th><th>Part</th><th>Filename</th><th>Size</th><th>Date</th></tr>
            </thead>
            <tbody>
              <tr v-for="h in history" :key="h.version_no + ':' + (h.part_key||'')">
                <td>v{{ h.version_no }}</td>
                <td>{{ h.part_key || '-' }}</td>
                <td>{{ h.filename }}</td>
                <td>{{ fmtSize(h.size) }}</td>
                <td>{{ h.uploaded_at || '-' }}</td>
              </tr>
              <tr v-if="!history.length">
                <td colspan="5" class="text-center text-medium-emphasis py-6">업로드 이력이 없습니다.</td>
              </tr>
            </tbody>
          </v-table>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="dlgHistory=false">닫기</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import http from '@/services/http'
import { useToast } from '@/ui/composables/useToast'

const props = defineProps({
  dataset: { type: String, required: true },
  label: { type: String, required: true },
  bizDate: { type: String, required: true },
  propertyCode: { type: String, required: true },
  dayStatus: { type: String, required: true },
  globalDryRun: { type: Boolean, default: false },
  dryRun: { type: Object, default: () => ({}) },
  bankParts: { type: Array, default: () => [] }
})

const emit = defineEmits(['refresh'])
const { success, error, info } = useToast()

const loading = ref(false)
const file = ref<File|null>(null)
const fnbFile1 = ref<File|null>(null)
const fnbFile2 = ref<File|null>(null)
const localDryRun = ref(true)

const version = ref(0)
const selectedVersion = ref<number|undefined>(undefined)
const versionItems = ref([{label:'latest', value: undefined}])
const dlgHistory = ref(false)
const history = ref<any[]>([])

const fnbParts = ['pay','items'] as const
const downloadPart = ref<''|'pay'|'items'>('')
const bankPart = ref<string>('')
const bankParts = computed(()=> props.bankParts ?? [])

const showPartition = computed(()=>{
  if (props.dataset==='fnb_sales') return true
  if (props.dataset==='bank_ledger') return bankParts.value.length > 1
  return false
})

watch(bankParts, (list)=>{
  if (props.dataset==='bank_ledger' && list.length===1) bankPart.value = String(list[0])
}, { immediate:true })

const safeIcon = computed(()=>({
  sales_front:'mdi-cash-register',
  rooms_status:'mdi-bed-outline',
  fnb_sales:'mdi-silverware-fork-knife',
  expenses:'mdi-receipt-text-outline',
  pay_settlement:'mdi-credit-card-outline',
  bank_ledger:'mdi-bank-transfer',
  reservations:'mdi-calendar-check'
}[props.dataset] || 'mdi-file-upload'))

const canUpload = computed(()=>{
  if (props.dayStatus==='CLOSED') return false
  if (props.dataset==='fnb_sales') return !!(fnbFile1.value && fnbFile2.value)
  return !!file.value
})

watch(() => localDryRun.value, v => { props.dryRun[props.dataset] = v })

function fmtSize(n:number){
  if(!n) return '-'
  if(n<1024) return `${n}B`
  if(n<1024*1024) return `${(n/1024).toFixed(1)}KB`
  return `${(n/1024/1024).toFixed(1)}MB`
}

const rawHref = computed(()=>{
  const q = new URLSearchParams({ dataset: props.dataset, business_date: props.bizDate, property_code: props.propertyCode })
  if (selectedVersion.value) q.set('version_no', String(selectedVersion.value))
  return `/api/upload/file?${q.toString()}`
})
const canonHref = computed(()=>{
  const q = new URLSearchParams({ dataset: props.dataset, business_date: props.bizDate, property_code: props.propertyCode })
  if (selectedVersion.value) q.set('version_no', String(selectedVersion.value))
  return `/api/upload/canon?${q.toString()}`
})

const fnb1El = ref<HTMLInputElement|null>(null)
const fnb2El = ref<HTMLInputElement|null>(null)
const bankEl = ref<HTMLInputElement|null>(null)
const generalEl = ref<HTMLInputElement|null>(null)

function openPick(which:'fnb1'|'fnb2'|'bank'|'general'){
  const map = { fnb1: fnb1El.value, fnb2: fnb2El.value, bank: bankEl.value, general: generalEl.value }
  map[which]?.click()
}

async function onUpload(){
  if (props.dayStatus==='CLOSED'){ error('마감 상태입니다. 재오픈 후 다시 시도하세요.'); return }
  const fd = new FormData()
  fd.append('property_code', props.propertyCode)
  fd.append('dry_run', (localDryRun.value && props.globalDryRun) ? '1':'0')

  try{
    loading.value = true
    fd.append('business_date', props.bizDate)
    if (props.dataset==='fnb_sales'){
      if (!fnbFile1.value || !fnbFile2.value) return error('두 파일을 모두 선택하세요.')
      fd.append('file_pay', fnbFile1.value)
      fd.append('file_items', fnbFile2.value)
    }else{
      if (!file.value) return error('파일을 선택하세요.')
      fd.append('file', file.value)
    }
    const res:any = await http.post(`/upload/${props.dataset}`, fd)
    if (res?.dry_run) info(`드라이런: ${res?.counts?.rows ?? res?.received ?? 0}건`)
    else { success(`${props.label} 업로드 완료`); emit('refresh'); await fetchVersions() }
  }catch(e:any){
    error(e?.detail ?? e?.message ?? '업로드 실패')
  }finally{ loading.value=false }
}

function onDropTo(target:'general'|'bank'|'fnb1'|'fnb2', ev:DragEvent){
  const f = ev.dataTransfer?.files?.[0]; if (!f) return
  if (target==='fnb1') fnbFile1.value=f
  else if (target==='fnb2') fnbFile2.value=f
  else file.value=f
}
function pickTo(target:'general'|'bank'|'fnb1'|'fnb2', ev:Event){
  const input=ev.target as HTMLInputElement
  const f=input.files?.[0]; if(!f)return
  onDropTo(target,{dataTransfer:{files:[f]}} as any)
}

/* 버전/이력 */
async function fetchVersions(){
  try{
    const r:any = await http.get(`/upload/versions?dataset=${props.dataset}&business_date=${props.bizDate}&property_code=${props.propertyCode}`)
    history.value = r?.items ?? []
    const uniq = Array.from(new Set(history.value.map((h:any)=>Number(h.version_no)||0))).sort((a,b)=>b-a)
    version.value = Math.max(0, ...uniq)
    versionItems.value = [{label:'latest', value:undefined}, ...uniq.map(v=>({label:`v${v}`, value:v})) ]
    if (selectedVersion.value!==undefined && !uniq.includes(Number(selectedVersion.value))) selectedVersion.value = undefined
  }catch(err:any){
    if (err?.status !== 404) console.warn('fetchVersions error:', err)
    history.value=[]; version.value=0; versionItems.value=[{label:'latest', value:undefined}]
  }
}

async function openHistory(){ dlgHistory.value=true; await fetchVersions() }

onMounted(fetchVersions)
watch(()=>[props.dataset, props.bizDate, props.propertyCode],()=>fetchVersions(),{deep:true})
</script>

<style scoped>
.dataset-card{
  border-radius:12px;
  box-shadow:0 1px 6px rgba(16,24,40,.08);
  background:rgb(var(--v-theme-surface));
}
.card-header{
  display:grid;
  grid-template-columns:1fr auto;
  align-items:center;
  gap:12px;
}
.header-left{display:flex;align-items:center;gap:8px;}
.title-text{font-weight:700;font-size:16px;line-height:40px;}
.header-right{display:flex;align-items:center;gap:10px;}
.ver-select{min-width:160px;height:40px;}
.dryrun-wrap{display:flex;align-items:center;gap:8px;}
.card-sep{margin:0;}
.card-body{padding:14px 16px 12px;}
.part-block{display:flex;align-items:center;gap:12px;margin-bottom:12px;}
.part-label{font-weight:600;color:var(--v-theme-on-surface-variant,#667085);}
.part-chips{display:flex;flex-wrap:wrap;gap:8px;}
.part-chip{max-width:160px;}
.ellipsis{display:inline-block;max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.dz-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.dz-card{display:flex;align-items:center;justify-content:space-between;border:2px dashed rgba(0,0,0,.15);border-radius:12px;padding:12px 14px;min-height:64px;background:linear-gradient(180deg,#fafbff,#f7f8fb);}
.dz-card.single{margin-top:12px;}
.dz-line{display:flex;align-items:center;font-size:.95rem;color:#374151;}
.dz-btn{height:32px;}
.hidden{display:none;}
.toggle-strong :deep(.v-switch__track){transition:background-color .2s;}
.toggle-strong :deep(input:checked + .v-switch__track){background-color:rgb(var(--v-theme-primary)) !important;opacity:1;}
.card-footer{display:flex;align-items:center;gap:8px;padding:10px 16px 12px;}
.btn-same{height:40px;min-width:120px;text-transform:none;font-weight:500;}
</style>
