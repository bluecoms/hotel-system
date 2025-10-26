<!-- ============================================================================
# File      : src/views/Admin/RoleAccess.vue
# Version   : 2025.11-08 · v4.7 (MenuTree Sync · Dept/Lead/Member 완전정합)
# Purpose   : Hotel Admin — 권한 관리 (부서별 접근권한 + 팀장/팀원 관리)
# ----------------------------------------------------------------------------
# ✅ 변경 요약
#   • 메뉴트리(router/menu.ts) 기반 라벨/루트 자동 정렬
#   • 부서별 팀장/팀원 — 각 부서 employees.dept 기준 필터링
#   • 팀원 없음 시 “소속 팀원이 없습니다.” 표시
#   • 부서 칩 색상 유지 (roles 탭에도 동일 표시)
# ========================================================================= -->
<template>
  <v-container fluid class="py-6 page-shell">
    <!-- 상단 헤더 -->
    <v-card flat class="pa-4 mb-4">
      <h2 class="text-h6 font-weight-bold mb-1">권한 관리</h2>
      <p class="text-body-2 text-medium-emphasis">부서별 접근권한 및 팀장/팀원 관리</p>

      <v-tabs v-model="activeTab" class="mt-2" density="compact">
        <v-tab value="roles">부서별 접근권한</v-tab>
        <v-tab value="leads">부서별 팀장·팀원 관리</v-tab>
      </v-tabs>
    </v-card>

    <!-- 메인 탭 -->
    <v-window v-model="activeTab" class="rounded-xl elevation-1">

      <!-- ▣ 부서별 접근권한 탭 -->
      <v-window-item value="roles">
        <v-card flat class="pa-4 rounded-xl elevation-1">
          <!-- 부서 칩 팔레트 -->
          <div class="d-flex flex-wrap gap-2 mb-4">
            <v-chip
              v-for="(label, code) in deptLabels"
              :key="code"
              :color="colorMap[code] || '#E5E7EB'"
              text-color="black"
              size="small"
              variant="flat"
            >
              {{ label }}
            </v-chip>
          </div>

          <!-- 접근권한 테이블 -->
          <v-data-table
            :headers="headers"
            :items="rows"
            :loading="loading"
            class="elevation-1 rounded-xl access-table"
            item-value="route_name"
          >
            <template #item.access_scope="{ item }">
              <div class="access-cell">
                <v-select
                  :items="deptOptions"
                  v-model="item.access_scope"
                  density="compact"
                  variant="outlined"
                  multiple
                  hide-details
                  class="role-chip"
                  :style="{ backgroundColor: item.access_scope.length ? colorMap[item.access_scope[0]] || '#E0E0E0' : '#F3F4F6' }"
                  @update:model-value="updateAccess(item)"
                />
              </div>
            </template>
          </v-data-table>
        </v-card>
      </v-window-item>

      <!-- ▣ 부서별 팀장·팀원 관리 탭 -->
      <v-window-item value="leads">
        <v-card flat class="pa-4 rounded-xl elevation-1">
          <v-row class="dept-lead-cards">
            <v-col
              v-for="lead in deptLeads"
              :key="lead.dept_code"
              cols="12"
              md="4"
              sm="6"
            >
              <v-card class="lead-card text-center">
                <h4 class="font-weight-bold mb-1">
                  {{ deptLabels[lead.dept_code] || lead.dept_code }}
                </h4>
                <p class="text-caption text-medium-emphasis mb-1">
                  {{ lead.lead_email || '이메일 없음' }}
                </p>

                <!-- 팀장 선택 -->
                <v-select
                  :items="employeeOptions.filter(e => e.dept === lead.dept_code)"
                  v-model="lead.emp_id"
                  label="팀장 선택"
                  item-title="title"
                  item-value="value"
                  density="comfortable"
                  variant="outlined"
                  hide-details
                  class="mb-2"
                  @update:model-value="saveLead(lead)"
                />

                <v-chip color="primary" variant="flat" size="x-small" class="mt-1">
                  현재 팀장: {{ lead.lead_name || '미지정' }}
                </v-chip>

                <v-divider class="my-3" />

                <!-- 팀원 목록 -->
                <div class="text-body-2 font-weight-medium mb-1">팀원 목록</div>
                <div v-if="members[lead.dept_code]?.length">
                  <v-chip
                    v-for="m in members[lead.dept_code]"
                    :key="m.id"
                    size="x-small"
                    class="ma-1"
                    color="#E0E7FF"
                  >
                    {{ m.name }}
                  </v-chip>
                </div>
                <div v-else class="text-caption text-medium-emphasis">
                  소속 팀원이 없습니다.
                </div>
              </v-card>
            </v-col>
          </v-row>
        </v-card>
      </v-window-item>
    </v-window>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import http from '@/services/http'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/ui/composables/useToast'
import menu from '@/router/menu'

const auth = useAuthStore()
const toast = useToast()

const activeTab = ref<'roles' | 'leads'>('roles')
const loading = ref(false)
const loadingLeads = ref(false)
const rows = ref<any[]>([])
const deptLeads = ref<any[]>([])
const members = ref<Record<string, any[]>>({})

// ───────────────────────────────────────────────
// 1️⃣ 부서/색상 로드 (SSOT: master_departments)
// ───────────────────────────────────────────────
const deptLabels = ref<Record<string, string>>({})
const deptOptions = ref<{ title: string; value: string }[]>([])
const colorMap = ref<Record<string, string>>({})
async function loadDepartments() {
  const res = await http.get<{ items?: any[] }>('master/departments')
  const items = res?.items ?? []
  const palette = ['#BFDBFE','#A7F3D0','#FDE68A','#E9D5FF','#C7D2FE','#E5E7EB','#FCA5A5']
  deptLabels.value = { ALL_VIEW: 'ALL 보기', ALL_EDIT: 'ALL 권한' }
  colorMap.value = { ALL_VIEW: '#BFDBFE', ALL_EDIT: '#FECACA' }
  items.forEach((d, i) => {
    deptLabels.value[d.dept_code] = d.dept_name
    colorMap.value[d.dept_code] = palette[i % palette.length]
  })
  deptOptions.value = Object.entries(deptLabels.value).map(([code, name]) => ({ title: name, value: code }))
}

// ───────────────────────────────────────────────
// 2️⃣ 메뉴트리 기반 권한 라벨/순서
// ───────────────────────────────────────────────
type NavItem = { label: string; routeName?: string; children?: NavItem[] }
function flattenMenu(list: NavItem[], acc: { route: string; label: string }[] = []) {
  for (const m of list) {
    if ((m as any).routeName) acc.push({ route: (m as any).routeName as string, label: m.label })
    if (m.children?.length) flattenMenu(m.children as NavItem[], acc)
  }
  return acc
}
const MENU = flattenMenu(menu as unknown as NavItem[])
const headers = [
  { title: 'Label', key: 'label', align: 'start' },
  { title: 'Route', key: 'route_name', align: 'center' },
  { title: '부서별 접근권한', key: 'access_scope', align: 'center' },
]
async function loadAccess() {
  loading.value = true
  const res = await http.get<any[]>('roles/access')
  const byRoute = new Map<string, any>((res || []).map(r => [r.route_name, r]))
  rows.value = MENU.map(m => {
    const r = byRoute.get(m.route)
    return {
      route_name: m.route,
      label: m.label,
      access_scope: r?.access_scope ?? [],
    }
  })
  loading.value = false
}
async function updateAccess(item: any) {
  const payload = { route_name: item.route_name, access_scope: item.access_scope }
  await http.put('roles/access', payload)
  toast.success(`『${item.label}』 권한이 저장되었습니다.`)
}

// ───────────────────────────────────────────────
// 3️⃣ 직원 + 팀원(부서별 분류)
// ───────────────────────────────────────────────
const employeeOptions = ref<{ title: string; value: number; rawName: string; rawEmail: string | null; dept: string }[]>([])
async function loadEmployees() {
  const res = await http.get<{ items?: any[] }>('employees')
  const items = res?.items ?? []
  employeeOptions.value = items.map((e: any) => ({
    title: `${e.name} (${e.email || e.emp_no})`,
    value: e.id,
    rawName: e.name,
    rawEmail: e.email,
    dept: e.dept,
  }))
  // 부서별 팀원 정리
  members.value = {}
  items.forEach(e => {
    if (!members.value[e.dept]) members.value[e.dept] = []
    members.value[e.dept].push(e)
  })
}

// ───────────────────────────────────────────────
// 4️⃣ 팀장 로드/저장
// ───────────────────────────────────────────────
async function loadDeptLeads() {
  loadingLeads.value = true
  const res = await http.get<{ items?: any[] }>('roles/dept-leads')
  const list = Array.isArray(res?.items) ? res.items : []
  const deptCodes = Object.keys(deptLabels.value).filter(k => !k.startsWith('ALL'))
  deptLeads.value = deptCodes.map(code => {
    const found = list.find(l => l.dept_code === code)
    return found || { dept_code: code, lead_name: null, lead_email: null, emp_id: null }
  })
  loadingLeads.value = false
}
async function saveLead(dept: any) {
  const sel = employeeOptions.value.find(o => o.value === dept.emp_id)
  if (sel) {
    dept.lead_name = sel.rawName
    dept.lead_email = sel.rawEmail
  }
  await http.put('roles/dept-leads', { dept_code: dept.dept_code, emp_id: dept.emp_id })
  toast.success(`『${deptLabels.value[dept.dept_code]}』 팀장이 ${dept.lead_name || ''}으로 지정되었습니다.`)
}

// ───────────────────────────────────────────────
// 5️⃣ 라이프사이클
// ───────────────────────────────────────────────
onMounted(async () => {
  await loadDepartments()
  await loadEmployees()
  await loadAccess()
})
watch(activeTab, v => { if (v === 'leads') loadDeptLeads() })
</script>

<style scoped>
.page-shell{background:#f9fafb}
.access-cell{display:flex;justify-content:center;align-items:center;width:100%}
.role-chip{width:220px;border-radius:10px;font-size:.85rem;font-weight:600;text-align:center;box-shadow:0 0 0 1px #d1d5db inset}
.dept-lead-cards{margin-top:8px;justify-content:center;gap:24px}
.lead-card{border-radius:16px;background:linear-gradient(180deg,#fff,#f9fafb);box-shadow:0 4px 14px rgba(0,0,0,.06);padding:16px;max-width:320px;margin:0 auto}
</style>
