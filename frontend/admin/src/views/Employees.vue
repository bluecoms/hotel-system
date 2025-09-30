<template>
  <v-container fluid>
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center justify-space-between">
        <div class="text-h6">사원 관리</div>
        <div class="d-flex" style="gap: 8px;">
          <v-text-field
            v-model="q"
            density="compact"
            placeholder="검색: 사번/이름/부서/직책"
            hide-details
            clearable
            @keyup.enter="onSearch"
            style="min-width: 280px;"
          />
          <v-btn variant="tonal" @click="onSearch">검색</v-btn>
          <v-btn variant="text" @click="downloadTpl" prepend-icon="mdi-download">템플릿</v-btn>
        </div>
      </v-card-title>

      <v-card-text>
        <div class="d-flex flex-wrap align-center" style="gap: 12px;">
          <v-file-input
            v-model="file"
            show-size
            density="comfortable"
            placeholder="사원명부 CSV / XLS / XLSX / (HTML표) 파일 선택"
            accept=".csv,.xlsx,.xls,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel"
            prepend-icon="mdi-file-upload-outline"
            style="max-width: 460px;"
            hide-details
          />
          <v-btn :loading="uploading" :disabled="!file" @click="doImport" color="primary">업로드</v-btn>
          <span v-if="importResult" class="text-medium-emphasis">
            처리결과: 생성 {{ importResult.created }} / 갱신 {{ importResult.updated }}
          </span>
          <v-spacer />
          <div class="text-caption text-medium-emphasis">
            총 {{ total }}건
          </div>
        </div>
      </v-card-text>

      <!-- Vuetify 3: v-model:page / v-model:items-per-page 사용 권장 -->
      <v-data-table
        :headers="headers"
        :items="items"
        :loading="loading"
        v-model:page="page"
        v-model:items-per-page="size"
        :items-length="total"
        class="elevation-1"
      >
        <!-- actions 슬롯: item.raw 가 실제 행 데이터 -->
        <template #item.actions="{ item }">
          <v-btn size="small" variant="text" @click="openDetail(item)">보기/수정</v-btn>
        </template>

        <template #loading>
          <div class="d-flex align-center justify-center py-6">
            <v-progress-circular indeterminate />
          </div>
        </template>

        <template #no-data>
          <div class="text-medium-emphasis py-6">데이터가 없습니다.</div>
        </template>
      </v-data-table>
    </v-card>

    <!-- HR 카드 다이얼로그 -->
    <v-dialog v-model="dlg" max-width="900">
      <v-card>
        <v-card-title class="text-h6 d-flex align-center justify-space-between">
          <div>
            HR 카드 • {{ form.name || '-' }} <span v-if="form.emp_no">({{ form.emp_no }})</span>
          </div>
          <div class="text-caption text-medium-emphasis">
            ID: {{ form.id ?? '-' }}
          </div>
        </v-card-title>

        <v-card-text>
          <div class="grid grid-cols-2 gap-3">
            <v-text-field v-model="form.name" label="이름" />
            <v-text-field v-model="form.emp_no" label="사번" readonly />
            <v-text-field v-model="form.dept" label="부서" />
            <v-text-field v-model="form.title" label="직책" />
            <v-text-field v-model="form.position" label="직위" />
            <v-text-field v-model="form.rank" label="직급(옵션)" />

            <v-text-field v-model="form.phone" label="연락처" />
            <v-text-field v-model="form.email" label="이메일" />
            <v-text-field v-model="form.address" label="주소" class="col-span-2" />

            <v-text-field v-model="form.hire_date" label="입사일" type="date" />
            <v-text-field v-model="form.leave_date" label="퇴사일" type="date" />

            <v-text-field v-model="form.rrn_mask" label="주민번호(마스킹)">
              <template #append>
                <v-btn size="x-small" variant="text" @click="form.rrn_mask = maskRRN(form.rrn_mask || '')">마스킹</v-btn>
              </template>
            </v-text-field>
            <v-text-field v-model="form.bank_name" label="은행명" />
            <v-text-field v-model="form.account_mask" label="계좌(마스킹)">
              <template #append>
                <v-btn
                  size="x-small"
                  variant="text"
                  @click="(() => { const r = maskAcct(form.account_mask || ''); form.account_mask = r.mask; form.account_last4 = r.last4 })()"
                >
                  마스킹
                </v-btn>
              </template>
            </v-text-field>
            <v-text-field v-model="form.account_last4" label="계좌 마지막 4자리" />

            <v-textarea v-model="form.memo" label="메모/히스토리" class="col-span-2" rows="4" />
          </div>

          <v-divider class="my-4" />

          <!-- 앱 계정 생성/매핑 -->
          <div class="d-flex align-center flex-wrap" style="gap: 8px;">
            <v-text-field v-model="newUserEmail" label="새 계정 이메일" style="max-width: 320px;" />
            <v-switch v-model="newUserActive" label="활성화" hide-details density="compact" inset />
            <v-btn :loading="creatingUser" @click="createUserFromEmployee" color="secondary">
              계정 생성+매핑
            </v-btn>
          </div>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="dlg=false">닫기</v-btn>
          <v-btn color="primary" :loading="saving" @click="save">저장</v-btn>
          <v-btn variant="text" @click="openPrev">이전</v-btn>
          <v-btn variant="text" @click="openNext">다음</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snack.show" :timeout="2500">
      {{ snack.text }}
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

type EmpItem = { id:number; emp_no:string; name:string; dept:string; title:string }
type EmpDetail = {
  id?: number
  emp_no: string
  name: string
  dept: string
  title: string
  position?: string
  rank?: string
  phone?: string
  email?: string
  address?: string
  hire_date?: string | null
  leave_date?: string | null
  rrn_mask?: string
  bank_name?: string
  account_mask?: string
  account_last4?: string
  memo?: string
}

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const q = ref<string>((route.query.q as string) || '')
const page = ref<number>(Number(route.query.page || 1))
const size = ref<number>(Number(route.query.size || 20))
const total = ref(0)
const items = ref<EmpItem[]>([])
const loading = ref(false)

const uploading = ref(false)
const file = ref<File | null>(null)
const importResult = ref<{ created: number; updated: number } | null>(null)

const dlg = ref(false)
const saving = ref(false)
const form = ref<EmpDetail>({
  emp_no: '',
  name: '',
  dept: '',
  title: '',
})

const snack = ref({ show: false, text: '' })

const headers = [
  { title: 'ID',     key: 'id',     sortable: true },
  { title: '사번',   key: 'emp_no', sortable: true },
  { title: '이름',   key: 'name',   sortable: true },
  { title: '부서',   key: 'dept',   sortable: true },
  { title: '직책',   key: 'title',  sortable: true },
  { title: '작업',   key: 'actions', sortable: false },
]

// 라우터 쿼리와 동기화
watch([q, page, size], () => {
  const query = { ...route.query, q: q.value || undefined, page: String(page.value), size: String(size.value) }
  router.replace({ query })
})

// (선택) JSON 강제 fetch 래퍼 — HTML 에러문서 방지
async function fetchJson(input: RequestInfo, init?: RequestInit) {
  const resp = await fetch(input, init)
  const ct = (resp.headers.get('content-type') || '').toLowerCase()
  const text = await resp.text()
  if (!resp.ok) throw new Error(text || `HTTP ${resp.status}`)
  if (!ct.includes('application/json')) throw new Error(`Non-JSON response: ${text.slice(0, 120).replace(/\s+/g,' ')}`)
  try { return JSON.parse(text) } catch { throw new Error('Invalid JSON') }
}

function authHeaders() {
  const h: Record<string, string> = {}
  // 운영에서 내부토큰 쓰면 VITE_INTERNAL_TOKEN로 주입
  // @ts-ignore
  if (import.meta.env.VITE_INTERNAL_TOKEN) {
    // @ts-ignore
    h['X-Internal-Token'] = import.meta.env.VITE_INTERNAL_TOKEN as string
  }
  return h
}

async function load() {
  loading.value = true
  try {
    const params = new URLSearchParams({
      q: q.value || '',
      page: String(page.value),
      size: String(size.value),
    })
    const data = await fetchJson(`/api/employees?${params.toString()}`, {
      headers: { ...authHeaders() },
    })
    total.value = data.total
    items.value = data.items
  } catch (e: any) {
    snack.value = { show: true, text: `목록 조회 실패: ${e?.message || e}` }
  } finally {
    loading.value = false
  }
}

function onSearch() {
  page.value = 1
  load()
}

async function downloadTpl() {
  try {
    const r = await fetch('/api/templates/employees.csv', { headers: { ...authHeaders() } })
    if (!r.ok) throw new Error(await r.text())
    const blob = await r.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'employees_template.csv'; a.click()
    URL.revokeObjectURL(url)
  } catch (e:any) {
    snack.value = { show: true, text: `템플릿 다운로드 실패: ${e?.message||e}` }
  }
}

async function doImport() {
  if (!file.value) return
  const fd = new FormData()
  fd.append('file', file.value)
  uploading.value = true
  try {
    const data = await fetchJson('/api/employees/import', {
      method: 'POST',
      headers: { ...authHeaders() }, // FormData는 Content-Type 자동
      body: fd,
    })
    importResult.value = { created: data.created ?? 0, updated: data.updated ?? 0 }
    snack.value = { show: true, text: `업로드 완료: 생성 ${importResult.value.created} / 갱신 ${importResult.value.updated}` }
    await load()
  } catch (e: any) {
    snack.value = { show: true, text: `업로드 실패: ${e?.message || e}` }
  } finally {
    uploading.value = false
    file.value = null // 같은 파일 재업로드 가능
  }
}

async function openDetail(row: any) {
  // Vuetify v-data-table 래퍼/원본 모두 대응
  const rid = row?.id ?? row?.raw?.id
  if (!rid) {
    snack.value = { show: true, text: '상세 조회 실패: 잘못된 항목입니다.' }
    return
  }
  try {
    const resp = await fetch(`/api/employees/${rid}`, { headers: { ...authHeaders() } })
    if (!resp.ok) throw new Error(await resp.text() || '상세 조회 실패')
    const data = await resp.json()
    form.value = { ...data, hire_date: data.hire_date || '', leave_date: data.leave_date || '' }
    dlg.value = true
  } catch (e:any) {
    snack.value = { show: true, text: `상세 조회 실패: ${e?.message || e}` }
  }
}

function normalizeForSave(src: EmpDetail) {
  const toNull = (v: any) => (v === '' ? null : v)
  const out: any = { ...src }
  delete out.id
  delete out.emp_no  // 사번은 읽기전용
  out.hire_date = toNull(out.hire_date)
  out.leave_date = toNull(out.leave_date)
  return out
}

async function save() {
  if (!form.value?.id) return
  saving.value = true
  try {
    const payload = normalizeForSave(form.value)
    await fetchJson(`/api/employees/${form.value.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload),
    })
    snack.value = { show: true, text: '저장되었습니다.' }
    dlg.value = false
    await load()
  } catch (e: any) {
    snack.value = { show: true, text: `저장 실패: ${e?.message || e}` }
  } finally {
    saving.value = false
  }
}

// 다음/이전 + Ctrl/Cmd+S 저장
function openNext() {
  const idx = items.value.findIndex(i => i.id === form.value.id)
  if (idx >= 0 && idx + 1 < items.value.length) openDetail(items.value[idx + 1])
}
function openPrev() {
  const idx = items.value.findIndex(i => i.id === form.value.id)
  if (idx > 0) openDetail(items.value[idx - 1])
}
function onKey(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
    e.preventDefault(); save()
  }
}

const newUserEmail = ref('')
const newUserActive = ref(true)
const creatingUser = ref(false)
async function createUserFromEmployee() {
  if (!form.value?.emp_no || !newUserEmail.value) {
    snack.value = { show: true, text: '사번/이메일을 확인하세요.' }
    return
  }
  creatingUser.value = true
  try {
    const res = await fetchJson('/api/users/from-employee', {
      method: 'POST',
      headers: { 'Content-Type':'application/json', ...authHeaders() },
      body: JSON.stringify({ emp_no: form.value.emp_no, email: newUserEmail.value, is_active: newUserActive.value })
    })
    snack.value = { show: true, text: `계정 생성 완료 (user_id=${res.user_id})` }
  } catch (e:any) {
    snack.value = { show: true, text: `계정 생성 실패: ${e?.message||e}` }
  } finally {
    creatingUser.value = false
  }
}

// 마스킹 헬퍼
function maskRRN(s: string) {
  const m = s.replace(/[^\d\-*]/g,'').match(/(\d{6})[\-]?\s*([1-4])/)
  return m ? `${m[1]}-${m[2]}**` : ''
}
function maskAcct(s: string) {
  const digits = s.replace(/[^\d]/g,'')
  const last4 = digits.slice(-4)
  return { mask: `***-***-${last4}`, last4 }
}

onMounted(async () => {
  // 로그인/역할 부트스트랩 (dev에선 /me 허용이라 우회됨)
  if (!auth.user) {
    try { await auth.bootstrap() } catch {}
  }
  window.addEventListener('keydown', onKey)
  await load()
})
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey)
})
</script>

<style scoped>
.grid { display: grid; }
.grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.gap-3 { gap: 12px; }
.col-span-2 { grid-column: span 2 / span 2; }
</style>
