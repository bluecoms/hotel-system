<template>
  <v-container class="py-6" style="max-width:1200px">
    <h2 class="text-h5 mb-4">Keywords</h2>

    <v-tabs v-model="tab" class="mb-4">
      <v-tab value="manage">Manage</v-tab>
      <v-tab value="test">Analyze Test</v-tab>
    </v-tabs>

    <v-window v-model="tab">
      <v-window-item value="manage">
        <v-card class="mb-4">
          <v-card-text>
            <div class="d-flex flex-wrap align-center" style="gap:12px">
              <v-select
                v-model="groupName"
                :items="groupOptions"
                item-title="title"
                item-value="value"
                label="Group"
                density="comfortable"
                hide-details
                style="max-width:260px"
              />
              <v-text-field
                v-model="q"
                label="Search (k / v)"
                density="comfortable"
                hide-details
                clearable
                style="max-width:300px"
                @keyup.enter="load(1)"
              />
              <v-select
                v-model="activeFilter"
                :items="activeFilterItems"
                item-title="title"
                item-value="value"
                label="Active"
                density="comfortable"
                hide-details
                style="max-width:140px"
              />
              <v-btn :loading="loading" color="primary" @click="load(1)">Search</v-btn>
              <v-spacer />
              <v-btn variant="tonal" @click="exportCsv" :disabled="!rows.length || exporting">Export CSV</v-btn>
              <v-btn variant="tonal" @click="openImport">Import CSV</v-btn>
              <v-btn color="primary" @click="openCreate">New</v-btn>
            </div>
          </v-card-text>
        </v-card>

        <v-skeleton-loader v-if="loading" type="table" class="mb-2" />

        <template v-else>
          <v-table density="comfortable">
            <thead>
              <tr>
                <th style="width:80px">ID</th>
                <th>Group</th>
                <th>k (pattern)</th>
                <th>v (canonical)</th>
                <th style="width:120px" class="text-right">Weight</th>
                <th style="width:120px">Active</th>
                <th style="width:200px"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in rows" :key="r.id">
                <td>{{ r.id }}</td>
                <td>{{ r.group_name }}</td>
                <td>{{ r.k }}</td>
                <td>{{ r.v }}</td>
                <td class="text-right">{{ r.weight }}</td>
                <td>
                  <v-chip :color="r.is_active ? 'success' : 'grey'" size="small" label>
                    {{ r.is_active ? 'Y' : 'N' }}
                  </v-chip>
                </td>
                <td class="d-flex" style="gap:8px">
                  <v-btn size="small" variant="text" @click="openEdit(r)">Edit</v-btn>
                  <v-btn size="small" variant="tonal" color="red" @click="removeRow(r)">Delete</v-btn>
                </td>
              </tr>
              <tr v-if="!rows.length">
                <td colspan="7" class="text-center text-medium-emphasis py-6">No items</td>
              </tr>
            </tbody>
          </v-table>

          <div class="d-flex justify-center my-4">
            <v-pagination v-model="page" :length="pages" @update:modelValue="load" />
          </div>
        </template>

        <v-alert v-if="err" type="warning" variant="tonal" class="mt-2">{{ err }}</v-alert>
        <v-alert v-if="msg" type="info" variant="tonal" class="mt-2">{{ msg }}</v-alert>

        <v-dialog v-model="dlg" max-width="560">
          <v-card>
            <v-card-title>{{ form.id ? 'Edit Keyword' : 'New Keyword' }}</v-card-title>
            <v-card-text>
              <v-select
                v-model="form.group_name"
                :items="groupOptions"
                item-title="title"
                item-value="value"
                label="Group"
                density="comfortable"
                hide-details
              />
              <v-text-field v-model="form.k" label="k (pattern, ex: 'O|바다' or '^(?=.*바다).*')" />
              <v-text-field v-model="form.v" label="v (canonical tag, ex: 'SEA','RO','BF2','POA')" />
              <div class="d-flex" style="gap:12px">
                <v-text-field v-model.number="form.weight" label="Weight" type="number" style="max-width:160px" />
                <v-switch v-model="form.is_active" label="Active" inset />
              </div>
              <div class="text-caption">
                • <strong>sales.tag.alias</strong> : 메모/노트에서 태그를 추출하기 위한 매칭 규칙<br>
                • k(패턴)은 <code>|</code> 로 여러 표현을 묶거나 정규식(예: <code>^(?=.*조식).*2인</code>)도 사용 가능<br>
                • v(표준태그)는 결과로 기록될 코드(예: <code>RO</code>, <code>BF2</code>, <code>POA</code>)<br>
                • weight는 충돌 시 우선순위(값이 클수록 우선)
              </div>
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <v-btn variant="text" @click="dlg=false">Cancel</v-btn>
              <v-btn color="primary" :loading="saving" @click="save">Save</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>

        <v-dialog v-model="dlgImport" max-width="640">
          <v-card>
            <v-card-title>Import CSV</v-card-title>
            <v-card-text>
              <div class="text-body-2 mb-2">
                헤더 권장: <code>group_name,k,v,weight,is_active</code> (미지정 시 group_name은 현재 선택 그룹으로 기본값)
              </div>
              <input
                type="file"
                ref="importRef"
                accept=".csv,.xlsx,.xls,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel"
              />
              <v-alert v-if="importMsg" type="info" variant="tonal" class="mt-3">{{ importMsg }}</v-alert>
              <v-alert v-if="importErr" type="warning" variant="tonal" class="mt-3">{{ importErr }}</v-alert>
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <v-btn variant="text" @click="dlgImport=false">Close</v-btn>
              <v-btn color="primary" :loading="importing" @click="doImport">Upload</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
      </v-window-item>

      <v-window-item value="test">
        <v-card class="mb-4">
          <v-card-text>
            <div class="d-flex flex-wrap align-start" style="gap:16px">
              <v-select
                v-model="testGroup"
                :items="[{title:'sales.tag.alias',value:'sales.tag.alias'}]"
                item-title="title"
                item-value="value"
                label="Rule Group"
                density="comfortable"
                hide-details
                style="max-width:260px"
              />
              <v-btn variant="tonal" @click="reloadRules">Reload Rules</v-btn>
              <v-spacer/>
              <v-switch v-model="useRegexWordBoundary" inset label="Word-boundary (토큰)" />
              <v-switch v-model="useCaseInsensitive" inset label="Ignore Case" />
            </div>
            <v-textarea
              v-model="sampleNote"
              class="mt-4"
              label="Sample Note / Memo"
              rows="5"
              auto-grow
              hide-details
            />
            <div class="d-flex align-center mt-3" style="gap:12px">
              <v-btn color="primary" @click="analyze">Analyze</v-btn>
              <div class="text-caption">현재 활성 규칙만 사용</div>
            </div>
          </v-card-text>
        </v-card>

        <v-card>
          <v-card-title>Result</v-card-title>
          <v-card-text>
            <div class="mb-2"><strong>Matched Tags:</strong></div>
            <div class="d-flex flex-wrap" style="gap:8px">
              <v-chip v-for="t in result.tags" :key="t.code" color="primary" label>
                {{ t.code }} (score: {{ t.score }})
              </v-chip>
              <span v-if="!result.tags.length" class="text-medium-emphasis">No tags</span>
            </div>

            <v-divider class="my-4" />

            <div class="mb-2"><strong>Matched Rules:</strong></div>
            <v-table density="compact">
              <thead>
                <tr>
                  <th style="width:90px">ID</th>
                  <th>k (pattern)</th>
                  <th style="width:140px">v (tag)</th>
                  <th style="width:100px" class="text-right">Weight</th>
                  <th>hit</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="m in result.matches" :key="m.id">
                  <td>{{ m.id }}</td>
                  <td>{{ m.k }}</td>
                  <td>{{ m.v }}</td>
                  <td class="text-right">{{ m.weight }}</td>
                  <td>{{ m.hit }}</td>
                </tr>
                <tr v-if="!result.matches.length">
                  <td colspan="5" class="text-center text-medium-emphasis py-6">No matches</td>
                </tr>
              </tbody>
            </v-table>

            <v-alert v-if="testErr" type="warning" variant="tonal" class="mt-3">{{ testErr }}</v-alert>
          </v-card-text>
        </v-card>
      </v-window-item>
    </v-window>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import http from '@/services/http'
import { useToast } from '@/ui/composables/useToast'

type KeywordRow = {
  id: number
  group_name: string
  k: string
  v: string
  weight: number
  is_active: boolean
  created_at: string
}

/* ========= Manage state ========= */
const { success: toastOk, error: toastErr } = useToast()
const tab = ref<'manage'|'test'>('manage')

const groupOptions = [
  { title: 'sales.tag.alias', value: 'sales.tag.alias' },
]

const groupName = ref<string>('sales.tag.alias')
const q = ref('')
const activeFilter = ref<'all'|'true'|'false'>('all')
const activeFilterItems = [
  { title: 'All', value: 'all' },
  { title: 'Active', value: 'true' },
  { title: 'Inactive', value: 'false' },
]

const rows = ref<KeywordRow[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(20)
const pages = computed(() => Math.max(1, Math.ceil(total.value / size.value)))
const loading = ref(false)
const saving = ref(false)
const exporting = ref(false)
const importing = ref(false)

const err = ref<string | null>(null)
const msg = ref<string | null>(null)

async function load(p = page.value) {
  err.value = null; msg.value = null
  page.value = p
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.set('group_name', groupName.value)
    if (q.value) params.set('q', q.value)
    if (activeFilter.value !== 'all') params.set('active', String(activeFilter.value === 'true'))
    params.set('page', String(p))
    params.set('size', String(size.value))
    const r = await http.get<{ total:number; page:number; size:number; items:KeywordRow[] }>(`keywords?${params}`)
    rows.value = r.items || []
    total.value = r.total || 0
  } catch (e: any) {
    rows.value = []; total.value = 0
    const m = e?.detail ?? e?.message ?? 'Load failed'
    err.value = m
    toastErr(m)
  } finally {
    loading.value = false
  }
}

onMounted(() => load(1))

/* Create/Edit */
const dlg = ref(false)
const form = ref<{id?:number; group_name:string; k:string; v:string; weight:number; is_active:boolean}>({
  group_name: groupName.value, k:'', v:'', weight: 0, is_active: true
})
function openCreate() {
  form.value = { group_name: groupName.value, k:'', v:'', weight:0, is_active:true }
  dlg.value = true
}
function openEdit(r: KeywordRow) {
  form.value = { id:r.id, group_name:r.group_name, k:r.k, v:r.v, weight:r.weight, is_active:r.is_active }
  dlg.value = true
}
async function save() {
  saving.value = true
  try {
    const body = {
      group_name: form.value.group_name,
      k: String(form.value.k || ''),
      v: String(form.value.v || ''),
      weight: Number(form.value.weight || 0),
      is_active: !!form.value.is_active,
    }
    if (!body.k) throw new Error('k (pattern)은 필수입니다.')
    if (form.value.id) await http.put(`keywords/${form.value.id}`, body)
    else await http.post('keywords', body)
    dlg.value = false
    msg.value = 'Saved'
    toastOk('저장되었습니다.')
    await load(1)
  } catch (e:any) {
    const m = e?.detail ?? e?.message ?? 'Save failed'
    err.value = m
    toastErr(m)
  } finally {
    saving.value = false
  }
}

/* Delete */
async function removeRow(r: KeywordRow) {
  if (!confirm(`#${r.id} 삭제할까요?`)) return
  try {
    await http.delete(`keywords/${r.id}`)
    toastOk('삭제되었습니다.')
    await load(page.value)
  } catch (e:any) {
    const m = e?.detail ?? e?.message ?? 'Delete failed'
    err.value = m
    toastErr(m)
  }
}

/* Export CSV */
function toCsvValue(v:any) { return `"${String(v ?? '').replace(/"/g,'""')}"` }
async function exportCsv() {
  exporting.value = true
  try {
    const items: KeywordRow[] = []
    let p = 1
    while (true) {
      const params = new URLSearchParams()
      params.set('group_name', groupName.value)
      if (q.value) params.set('q', q.value)
      if (activeFilter.value !== 'all') params.set('active', String(activeFilter.value === 'true'))
      params.set('page', String(p))
      params.set('size', String(size.value))
      const r = await http.get<{ total:number; page:number; size:number; items:KeywordRow[] }>(`keywords?${params}`)
      items.push(...(r.items || []))
      const last = Math.max(1, Math.ceil((r.total || 0) / (r.size || 1)))
      if (p >= last) break
      p++
    }

    const header = ['group_name','k','v','weight','is_active','created_at']
    const lines = [header.join(',')]
    for (const r of items) {
      lines.push([
        toCsvValue(r.group_name),
        toCsvValue(r.k),
        toCsvValue(r.v),
        toCsvValue(r.weight),
        toCsvValue(r.is_active ? 'true' : 'false'),
        toCsvValue(r.created_at || ''),
      ].join(','))
    }
    const blob = new Blob([`\uFEFF${lines.join('\n')}\n`], { type:'text/csv' }) // BOM 추가(엑셀 호환)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `keywords_${groupName.value}.csv`; a.click()
    URL.revokeObjectURL(url)
    toastOk('CSV 내보내기 완료')
  } catch (e:any) {
    const m = e?.detail ?? e?.message ?? 'Export failed'
    err.value = m
    toastErr(m)
  } finally {
    exporting.value = false
  }
}

/* Import CSV */
const dlgImport = ref(false)
const importRef = ref<HTMLInputElement|null>(null)
const importMsg = ref<string | null>(null)
const importErr = ref<string | null>(null)
function openImport() {
  importMsg.value = null; importErr.value = null
  if (importRef.value) importRef.value.value = ''
  dlgImport.value = true
}

async function doImport() {
  const el = importRef.value
  if (!el || !el.files || !el.files[0]) { importErr.value = 'CSV 파일 선택'; return }
  importMsg.value = null; importErr.value = null
  importing.value = true

  try {
    // BOM 제거 포함
    let text = await el.files[0].text()
    text = text.replace(/^\uFEFF/, '')
    const lines = text.split(/\r?\n/).map(s => s.trim()).filter(Boolean)
    if (!lines.length) throw new Error('빈 파일')

    const cols = lines[0].split(',').map(s => s.trim().replace(/^"|"$/g,'').toLowerCase())
    const hasHeader = ['group_name','k','v','weight','is_active'].every(h => cols.includes(h))
    let start = hasHeader ? 1 : 0

    let ok = 0, fail = 0
    for (let i = start; i < lines.length; i++) {
      const raw = splitCsvLine(lines[i])
      const obj = mapCsvRow(raw, hasHeader ? cols : null)
      const body = {
        group_name: obj.group_name || groupName.value,
        k: obj.k || '',
        v: obj.v || '',
        weight: Number(obj.weight || 0),
        is_active: String(obj.is_active||'').toLowerCase() !== 'false',
      }
      if (!body.k) { fail++; continue }
      try { await http.post('keywords', body); ok++ } catch { fail++ }
    }
    importMsg.value = `완료: ${ok}건, 실패: ${fail}건`
    toastOk(importMsg.value)
    await load(1)
  } catch (e:any) {
    importErr.value = e?.message ?? 'Import failed'
    toastErr(importErr.value)
  } finally {
    importing.value = false
  }
}

// CSV 라인 split(따옴표 내부 콤마 보존)
function splitCsvLine(line:string) {
  const out:string[] = []
  let cur = '', inQ = false
  for (let i=0; i<line.length; i++) {
    const ch = line[i]
    if (ch === '"') {
      if (inQ && line[i+1] === '"') { cur += '"'; i++ } // "" -> "
      else inQ = !inQ
    } else if (ch === ',' && !inQ) {
      out.push(cur); cur = ''
    } else {
      cur += ch
    }
  }
  out.push(cur)
  return out.map(s => s.replace(/^"|"$/g,''))
}

// 헤더 매핑 또는 기본 순서(k,v,weight,is_active,group_name)
function mapCsvRow(arr:string[], header:string[] | null) {
  const o:any = {}
  if (header) {
    header.forEach((h,idx)=> o[h] = arr[idx])
  } else {
    o.k = arr[0] || ''
    o.v = arr[1] || ''
    o.weight = arr[2] || '0'
    o.is_active = arr[3] || 'true'
    o.group_name = arr[4] || ''
  }
  return o
}

/* ========= Analyze Test ========= */
const testGroup = ref('sales.tag.alias')
const sampleNote = ref('예) 바다 전망 룸온리, 조식 2인 포함, 현장결제(POA). 메모에 다양한 약어/표기가 섞여 있어요.')
const testErr = ref<string | null>(null)
const useRegexWordBoundary = ref(true)
const useCaseInsensitive = ref(true)

const rules = ref<KeywordRow[]>([])
async function reloadRules() {
  testErr.value = null
  try {
    const params = new URLSearchParams()
    params.set('group_name', testGroup.value)
    params.set('active', 'true')
    params.set('page', '1')
    params.set('size', '2000')
    const r = await http.get<{ items:KeywordRow[] }>(`keywords?${params}`)
    rules.value = r.items || []
  } catch (e:any) {
    const m = e?.detail ?? e?.message ?? 'Rules load failed'
    testErr.value = m
    rules.value = []
    toastErr(m)
  }
}
onMounted(reloadRules)

const result = ref<{ tags: {code:string; score:number}[], matches: {id:number;k:string;v:string;weight:number;hit:string}[] }>({
  tags: [],
  matches: [],
})

function escapeRegExp(s:string) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') }

function compileTokens(k:string) {
  // 정규식 형상 판단
  const looksRegex = /[.*+?^${}()|[\]\\]/.test(k) || k.startsWith('^')
  if (looksRegex) {
    const flags = useCaseInsensitive.value ? 'i' : ''
    try { return [new RegExp(k, flags)] } catch { /* fallback */ }
  }
  // 파이프 구분 토큰
  const parts = k.split('|').map(s=>s.trim()).filter(Boolean)
  const flags = useCaseInsensitive.value ? 'i' : ''
  return parts.map(p => {
    const body = useRegexWordBoundary.value ? `\\b${escapeRegExp(p)}\\b` : escapeRegExp(p)
    return new RegExp(body, flags)
  })
}

function analyze() {
  testErr.value = null
  const text = sampleNote.value || ''
  const mlist: {id:number;k:string;v:string;weight:number;hit:string}[] = []
  const score: Record<string, number> = {}

  for (const r of rules.value) {
    const regs = compileTokens(r.k || '')
    let hit = ''
    for (const rg of regs) {
      const found = text.match(rg)
      if (found) { hit = found[0] || String(found); break }
    }
    if (hit) {
      mlist.push({ id:r.id, k:r.k, v:r.v, weight:r.weight, hit })
      score[r.v] = (score[r.v] || 0) + (Number(r.weight) || 0) || 1
    }
  }

  const tags = Object.entries(score)
    .map(([code, s]) => ({ code, score: s }))
    .sort((a,b)=> b.score - a.score)

  result.value = { tags, matches: mlist }
}
</script>
