<template>
  <v-container fluid class="py-6 page-shell">
    <div class="brand-subbar mb-5 d-flex align-center justify-space-between">
      <div class="d-flex align-center gap10">
        <v-icon icon="mdi-shield-account-outline" color="primary" size="22" />
        <div>
          <h2 class="text-h6 font-weight-bold mb-0">역할별 화면 접근 권한</h2>
          <div class="text-caption text-grey-darken-1">Route별 Role-Access 레벨 관리</div>
        </div>
      </div>

      <div class="d-flex align-center gap8">
        <v-btn color="primary" variant="flat" prepend-icon="mdi-plus" @click="openAdd">
          새 권한 추가
        </v-btn>
        <v-btn variant="outlined" color="grey" prepend-icon="mdi-refresh" @click="reload" :loading="loading">
          새로고침
        </v-btn>
      </div>
    </div>

    <div class="brand-panel d-flex flex-wrap align-center gap8 mb-4 pa-3">
      <v-text-field
        v-model="q"
        prepend-inner-icon="mdi-magnify"
        label="검색 (Route / 역할)"
        hide-details
        density="comfortable"
        class="minw-260"
      />
      <v-select
        v-model="filterRole"
        :items="roleOptions"
        label="역할"
        clearable
        density="comfortable"
        hide-details
        style="max-width:160px"
      />
      <v-select
        v-model="filterLevel"
        :items="levelOptions"
        label="레벨"
        clearable
        density="comfortable"
        hide-details
        style="max-width:160px"
      />
    </div>

    <v-card v-if="selected.length" class="pa-3 mb-4" variant="outlined">
      <div class="d-flex align-center justify-space-between flex-wrap gap8">
        <div class="text-body-2">
          선택됨: <b>{{ selected.length }}</b>건
        </div>
        <div class="d-flex gap8 align-center">
          <v-select
            v-model="bulkLevel"
            :items="levelOptions"
            label="레벨 변경"
            density="compact"
            hide-details
            style="width:140px"
          />
          <v-btn
            color="primary"
            variant="tonal"
            size="small"
            :disabled="!bulkLevel"
            @click="bulkApplyLevel"
          >적용</v-btn>
          <v-btn
            color="error"
            variant="tonal"
            size="small"
            @click="bulkRemove"
          >삭제</v-btn>
        </div>
      </div>
    </v-card>

    <v-data-table
      :headers="headers"
      :items="filtered"
      :loading="loading"
      :items-per-page="20"
      class="rounded-xl elevation-1"
      show-select
      v-model="selected"
      density="comfortable"
      fixed-header
      hover
    >
      <template #loading>
        <div class="text-center pa-6">
          <v-progress-linear indeterminate color="primary" class="mb-2" />
          <div class="text-caption">불러오는 중…</div>
        </div>
      </template>

      <template #no-data>
        <v-alert type="info" variant="tonal" density="comfortable">데이터가 없습니다.</v-alert>
      </template>

      <template #item.role_code="{ item }">
        <v-chip size="small" color="grey-lighten-3" class="font-mono">{{ item.role_code }}</v-chip>
      </template>

      <template #item.route_name="{ item }">
        <div class="font-mono text-body-2">{{ item.route_name }}</div>
        <div class="text-caption text-grey-darken-1">{{ prettyRoute(item.route_name) }}</div>
      </template>

      <template #item.access_level="{ item }">
        <v-chip
          size="small"
          label
          :color="colorForLevel(item.access_level)"
          class="text-white cursor-pointer"
          @click="cycleLevel(item)"
        >
          {{ item.access_level }}
        </v-chip>
      </template>

      <template #item.actions="{ item }">
        <v-btn icon="mdi-content-copy" size="small" variant="text" color="primary" @click="duplicate(item)" />
        <v-btn icon="mdi-delete-outline" size="small" variant="text" color="error" @click="remove(item)" />
      </template>
    </v-data-table>

    <v-expansion-panels class="mt-6">
      <v-expansion-panel>
        <v-expansion-panel-title>고급 도구 (CSV 가져오기 / 내보내기)</v-expansion-panel-title>
        <v-expansion-panel-text>
          <div class="d-flex align-center gap8 mb-3">
            <v-btn color="primary" variant="outlined" prepend-icon="mdi-file-export" @click="exportCsv">CSV 내보내기</v-btn>
            <v-btn color="primary" variant="flat" prepend-icon="mdi-file-import" @click="importCsv" :loading="importBusy">
              CSV 가져오기
            </v-btn>
          </div>
          <v-textarea
            v-model="csvText"
            label="CSV 붙여넣기 (role_code,route_name,access_level)"
            rows="6"
            variant="outlined"
            placeholder="role_code,route_name,access_level&#10;ADMIN,dashboard-kpi,view"
          />
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>

    <v-dialog v-model="showForm" max-width="520">
      <v-card>
        <v-card-title class="text-subtitle-1">{{ formMode === 'add' ? '권한 추가' : '권한 수정' }}</v-card-title>
        <v-card-text>
          <v-form ref="formRef" @submit.prevent="submitForm">
            <v-select v-model="form.role_code" :items="roleOptions" label="역할" :disabled="formMode==='edit'" />
            <v-text-field v-model.trim="form.route_name" label="Route Name (예: dashboard-kpi)" :disabled="formMode==='edit'" />
            <v-select v-model="form.access_level" :items="levelOptions" label="접근 레벨" />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showForm=false">취소</v-btn>
          <v-btn color="primary" :loading="saving" @click="submitForm">{{ formMode==='add'?'추가':'저장' }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import http from '@/services/http'
import { useToast } from '@/ui/composables/useToast'
import { useConfirm } from '@/ui/composables/useConfirm'

type Level = 'none' | 'view' | 'edit' | 'admin'
type Rec = { role_code: string; route_name: string; access_level: Level }
type FormMode = 'add' | 'edit'

const toast = useToast()
const confirmApi = useConfirm()

const loading = ref(false)
const saving = ref(false)
const items = ref<Rec[]>([])
const selected = ref<Rec[]>([])
const q = ref('')
const filterRole = ref<string | null>(null)
const filterLevel = ref<Level | null>(null)
const bulkLevel = ref<Level | null>(null)
const showForm = ref(false)
const formMode = ref<FormMode>('add')
const form = ref<Rec>({ role_code: 'ADMIN', route_name: '', access_level: 'view' })
const formRef = ref()
const csvText = ref('')
const importBusy = ref(false)

const headers = [
  { title: 'Role', key: 'role_code', minWidth: 100 },
  { title: 'Route', key: 'route_name', minWidth: 200 },
  { title: 'Level', key: 'access_level', width: 100 },
  { title: '', key: 'actions', width: 100, align: 'end' },
]

const roleOptions = ['ADMIN', 'SUPERADMIN', 'USER'].map(r => ({ title: r, value: r }))
const levelOptions: Level[] = ['none', 'view', 'edit', 'admin']

function prettyRoute(r: string) {
  const map: Record<string, string> = {
    'dashboard-kpi': '대시보드 / KPI',
    'closing-calendar': '마감 캘린더',
    'users-list': '사용자 관리',
    'role-access': '권한 설정',
  }
  return map[r] || r.replace(/-/g, ' ')
}

const filtered = computed(() => {
  const qq = q.value.trim().toLowerCase()
  return items.value.filter(it => {
    if (filterRole.value && it.role_code !== filterRole.value) return false
    if (filterLevel.value && it.access_level !== filterLevel.value) return false
    if (!qq) return true
    return `${it.role_code} ${it.route_name}`.toLowerCase().includes(qq)
  })
})

function colorForLevel(level: Level) {
  switch (level) {
    case 'admin': return 'red-darken-2'
    case 'edit': return 'blue'
    case 'view': return 'green'
    default: return 'grey-lighten-2'
  }
}
function nextLevel(cur: Level): Level {
  const order: Level[] = ['none', 'view', 'edit', 'admin']
  return order[(order.indexOf(cur) + 1) % order.length]
}
async function cycleLevel(item: Rec) {
  const next = nextLevel(item.access_level)
  try {
    await upsert({ ...item, access_level: next })
    item.access_level = next
    toast.success(`권한이 ${next}로 변경되었습니다.`)
  } catch { toast.error('변경 실패') }
}

async function reload() {
  loading.value = true
  try {
    const r:any = await http.get('/users/roles/access')
    items.value = Array.isArray(r) ? r : (r.items ?? [])
  } finally { loading.value = false }
}

async function upsert(rec: Rec) {
  await http.put('/users/roles/access', rec)
}
async function remove(item: Rec) {
  const ok = await confirmApi.ask(`${item.role_code} / ${item.route_name} 삭제?`)
  if (!ok) return
  await http.delete(`/users/roles/access?role=${item.role_code}&route=${item.route_name}`)
  items.value = items.value.filter(x => !(x.role_code===item.role_code && x.route_name===item.route_name))
  toast.info('삭제되었습니다.')
}
function openAdd(seed?: Partial<Rec>) {
  formMode.value = 'add'
  form.value = { role_code: seed?.role_code || 'ADMIN', route_name: seed?.route_name || '', access_level: seed?.access_level || 'view' }
  showForm.value = true
}
function duplicate(item: Rec) { openAdd({ ...item }) }
async function submitForm() {
  const payload = { ...form.value }
  saving.value = true
  try {
    await upsert(payload)
    const idx = items.value.findIndex(x => x.role_code===payload.role_code && x.route_name===payload.route_name)
    if (idx >= 0) items.value[idx] = payload; else items.value.unshift(payload)
    toast.success('저장되었습니다.')
    showForm.value = false
  } finally { saving.value = false }
}
async function bulkRemove() {
  for (const item of selected.value) await remove(item)
  selected.value = []
}
async function bulkApplyLevel() {
  if (!bulkLevel.value) return
  for (const item of selected.value) await upsert({ ...item, access_level: bulkLevel.value })
  toast.success(`레벨 ${bulkLevel.value}로 일괄 변경`)
  reload()
}
function exportCsv() {
  const header = 'role_code,route_name,access_level'
  const rows = filtered.value.map(r => [r.role_code, r.route_name, r.access_level].join(',')).join('\n')
  const blob = new Blob([header+'\n'+rows], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href=url; a.download='role_access.csv'; a.click(); URL.revokeObjectURL(url)
}
async function importCsv() {
  const lines = csvText.value.split(/\r?\n/).filter(Boolean)
  for (const ln of lines.slice(1)) {
    const [role_code, route_name, access_level] = ln.split(',').map(x=>x.trim())
    if (role_code && route_name && access_level) await upsert({ role_code, route_name, access_level: access_level as Level })
  }
  toast.success('CSV 가져오기 완료')
  reload()
}
onMounted(reload)
</script>

<style scoped>
.brand-subbar {
  border: 1px solid var(--color-line);
  background: var(--color-surface);
  border-radius: 12px;
  padding: 12px 20px;
  box-shadow: var(--shadow-sm);
}
.cursor-pointer { cursor: pointer; }
</style>
