<template>
  <v-container class="py-6" style="max-width:1200px">
    <h2 class="text-h5 mb-4">OTA Management</h2>

    <v-tabs v-model="tab" class="mb-4">
      <v-tab value="sales">Sales</v-tab>
      <v-tab value="alias">Channel Aliases</v-tab>
      <v-tab value="fees">Channel Fees</v-tab>
    </v-tabs>

    <!-- 딱 1개만 존재해야 하는 v-window -->
    <v-window v-model="tab">
      <!-- ========== Sales ========== -->
      <v-window-item value="sales">
        <v-card class="mb-4">
          <v-card-text>
            <div class="d-flex flex-wrap align-center" style="gap:12px">
              <v-text-field v-model="from" label="From (YYYY-MM-DD)" density="comfortable" style="max-width:180px"/>
              <v-text-field v-model="to"   label="To (YYYY-MM-DD)"   density="comfortable" style="max-width:180px"/>
              <v-btn color="primary" @click="syncAndLoad">Load</v-btn>
              <v-btn variant="tonal" @click="exportSalesCsv" :disabled="!sales.rows.length">Export CSV</v-btn>
              <v-spacer/>
              <div class="text-caption">
                Unknown: gross {{ fmtMoney(sales.unknown.gross) }} / cnt {{ sales.unknown.count }}
              </div>
            </div>
          </v-card-text>
        </v-card>

        <v-table density="comfortable">
          <thead>
            <tr>
              <th>Channel</th>
              <th class="text-right">Gross</th>
              <th class="text-right">Fee %</th>
              <th class="text-right">Fee Amt</th>
              <th class="text-right">Net</th>
              <th class="text-right">Count</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in sales.rows" :key="r.channel">
              <td>{{ r.channel }}</td>
              <td class="text-right">{{ fmtMoney(r.gross) }}</td>
              <td class="text-right">{{ r.fee_pct ?? 0 }}</td>
              <td class="text-right">{{ fmtMoney(r.fee_amount ?? (r.gross * (Number(r.fee_pct || 0)/100))) }}</td>
              <td class="text-right">{{ fmtMoney(r.net ?? (r.gross - (r.fee_amount ?? (r.gross * (Number(r.fee_pct || 0)/100))))) }}</td>
              <td class="text-right">{{ r.count || 0 }}</td>
            </tr>
            <tr v-if="!sales.rows.length">
              <td colspan="6" class="text-center text-medium-emphasis py-6">No data</td>
            </tr>
          </tbody>
          <tfoot>
            <tr>
              <td class="text-right"><strong>Total</strong></td>
              <td class="text-right"><strong>{{ fmtMoney(sales.total.gross) }}</strong></td>
              <td></td>
              <td></td>
              <td class="text-right"><strong>{{ fmtMoney(sales.total.net) }}</strong></td>
              <td></td>
            </tr>
          </tfoot>
        </v-table>

        <v-alert v-if="errSales" type="warning" class="mt-3">{{ errSales }}</v-alert>
      </v-window-item>

      <!-- ========== Aliases ========== -->
      <v-window-item value="alias">
        <v-card class="mb-4">
          <v-card-text>
            <div class="d-flex flex-wrap align-center" style="gap:12px">
              <v-text-field v-model="alias.q" label="Search" density="comfortable" hide-details style="max-width:240px" @keyup.enter="loadAlias(1)"/>
              <v-select
                :items="activeFilterItems"
                v-model="alias.active"
                label="Active"
                density="comfortable"
                hide-details
                style="max-width:140px"
              />
              <v-btn color="primary" @click="loadAlias(1)">Search</v-btn>
              <v-spacer/>
              <v-btn color="primary" @click="openAliasCreate">New Alias</v-btn>
            </div>
          </v-card-text>
        </v-card>

        <v-table density="comfortable">
          <thead>
            <tr>
              <th style="width:80px">ID</th>
              <th>Pattern (k)</th>
              <th>Canonical (v)</th>
              <th style="width:120px" class="text-right">Weight</th>
              <th style="width:120px">Active</th>
              <th style="width:200px"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in alias.rows" :key="r.id">
              <td>{{ r.id }}</td>
              <td>{{ r.k }}</td>
              <td>{{ r.v }}</td>
              <td class="text-right">{{ r.weight }}</td>
              <td>
                <v-chip :color="r.is_active ? 'green' : 'grey'" size="small" label>{{ r.is_active ? 'Y' : 'N' }}</v-chip>
              </td>
              <td class="d-flex" style="gap:8px">
                <v-btn size="small" variant="text" @click="openAliasEdit(r)">Edit</v-btn>
                <v-btn size="small" variant="tonal" color="red" @click="delKeyword(r, GROUP_ALIAS)">Delete</v-btn>
              </td>
            </tr>
            <tr v-if="!alias.rows.length">
              <td colspan="6" class="text-center text-medium-emphasis py-6">No items</td>
            </tr>
          </tbody>
        </v-table>

        <div class="d-flex justify-center my-4">
          <v-pagination v-model="alias.page" :length="alias.pages" @update:modelValue="loadAlias"/>
        </div>

        <v-alert v-if="alias.err" type="warning">{{ alias.err }}</v-alert>
        <v-alert v-if="alias.msg" type="info" class="mt-2">{{ alias.msg }}</v-alert>
      </v-window-item>

      <!-- ========== Fees ========== -->
      <v-window-item value="fees">
        <v-card class="mb-4">
          <v-card-text>
            <div class="d-flex flex-wrap align-center" style="gap:12px">
              <v-text-field v-model="fee.q" label="Search" density="comfortable" hide-details style="max-width:240px" @keyup.enter="loadFee(1)"/>
              <v-select
                :items="activeFilterItems"
                v-model="fee.active"
                label="Active"
                density="comfortable"
                hide-details
                style="max-width:140px"
              />
              <v-btn color="primary" @click="loadFee(1)">Search</v-btn>
              <v-spacer/>
              <v-btn color="primary" @click="openFeeCreate">New Fee</v-btn>
            </div>
          </v-card-text>
        </v-card>

        <v-table density="comfortable">
          <thead>
            <tr>
              <th style="width:80px">ID</th>
              <th>Channel (k)</th>
              <th class="text-right" style="width:140px">Fee % (v)</th>
              <th style="width:120px" class="text-right">Weight</th>
              <th style="width:120px">Active</th>
              <th style="width:200px"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in fee.rows" :key="r.id">
              <td>{{ r.id }}</td>
              <td>{{ r.k }}</td>
              <td class="text-right">{{ r.v }}</td>
              <td class="text-right">{{ r.weight }}</td>
              <td>
                <v-chip :color="r.is_active ? 'green' : 'grey'" size="small" label>{{ r.is_active ? 'Y' : 'N' }}</v-chip>
              </td>
              <td class="d-flex" style="gap:8px">
                <v-btn size="small" variant="text" @click="openFeeEdit(r)">Edit</v-btn>
                <v-btn size="small" variant="tonal" color="red" @click="delKeyword(r, GROUP_FEE)">Delete</v-btn>
              </td>
            </tr>
            <tr v-if="!fee.rows.length">
              <td colspan="6" class="text-center text-medium-emphasis py-6">No items</td>
            </tr>
          </tbody>
        </v-table>

        <div class="d-flex justify-center my-4">
          <v-pagination v-model="fee.page" :length="fee.pages" @update:modelValue="loadFee"/>
        </div>

        <v-alert v-if="fee.err" type="warning">{{ fee.err }}</v-alert>
        <v-alert v-if="fee.msg" type="info" class="mt-2">{{ fee.msg }}</v-alert>
      </v-window-item>
    </v-window>

    <!-- === Dialogs (한 번만) === -->
    <v-dialog v-model="dlgAlias" max-width="520">
      <v-card>
        <v-card-title>{{ aliasForm.id ? 'Edit Alias' : 'New Alias' }}</v-card-title>
        <v-card-text>
          <v-text-field v-model="aliasForm.k" label="Pattern (정규식/파이프 구분 등 자유)" />
          <v-text-field v-model="aliasForm.v" label="Canonical (표준 채널명, 예: agoda)" />
          <div class="d-flex" style="gap:12px">
            <v-text-field v-model.number="aliasForm.weight" label="Weight" type="number" style="max-width:160px"/>
            <v-switch v-model="aliasForm.is_active" label="Active" inset />
          </div>
          <div class="text-caption">
            예) <code>agoda|ago|아고다</code> → Canonical: <code>agoda</code>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer/>
          <v-btn variant="text" @click="dlgAlias=false">Cancel</v-btn>
          <v-btn color="primary" @click="saveAlias">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="dlgFee" max-width="520">
      <v-card>
        <v-card-title>{{ feeForm.id ? 'Edit Fee' : 'New Fee' }}</v-card-title>
        <v-card-text>
          <v-text-field v-model="feeForm.k" label="Channel (표준 채널명, 예: agoda)" />
          <v-text-field v-model="feeForm.v" label="Fee % (숫자, 예: 12.5)" type="number" />
          <div class="d-flex" style="gap:12px">
            <v-text-field v-model.number="feeForm.weight" label="Weight" type="number" style="max-width:160px"/>
            <v-switch v-model="feeForm.is_active" label="Active" inset />
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer/>
          <v-btn variant="text" @click="dlgFee=false">Cancel</v-btn>
          <v-btn color="primary" @click="saveFee">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import http from '@/services/http'
import { useAuthStore } from '@/stores/auth'

type KeywordRow = {
  id: number
  group_name: string
  k: string
  v: string
  weight: number
  is_active: boolean
  created_at: string
}
type OtaSalesRow = {
  channel: string
  gross: number
  fee_pct?: number
  fee_amount?: number
  net?: number
  count?: number
}

const auth = useAuthStore()
const isAdmin = computed(() => {
  const r = auth.user?.roles || []
  return r.includes('ADMIN') || r.includes('SUPERADMIN')
})
const router = useRouter()
const route  = useRoute()

// 그룹 상수
const GROUP_ALIAS = 'sales.channel.alias'
const GROUP_FEE   = 'sales.channel.fee'

// 탭
const tab = ref<'sales'|'alias'|'fees'>('sales')

// 기간 쿼리 동기화
const today = new Date().toISOString().slice(0,10)
const from = ref(typeof route.query.from === 'string' ? route.query.from : today)
const to   = ref(typeof route.query.to   === 'string' ? route.query.to   : today)

watch(() => route.query, (q) => {
  if (typeof q.from === 'string') from.value = q.from
  if (typeof q.to   === 'string') to.value   = q.to
}, { deep: true })

function syncAndLoad() {
  router.replace({ path: '/ota', query: { from: from.value, to: to.value } })
  loadSales()
}

/* ---------------- Sales ---------------- */
const errSales = ref<string | null>(null)
const sales = ref<{rows:OtaSalesRow[], unknown:{gross:number;count:number}, total:{gross:number;net:number}}>({
  rows: [],
  unknown: { gross: 0, count: 0 },
  total: { gross: 0, net: 0 }
})

async function loadSales() {
  errSales.value = null
  try{
    const data = await http.get<{rows:OtaSalesRow[], unknown:{gross:number;count:number}, total:{gross:number;net:number}}>(
      `reports/ota-sales?from=${encodeURIComponent(from.value)}&to=${encodeURIComponent(to.value)}&property_code=MOP`
    )
    sales.value = {
      rows: data.rows || [],
      unknown: data.unknown || {gross:0, count:0},
      total: data.total || {gross:0, net:0}
    }
  }catch(e:any){
    errSales.value = e?.detail ?? e?.message ?? 'Sales load failed'
    sales.value = { rows: [], unknown:{gross:0,count:0}, total:{gross:0,net:0} }
  }
}

function toCsvValue(v:any){ return `"${String(v ?? '').replace(/"/g,'""')}"` }
function exportSalesCsv(){
  const rows = sales.value.rows || []
  const header = ['channel','gross','fee_pct','fee_amount','net','count']
  const lines = [header.join(',')]
  for(const r of rows){
    const feeAmt = r.fee_amount ?? (r.gross * (Number(r.fee_pct || 0)/100))
    const net = r.net ?? (r.gross - feeAmt)
    lines.push([
      toCsvValue(r.channel),
      toCsvValue(r.gross),
      toCsvValue(r.fee_pct ?? 0),
      toCsvValue(feeAmt),
      toCsvValue(net),
      toCsvValue(r.count ?? 0),
    ].join(','))
  }
  const blob = new Blob([lines.join('\n')+'\n'], { type:'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = `ota-sales_${from.value}_${to.value}.csv`; a.click()
  URL.revokeObjectURL(url)
}
function fmtMoney(n:number){ try{ return (Number(n||0)).toLocaleString() } catch { return String(n ?? 0) } }

/* ---------------- Aliases ---------------- */
const activeFilterItems = [
  { title: 'All',   value: 'all' },
  { title: 'Active',value: 'true' },
  { title: 'Inactive', value: 'false' },
]
const alias = ref({
  rows: [] as KeywordRow[],
  q: '',
  active: 'all' as 'all'|'true'|'false',
  page: 1,
  size: 20,
  total: 0,
  err: null as string | null,
  msg: null as string | null,
  get pages(){ return Math.max(1, Math.ceil(this.total / this.size)) }
})
async function loadAlias(p = alias.value.page){
  alias.value.err = null; alias.value.msg = null
  alias.value.page = p
  try{
    const params = new URLSearchParams()
    params.set('group_name', GROUP_ALIAS)
    if (alias.value.q) params.set('q', alias.value.q)
    if (alias.value.active !== 'all') params.set('active', String(alias.value.active === 'true'))
    params.set('page', String(p))
    params.set('size', String(alias.value.size))
    const r = await http.get<{total:number;page:number;size:number;items:KeywordRow[]}>(
      `keywords?${params.toString()}`
    )
    alias.value.rows = r.items
    alias.value.total = r.total
  }catch(e:any){
    alias.value.rows = []; alias.value.total = 0
    alias.value.err = e?.detail ?? e?.message ?? 'Load failed'
  }
}
const dlgAlias = ref(false)
const aliasForm = ref<{id?:number; k:string; v:string; weight:number; is_active:boolean}>({
  k: '', v: '', weight: 0, is_active: true
})
function openAliasCreate(){ aliasForm.value = { k:'', v:'', weight:0, is_active:true }; dlgAlias.value = true }
function openAliasEdit(row: KeywordRow){
  aliasForm.value = { id: row.id, k: row.k, v: row.v, weight: row.weight, is_active: row.is_active }
  dlgAlias.value = true
}
async function saveAlias(){
  try{
    const body = {
      group_name: GROUP_ALIAS,
      k: aliasForm.value.k,
      v: aliasForm.value.v,
      weight: Number(aliasForm.value.weight||0),
      is_active: !!aliasForm.value.is_active,
    }
    if (aliasForm.value.id) await http.put(`keywords/${aliasForm.value.id}`, body)
    else await http.post('keywords', body)
    dlgAlias.value = false
    alias.value.msg = 'Saved'
    await loadAlias(1)
  }catch(e:any){
    alias.value.err = e?.detail ?? e?.message ?? 'Save failed'
  }
}

/* ---------------- Fees ---------------- */
const fee = ref({
  rows: [] as KeywordRow[],
  q: '',
  active: 'all' as 'all'|'true'|'false',
  page: 1,
  size: 20,
  total: 0,
  err: null as string | null,
  msg: null as string | null,
  get pages(){ return Math.max(1, Math.ceil(this.total / this.size)) }
})
async function loadFee(p = fee.value.page){
  fee.value.err = null; fee.value.msg = null
  fee.value.page = p
  try{
    const params = new URLSearchParams()
    params.set('group_name', GROUP_FEE)
    if (fee.value.q) params.set('q', fee.value.q)
    if (fee.value.active !== 'all') params.set('active', String(fee.value.active === 'true'))
    params.set('page', String(p))
    params.set('size', String(fee.value.size))
    const r = await http.get<{total:number;page:number;size:number;items:KeywordRow[]}>(
      `keywords?${params.toString()}`
    )
    fee.value.rows = r.items
    fee.value.total = r.total
  }catch(e:any){
    fee.value.rows = []; fee.value.total = 0
    fee.value.err = e?.detail ?? e?.message ?? 'Load failed'
  }
}
const dlgFee = ref(false)
const feeForm = ref<{id?:number; k:string; v:string; weight:number; is_active:boolean}>({
  k: '', v: '', weight: 0, is_active: true
})
function openFeeCreate(){ feeForm.value = { k:'', v:'', weight:0, is_active:true }; dlgFee.value = true }
function openFeeEdit(row: KeywordRow){
  feeForm.value = { id: row.id, k: row.k, v: row.v, weight: row.weight, is_active: row.is_active }
  dlgFee.value = true
}
async function saveFee(){
  try{
    const body = {
      group_name: GROUP_FEE,
      k: feeForm.value.k,
      v: String(feeForm.value.v ?? ''),
      weight: Number(feeForm.value.weight||0),
      is_active: !!feeForm.value.is_active,
    }
    if (feeForm.value.id) await http.put(`keywords/${feeForm.value.id}`, body)
    else await http.post('keywords', body)
    dlgFee.value = false
    fee.value.msg = 'Saved'
    await loadFee(1)
  }catch(e:any){
    fee.value.err = e?.detail ?? e?.message ?? 'Save failed'
  }
}

/* 공통 삭제 */
async function delKeyword(row: KeywordRow, group: string){
  if (!confirm(`#${row.id} 삭제할까요?`)) return
  try{
    await http.delete(`keywords/${row.id}`)
    if (group === GROUP_ALIAS) await loadAlias(alias.value.page)
    else await loadFee(fee.value.page)
  }catch(e:any){
    const tgt = (group === GROUP_ALIAS) ? alias.value : fee.value
    tgt.err = e?.detail ?? e?.message ?? 'Delete failed'
  }
}

/* 초기 로드 */
onMounted(() => {
  // 주소의 쿼리를 우선 반영
  from.value = (typeof route.query.from === 'string' && route.query.from) ? route.query.from : from.value
  to.value   = (typeof route.query.to   === 'string' && route.query.to)   ? route.query.to   : to.value
  loadSales(); loadAlias(1); loadFee(1)
})
</script>
