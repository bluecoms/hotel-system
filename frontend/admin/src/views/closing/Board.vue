<template>
  <v-container class="py-6" style="max-width: 1000px">
    <!-- 알림 -->
    <v-snackbar v-model="snack.show" :timeout="2500" :color="snack.color" location="top right">
      {{ snack.text }}
    </v-snackbar>

    <!-- ANCHOR: BREADCRUMBS / HEADER -->
    <div class="d-flex align-center justify-space-between mb-3" style="gap:12px">
      <div class="d-flex align-center" style="gap:10px">
        <v-breadcrumbs :items="crumbs" class="pa-0 ma-0" />
        <v-divider vertical />
        <h2 class="text-h6">Closing Board</h2>
      </div>

      <div class="d-flex align-center" style="gap:8px">
        <v-chip :color="dayStatus==='CLOSED' ? 'red' : 'blue'" size="small" label>{{ dayStatus }}</v-chip>
        <v-text-field v-model="bizDate" label="Business Date (YYYY-MM-DD)" density="comfortable" style="max-width:160px" />
        <v-btn variant="tonal" @click="refreshDay">Refresh</v-btn>
        <v-divider vertical class="mx-2" />
        <v-btn v-if="isSuper" size="small" :color="dayStatus==='OPEN' ? 'red' : 'green'" @click="toggleDay()">
          {{ dayStatus==='OPEN' ? 'Close Day' : 'Reopen Day' }}
        </v-btn>
      </div>
    </div>

    <v-alert v-if="dayStatus==='CLOSED'" type="warning" class="mb-4">
      선택한 영업일은 <strong>CLOSED</strong> 상태입니다. 업로드가 차단됩니다.
    </v-alert>

    <!-- ANCHOR: CARDS -->
    <v-row>
      <v-col v-for="ds in datasets" :key="ds" cols="12" md="6" lg="4">
        <v-card class="mb-4">
          <v-card-title class="d-flex align-center justify-space-between">
            <span>{{ labelMap[ds] ?? ds }}</span>
            <div class="d-flex align-center" style="gap:6px">
              <v-chip v-if="versions[ds] > 0" size="x-small" label>v{{ versions[ds] }}</v-chip>
              <v-chip
                v-if="(requiredParts[ds]?.length||0)>0"
                :color="(missingParts[ds]?.length||0)===0 ? 'green' : 'orange'"
                size="x-small" label
              >
                Parts {{ (requiredParts[ds]?.length||0) - (missingParts[ds]?.length||0) }}/{{ requiredParts[ds]?.length||0 }}
              </v-chip>
            </div>
          </v-card-title>

          <v-card-text>
            <!-- 일반 업로드 -->
            <template v-if="ds !== 'fnb_sales'">
              <input
                type="file"
                :ref="setRef(ds)"
                accept=".csv,.xlsx,.xls"
                :disabled="dayStatus==='CLOSED'"
              />
            </template>

            <!-- ANCHOR: FNB PAIR INPUTS -->
            <template v-else>
              <div class="d-flex flex-column" style="gap:10px">
                <div>
                  <div class="text-caption mb-1">① 결제수단별 매출 파일</div>
                  <input
                    type="file"
                    :ref="(el:any)=>{ fnbPayRef=el }"
                    accept=".csv,.xlsx,.xls"
                    :disabled="dayStatus==='CLOSED'"
                  />
                </div>
                <div>
                  <div class="text-caption mb-1">② 상품별 매출현황 파일</div>
                  <input
                    type="file"
                    :ref="(el:any)=>{ fnbItemsRef=el }"
                    accept=".csv,.xlsx,.xls"
                    :disabled="dayStatus==='CLOSED'"
                  />
                </div>
                <div class="hint">
                  두 파일 모두 선택 후 <strong>Upload</strong>를 눌러주세요.
                </div>
              </div>
            </template>

            <!-- 파티션(매장/통장 등) -->
            <v-combobox
              v-if="multiParts.has(ds)"
              v-model="partKey[ds]"
              :items="suggestionParts(ds)"
              :label="ds==='fnb_sales' ? 'Partition (예: Restaurant / Bar)' : 'Partition (예: kb-1234 / nh-1234)'"
              density="comfortable"
              hide-details
              clearable
              class="mt-3"
            />

            <!-- 필수 파트 칩 -->
            <div v-if="(requiredParts[ds]?.length||0)>0" class="mt-3">
              <div class="text-caption mb-1">필수 파트</div>
              <div class="d-flex flex-wrap" style="gap:6px">
                <v-chip
                  v-for="p in requiredParts[ds]"
                  :key="p"
                  size="x-small"
                  :color="presentParts[ds]?.includes(p) ? 'green' : ''"
                  :variant="presentParts[ds]?.includes(p) ? 'flat' : 'tonal'"
                  @click="partKey[ds]=p"
                >
                  {{ p }}
                </v-chip>
              </div>
            </div>

            <!-- 헤더 안내(정보성) -->
            <div class="text-caption mt-2" v-if="ds!=='fnb_sales'">
              템플릿 헤더(다른 형식도 자동 변환 지원): <code>{{ headersMap[ds] }}</code>
            </div>
            <div class="text-caption mt-2" v-else>
              템플릿 헤더 예시:
              <div class="mono">[결제수단별] date,dept,method,amount,currency</div>
              <div class="mono">[상품별] date,dept,menu_name,qty,amount,currency</div>
            </div>
          </v-card-text>

          <v-card-actions class="gap-2">
            <!-- 업로드 -->
            <v-btn
              :loading="!!loading[ds]"
              color="primary"
              :disabled="dayStatus==='CLOSED'"
              @click="ds==='fnb_sales' ? uploadFnbPair() : upload(ds)"
            >Upload</v-btn>

            <!-- 템플릿/히스토리 -->
            <v-btn v-if="ds!=='fnb_sales'" variant="text" @click="downloadTemplate(ds)">Template</v-btn>
            <v-btn variant="tonal" @click="openHistory(ds)">History</v-btn>

            <!-- ANCHOR: NO-TXN BUTTON -->
            <v-btn
              v-if="noTxnTargets.has(ds)"
              variant="outlined"
              size="small"
              :disabled="dayStatus==='CLOSED'"
              @click="openNoTxn(ds)"
            >무거래일</v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- History Dialog -->
    <v-dialog v-model="dlgHistory" max-width="780">
      <v-card>
        <v-card-title>History — {{ labelMap[histDs] ?? histDs }} / {{ bizDate }}</v-card-title>
        <v-card-text>
          <v-table>
            <thead>
              <tr>
                <th style="width:80px">Ver</th>
                <th>Filename</th>
                <th style="width:120px">Part</th>
                <th style="width:140px">Size</th>
                <th style="width:180px">Uploaded</th>
                <th style="width:180px"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="it in histItems" :key="it.version_no">
                <td>v{{ it.version_no }}</td>
                <td>{{ it.filename }}</td>
                <td>{{ it.part_key || '-' }}</td>
                <td>{{ fmtSize(it.size) }}</td>
                <td>{{ it.uploaded_at || '-' }}</td>
                <td class="d-flex" style="gap:8px">
                  <v-btn size="small" variant="text" @click="download(histDs, it.version_no)">Download</v-btn>
                  <v-btn v-if="isSuper" size="small" variant="tonal" @click="restore(histDs, it.version_no)">Restore</v-btn>
                </td>
              </tr>
              <tr v-if="!histItems.length"><td colspan="6" class="text-center text-medium-emphasis py-6">No history</td></tr>
            </tbody>
          </v-table>
          <v-alert v-if="msg" type="info" class="mt-2">{{ msg }}</v-alert>
          <v-alert v-if="err" type="warning" class="mt-2">{{ err }}</v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer/>
          <v-btn variant="text" @click="dlgHistory=false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- ANCHOR: NO-TXN MODAL -->
    <NoTxnModal
      :open="dlgNoTxn"
      :businessDate="bizDate"
      :propertyCode="'MOP'"
      :suggestions="['무거래(주말)','은행휴무','공휴일','기타']"
      @done="() => onNoTxnDone()"
      @update:open="(v:boolean)=> dlgNoTxn = v"
    />
  </v-container>
</template>

<script setup lang="ts">
/* ANCHOR: IMPORTS */
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import http from '@/services/http'
import { useAuthStore } from '@/stores/auth'
import NoTxnModal from '@/ui/components/NoTxnModal.vue'

/* ANCHOR: BASIC */
const route = useRoute()
const auth = useAuthStore()
const isSuper = computed(() => !!auth?.hasRole?.('SUPERADMIN') || auth.user?.roles?.includes('SUPERADMIN'))

/** FNB 페어 업로드 엔드포인트 */
const FNB_PAIR_ENDPOINT = 'upload/fnb_sales' // FormData: file_pay, file_items

/* ANCHOR: CONSTS/DATASETS */
const datasets = ['rooms_status','sales_front','fnb_sales','expenses','pay_settlement'] as const
const labelMap: Record<string,string> = {
  rooms_status: 'Rooms Status',
  sales_front: 'Front Sales',
  fnb_sales:   'F&B Sales',
  expenses:    'Expenses',
  pay_settlement: 'Payment Settlement',
}
const headersMap: Record<string,string> = {
  rooms_status:   'room_no,status_code,is_dirty,hk_note',
  sales_front:    'date,folio_no,amount,currency,note',
  fnb_sales:      '(결제수단별 + 상품별) — 템플릿 버튼 숨김',
  expenses:       'date,category,amount,currency,note',
  pay_settlement: 'date,method,amount,currency,note',
}
const crumbs = [
  { title: 'Dashboard', disabled: false, href: '/' },
  { title: 'Closing',   disabled: false },
  { title: 'Board',     disabled: true },
]

/* 파티션 필요한 데이터셋 / 무거래 대상 */
const multiParts = new Set(['fnb_sales','expenses','pay_settlement'])
const noTxnTargets = new Set(['expenses', 'pay_settlement'])

/* ANCHOR: STATE */
const partKey = ref<Record<string,string>>({})
const bizDate = ref(new Date().toISOString().slice(0,10))
const fileRefs: Record<string, HTMLInputElement|null> = {}
let fnbPayRef: HTMLInputElement | null = null
let fnbItemsRef: HTMLInputElement | null = null

const msg = ref(''); const err = ref('')
const dayStatus = ref<'OPEN'|'CLOSED'>('OPEN')
const versions = ref<Record<string, number>>({})
const requiredParts = ref<Record<string,string[]>>({})
const presentParts  = ref<Record<string,string[]>>({})
const missingParts  = ref<Record<string,string[]>>({})
const loading = ref<Record<string, boolean>>({})

/* 스낵바 */
const snack = ref<{show:boolean;color:string;text:string}>({show:false,color:'info',text:''})
function notify(text:string, type:'success'|'info'|'warning'|'error'='info'){
  snack.value = { show: true, text, color:
    type==='success' ? 'green' :
    type==='warning' ? 'orange' :
    type==='error'   ? 'red' : 'info'
  }
}

/* 유틸/제안 */
function setRef(ds:string){ return (el:any)=>{ fileRefs[ds]=el } }
const fallbackParts: Record<string,string[]> = {
  fnb_sales: ['Restaurant','Bar'],
  expenses:  ['kb-1234','nh-1234','woori-1234'],
  pay_settlement: ['kb-1234','nh-1234','woori-1234'],
}
function suggestionParts(ds: string): string[] {
  const req = requiredParts.value[ds] || []
  const pres = presentParts.value[ds] || []
  const merged = Array.from(new Set([...req, ...pres]))
  return merged.length ? merged : (fallbackParts[ds] || [])
}

/* CSV 헤더 검사(정보성) */
async function validateHeadersBeforeUpload(file: File, ds: string) {
  const lower = file.name.toLowerCase()
  if (lower.endsWith('.xlsx') || lower.endsWith('.xls')) return { ok: true }
  const want = (headersMap[ds] || '').split(',').map(s => s.trim()).filter(Boolean)
  if (!want.length || ds==='fnb_sales') return { ok: true }

  const text = await file.text()
  const firstLine = (text.split(/\r?\n/)[0] || '').trim()
  if (!firstLine) return { ok: false, warn: '파일이 비어있거나 헤더가 없습니다.' }
  const got = firstLine.split(',').map(s => s.trim())
  if (got.length === want.length && got.every((h, i) => h === want[i])) return { ok: true }
  return { ok: true, warn: `헤더 불일치(자동 변환 예정)\n- 기대: ${want.join(', ')}\n- 실제: ${got.join(', ')}` }
}

/* ANCHOR: LOAD / STATUS */
async function refreshDay(){
  err.value = ''; msg.value = ''
  try {
    const day = await http.get<{date:string;status:'OPEN'|'CLOSED';done:number;total:number;complete:boolean}>(
      `closing/day?date=${encodeURIComponent(bizDate.value)}&property_code=MOP`
    )
    dayStatus.value = day.status

    const st = await http.get<{
      date:string; property_code:string;
      items:{dataset:string;exists:boolean;versions:number;required_parts?:string[];present_parts?:string[];missing_parts?:string[]}[];
    }>(`closing/status?date=${encodeURIComponent(bizDate.value)}&property_code=MOP`)

    const ver: Record<string, number> = {}
    const req: Record<string,string[]> = {}
    const pres: Record<string,string[]> = {}
    const miss: Record<string,string[]> = {}

    for (const it of st.items) {
      ver[it.dataset]  = it.versions || 0
      req[it.dataset]  = it.required_parts || []
      pres[it.dataset] = it.present_parts || []
      miss[it.dataset] = it.missing_parts || []
    }
    versions.value = ver
    requiredParts.value = req
    presentParts.value = pres
    missingParts.value = miss
  } catch (e:any) {
    const t = e?.detail ?? e?.message ?? '마감 상태 로드 실패'
    err.value = t
    notify(t, 'error')
    dayStatus.value = 'OPEN'
    versions.value = {}
    requiredParts.value = {}
    presentParts.value = {}
    missingParts.value = {}
  }
}

async function toggleDay(){
  try{
    const next: 'OPEN'|'CLOSED' = dayStatus.value === 'OPEN' ? 'CLOSED' : 'OPEN'
    await http.put<{ok:boolean; status:string}>('closing/day', {
      date: bizDate.value, property_code: 'MOP', status: next,
    })
    await refreshDay()
    const t = `Day → ${next}`; msg.value = t; notify(t, 'success')
  }catch(e:any){
    const t = e?.detail ?? e?.message ?? '상태 변경 실패'
    err.value = t; notify(t, 'error')
  }
}

/* ANCHOR: UPLOAD (SINGLE) */
async function upload(ds:string){
  const el=fileRefs[ds]
  if(!el||!el.files||!el.files[0]){ const t='파일 선택 필요'; err.value=t; notify(t,'warning'); return }
  msg.value=''; err.value=''

  if (dayStatus.value === 'CLOSED') { const t='마감(CLOSED) 일자는 업로드할 수 없습니다.'; err.value=t; notify(t,'error'); return }

  if (multiParts.has(ds)) {
    const pk = (partKey.value[ds] || '').trim()
    if (!pk) { const t='Partition을 선택/입력하세요.'; err.value=t; notify(t,'warning'); return }
  }

  const file = el.files[0]
  const head = await validateHeadersBeforeUpload(file, ds)
  if (!head.ok) { const t=head.warn || '파일 오류'; err.value=t; notify(t,'error'); return }
  if (head.warn) { msg.value = head.warn; notify(head.warn,'info') }

  const fd=new FormData()
  fd.append('business_date', bizDate.value)
  fd.append('property_code', 'MOP')
  fd.append('part_key', (partKey.value[ds] || '').trim())
  fd.append('file', file)

  try {
    loading.value[ds] = true
    const r = await http.post<{ok:boolean;session_id:number;version_no:number}>(`upload/${ds}`, fd)
    const t = `${labelMap[ds] ?? ds} v${r.version_no ?? '?'} 업로드 완료`
    msg.value = t; notify(t,'success')
    await refreshDay()
  } catch (e:any) {
    const why =
      e?.detail?.message || e?.detail ||
      (e?.status===409 ? '마감(CLOSED) 일자 업로드 금지(409)' : '') ||
      e?.message || '업로드 실패(원인 불명)'
    err.value = why; notify(why,'error')
  } finally {
    loading.value[ds] = false
    if (el) el.value = ''
  }
}

/* ANCHOR: FNB UPLOAD (PAIR) */
async function uploadFnbPair(){
  if (dayStatus.value === 'CLOSED') { notify('마감(CLOSED) 일자는 업로드 불가','error'); return }
  const pk = (partKey.value['fnb_sales'] || '').trim()
  if (!pk) { notify('Partition을 선택/입력하세요. (예: Restaurant / Bar)','warning'); return }
  const f1 = fnbPayRef?.files?.[0]
  const f2 = fnbItemsRef?.files?.[0]
  if (!f1 || !f2) { notify('결제수단별 파일과 상품별 파일을 모두 선택해주세요.','warning'); return }

  const fd = new FormData()
  fd.append('business_date', bizDate.value)
  fd.append('property_code', 'MOP')
  fd.append('part_key', pk)
  fd.append('file_pay', f1)   // 백엔드: file_pay / file_items
  fd.append('file_items', f2)

  try{
    loading.value['fnb_sales'] = true
    const r = await http.post<{ok:boolean;version_no:number}>(FNB_PAIR_ENDPOINT, fd)
    notify(`F&B 업로드 완료 → v${r.version_no ?? '?'}`, 'success')
    await refreshDay()
  }catch(e:any){
    notify(e?.detail ?? e?.message ?? 'F&B 업로드 실패', 'error')
  }finally{
    loading.value['fnb_sales'] = false
    if (fnbPayRef) fnbPayRef.value = ''
    if (fnbItemsRef) fnbItemsRef.value = ''
  }
}

/* ANCHOR: TEMPLATE DL */
function downloadTemplate(ds:string){
  const text = (headersMap[ds] ?? '') + '\n'
  const blob = new Blob([text], { type:'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href=url; a.download=`${ds}.csv`; a.click()
  URL.revokeObjectURL(url)
}

/* ANCHOR: HISTORY */
const dlgHistory = ref(false)
const histDs = ref<string>('rooms_status')
const histItems = ref<{version_no:number;filename:string;size:number;uploaded_at:string;part_key?:string}[]>([])

function fmtSize(n:number){
  if(!n && n!==0) return '-'
  if(n<1024) return `${n} B`
  if(n<1024*1024) return `${(n/1024).toFixed(1)} KB`
  return `${(n/1024/1024).toFixed(1)} MB`
}

async function openHistory(ds:string){
  histDs.value = ds
  msg.value = ''; err.value = ''
  try{
    const r = await http.get<{session_id:number;items:{version_no:number;filename:string;size:number;uploaded_at:string;part_key?:string}[]}>(
      `upload/versions?dataset=${encodeURIComponent(ds)}&business_date=${encodeURIComponent(bizDate.value)}&property_code=MOP`
    )
    histItems.value = r.items || []
    dlgHistory.value = true
  }catch(e:any){
    const t='이력 조회 실패'; err.value = t; notify(t,'error')
  }
}

async function download(ds: string, ver: number) {
  try {
    const qs = new URLSearchParams({
      dataset: ds, business_date: bizDate.value, property_code: 'MOP', version_no: String(ver),
    })
    const url = `${http.url('upload/download')}?${qs.toString()}`
    const resp = await fetch(url, { headers: http.headers() })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const blob = await resp.blob()
    const link = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = link; a.download = `${ds}_${bizDate.value}_v${ver}.csv`; a.click()
    URL.revokeObjectURL(link)
  } catch (e: any) {
    const t = `다운로드 실패: ${e?.message || 'unknown'}`
    err.value = t; notify(t,'error')
  }
}

async function restore(ds:string, ver:number){
  if (!confirm(`v${ver} 으로 되돌리고 새 버전을 생성할까요?`)) return
  try{
    const r = await http.post<{ok:boolean;version_no:number}>(
      'upload/restore',
      { dataset: ds, business_date: bizDate.value, property_code: 'MOP', version_no: ver }
    )
    const t = `복구 완료 → v${r.version_no}`; msg.value = t; notify(t,'success')
    await refreshDay()
    await openHistory(ds)
  }catch(e:any){
    const t = (e?.status === 409) ? '마감(CLOSED) 일자는 복구할 수 없습니다.(409)' : (e?.detail ?? e?.message ?? '복구 실패')
    err.value = t; notify(t,'error')
  }
}

/* ANCHOR: NO-TXN MODAL STATE/HANDLERS */
const dlgNoTxn = ref(false)
const noTxnDs  = ref<'expenses'|'pay_settlement'>('expenses')
function openNoTxn(ds:string){
  noTxnDs.value = (ds === 'pay_settlement') ? 'pay_settlement' : 'expenses'
  dlgNoTxn.value = true
}
async function onNoTxnDone(){
  // NoTxnModal이 내부에서 API 호출을 끝내고 완료 신호만 emit하는 케이스
  notify('무거래일 등록 완료', 'success')
  dlgNoTxn.value = false
  await refreshDay()
}

/* ANCHOR: INIT */
onMounted(async () => {
  const q = route.query
  const qDate = typeof q.date === 'string' ? q.date : ''
  const qDs = typeof q.dataset === 'string' ? q.dataset : ''
  const qHist = String(q.history ?? '') === '1'

  if (qDate) bizDate.value = qDate
  await refreshDay()
  if (qHist && qDs && (datasets as readonly string[]).includes(qDs)) {
    openHistory(qDs)
  }
})
</script>

<style scoped>
.v-card .v-card-title{ font-weight:700; }
.v-card .text-caption code{ background:#f7f9fd; border:1px solid var(--line); padding:2px 6px; border-radius:6px; }
.v-chip.bg-green{ color:#0b6245 !important; }
.hint{ font-size:.85rem; color:#6b7280 }
.mono{ font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
</style>
