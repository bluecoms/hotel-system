<!-- ============================================================================
  File    : src/views/Admin/RoleAccess.vue
  Version : v2025.10-FINAL (Dept Access + Matrix UI Polished · Shields Restored)
  Purpose : Hotel Admin — 부서별 접근권한 + 팀장관리 통합 화면
  ------------------------------------------------------------------------------
  • 개요
      - SUPERADMIN 전용: 조직/업무 권한을 "부서" 단위로 직관 관리
      - 탭1: 부서별 접근권한 (메뉴별 접근 부서/ALL 설정 + 색상 시각화)
      - 탭2: 부서별 팀장 관리 (카드 → 직원 선택 → 팀장 지정)
  • 정책
      - SUPERADMIN: 별도 설정 불필요(항상 전체 접근)
      - ADMIN/USER 역할은 계정 생성 시 고정, 이 화면은 "부서/범위"만 설정
      - ALL(보기) / ALL(권한) 예외 경로 지원 (예: 내 정보/비밀번호 변경 등)
  • 연동 백엔드
      GET    /api/roles/access                     → [{ route_name, access_scope[] }, ...]
      PUT    /api/roles/access                     → { route_name, access_scope[] }
      GET    /api/master/departments               → 부서 목록
      PUT    /api/master/departments/{id}/leader   → 팀장 지정
      GET    /api/employees/by-department/{code}   → 부서별 직원
  • 주의
      - v-data-table headers에 access_scope 열이 반드시 존재해야 행 내 방패(4칸)가 렌더됨
      - 행 색상은 access_scope의 우선순위(ALL_EDIT → ALL_VIEW → 첫 부서코드)로 적용
============================================================================ -->

<template>
  <v-container fluid class="py-6 page-shell">
    <!-- ▣ 헤더 -->
    <div class="brand-subbar mb-5 d-flex align-center justify-space-between">
      <div class="d-flex align-center gap10">
        <v-icon icon="mdi-shield-account-outline" color="primary" size="22" />
        <div>
          <h2 class="text-h6 font-weight-bold mb-0">권한 관리</h2>
          <div class="text-caption text-grey-darken-1">
            부서별 접근권한 및 팀장 지정 통합 관리
          </div>
        </div>
      </div>
      <v-btn
        variant="outlined"
        color="grey"
        prepend-icon="mdi-refresh"
        :loading="loading"
        @click="reloadAll"
      >새로고침</v-btn>
    </div>

    <!-- ▣ 탭 -->
    <v-tabs v-model="activeTab" color="primary" class="mb-6">
      <v-tab value="roles">부서별 접근권한</v-tab>
      <v-tab value="leaders">부서별 팀장 관리</v-tab>
    </v-tabs>

    <v-window v-model="activeTab">
      <!-- ① 부서별 접근권한 -->
      <v-window-item value="roles">
        <v-card flat class="pa-4 rounded-xl elevation-1">
          <div class="text-subtitle-1 font-weight-bold mb-4">메뉴별 부서 접근 설정</div>

          <!-- 색상 식별 코드 -->
          <div class="d-flex align-center flex-wrap gap-3 mb-6">
            <v-chip color="blue"   text-color="white" size="small" label>ALL 보기</v-chip>
            <v-chip color="red"    text-color="white" size="small" label>ALL 권한</v-chip>
            <v-chip color="teal"   text-color="white" size="small" label>FR (프런트)</v-chip>
            <v-chip color="orange" text-color="white" size="small" label>HK (하우스키핑)</v-chip>
            <v-chip color="indigo" text-color="white" size="small" label>AD (경영지원)</v-chip>
            <v-chip color="purple" text-color="white" size="small" label>FM (시설관리)</v-chip>
            <v-chip color="grey"   text-color="white" size="small" label>MG (관리)</v-chip>
          </div>

          <!-- 메뉴 테이블 -->
          <v-data-table
            :headers="menuHeaders"
            :items="menuMatrix"
            :loading="loading"
            class="rounded-xl elevation-1"
            density="compact"
            fixed-header
            hover
            :item-class="rowColorClass"
          >
            <!-- 방패 4칸: 부서/ALL 선택 -->
            <template #item.access_scope="{ item }">
              <div class="d-flex flex-wrap align-center gap-3">
                <template v-for="shield in 4" :key="shield">
                  <v-select
                    v-model="accessMatrix[item.route][shield - 1]"
                    :items="deptOptions"
                    item-title="label"
                    item-value="value"
                    hide-details
                    density="comfortable"
                    style="width:120px"
                    clearable
                    @update:model-value="updateAccess(item)"
                  >
                    <template #prepend-inner>
                      <v-icon size="18" color="primary">mdi-shield</v-icon>
                    </template>
                  </v-select>
                </template>
              </div>
            </template>

            <template #no-data>
              <v-alert type="info" variant="tonal" class="ma-4">
                메뉴 데이터를 불러올 수 없습니다.
              </v-alert>
            </template>
          </v-data-table>
        </v-card>
      </v-window-item>

      <!-- ② 부서별 팀장 관리 -->
      <v-window-item value="leaders">
        <v-card flat class="pa-4 rounded-xl elevation-1">
          <div class="text-subtitle-1 font-weight-bold mb-5">부서별 팀장 관리</div>

          <v-row dense>
            <v-col v-for="dept in departments" :key="dept.id" cols="12" sm="6" md="4" lg="3">
              <v-card
                class="rounded-xl pa-4 hover-elevate cursor-pointer"
                :color="selectedDept?.id === dept.id ? 'primary-lighten-5' : undefined"
                @click="selectDept(dept)"
              >
                <div class="d-flex align-center justify-space-between">
                  <div>
                    <div class="text-subtitle-1 font-weight-bold">{{ dept.dept_name }}</div>
                    <div class="text-caption text-grey-darken-1">{{ dept.dept_code }}</div>
                  </div>
                  <v-icon v-if="selectedDept?.id === dept.id" icon="mdi-check-circle" color="primary" />
                </div>
                <v-divider class="my-2" />
                <div class="text-body-2">
                  <v-icon icon="mdi-account" size="16" class="me-1" />
                  <span v-if="dept.leader_name">현 팀장: <b>{{ dept.leader_name }}</b></span>
                  <span v-else class="text-grey">팀장 미지정</span>
                </div>
              </v-card>
            </v-col>
          </v-row>

          <v-card v-if="selectedDept" class="mt-8 pa-4 rounded-xl elevation-1">
            <div class="d-flex align-center justify-space-between mb-3">
              <div class="text-subtitle-1 font-weight-bold">
                {{ selectedDept.dept_name }} 부서 직원 목록
              </div>
              <v-btn color="primary" variant="flat" prepend-icon="mdi-check" :disabled="!selectedLeaderId" @click="confirmLeader">
                팀장 지정
              </v-btn>
            </div>
            <v-radio-group v-model="selectedLeaderId" class="w-100">
              <v-data-table
                :headers="empHeaders"
                :items="employees"
                :loading="empLoading"
                item-key="id"
                density="comfortable"
                class="rounded-xl elevation-1"
                hover
              >
                <template #item.name="{ item }">
                  <div class="d-flex align-center justify-space-between" style="cursor:pointer">
                    <span>{{ item.name }}</span>
                    <v-radio :value="item.id" />
                  </div>
                </template>

                <template #item.is_leader="{ item }">
                  <v-chip
                    size="small"
                    :color="item.id === selectedDept?.leader_emp_id ? 'primary' : 'grey-lighten-2'"
                    class="text-white"
                  >{{ item.id === selectedDept?.leader_emp_id ? '팀장' : '-' }}</v-chip>
                </template>
              </v-data-table>
            </v-radio-group>
          </v-card>
        </v-card>
      </v-window-item>
    </v-window>
  </v-container>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import http from '@/services/http'
import { useToast } from '@/ui/composables/useToast'
import { useConfirm } from '@/ui/composables/useConfirm'
import menu from '@/router/menu'

const toast = useToast()
const confirmApi = useConfirm()
const loading = ref(false)
const activeTab = ref<'roles' | 'leaders'>('roles')

/* ─────────────────────────────
 * 메뉴별 접근 설정 (방패 4칸 + 색상 행)
 * ────────────────────────────*/
const menuHeaders = [
  { title: 'Label', key: 'label', minWidth: 160 },
  { title: 'Route', key: 'route', minWidth: 180 },
  { title: '부서별 접근권한', key: 'access_scope', sortable: false, minWidth: 520 },
]

const menuMatrix = ref<{ label: string; route: string }[]>([])
const accessMatrix = reactive<Record<string, string[][]>>({})

const deptOptions = [
  { label: 'ALL (보기)',  value: 'ALL_VIEW' },
  { label: 'ALL (권한)',  value: 'ALL_EDIT' },
  { label: 'FR (프런트)', value: 'FR' },
  { label: 'HK (하우스키핑)', value: 'HK' },
  { label: 'AD (경영지원)', value: 'AD' },
  { label: 'FM (시설관리)', value: 'FM' },
  { label: 'MG (관리)', value: 'MG' },
]

const colorMap: Record<string, string> = {
  ALL_VIEW: 'blue-lighten-5',
  ALL_EDIT: 'red-lighten-5',
  FR: 'teal-lighten-5',
  HK: 'orange-lighten-5',
  AD: 'indigo-lighten-5',
  FM: 'purple-lighten-5',
  MG: 'grey-lighten-4',
}

function flattenMenu(list:any[]): any[] {
  const result:any[] = []
  for (const m of list) {
    if (m.children) result.push(...flattenMenu(m.children))
    else if (m.routeName) result.push({ label: m.label, route: m.routeName })
  }
  return result
}

async function loadMenuMatrix() {
  menuMatrix.value = flattenMenu(menu)

  // 초기 방패 4칸 배열 준비
  for (const m of menuMatrix.value) accessMatrix[m.route] = [[], [], [], []]

  // 기존 저장된 scope 로드
  const res:any = await http.get('/roles/access')
  const existing = Array.isArray(res) ? res : (res.items ?? [])
  for (const r of existing) {
    if (!accessMatrix[r.route_name]) accessMatrix[r.route_name] = [[], [], [], []]
    // 단일 리스트를 1번 방패에 기본 주입 (복수 방패 선택 시 updateAccess에서 병합 저장)
    accessMatrix[r.route_name][0] = (r.access_scope || []).slice(0)
  }
}

async function updateAccess(item:any) {
  // 4칸 데이터 병합 → 중복 제거 → 저장
  const merged = [...new Set(accessMatrix[item.route].flat().filter(Boolean))]
  await http.put('/roles/access', { route_name: item.route, access_scope: merged })
  toast.success(`${item.label} 저장됨 (${merged.join(', ')})`)
}

function rowColorClass(item:any) {
  const scopes = [...new Set(accessMatrix[item.route].flat())]
  if (scopes.includes('ALL_EDIT')) return 'row-all-edit'
  if (scopes.includes('ALL_VIEW')) return 'row-all-view'
  const first = scopes[0]
  return first ? `row-${first.toLowerCase()}` : ''
}

/* ─────────────────────────────
 * 팀장 관리
 * ────────────────────────────*/
const departments = ref<any[]>([])
const employees = ref<any[]>([])
const empLoading = ref(false)
const selectedDept = ref<any|null>(null)
const selectedLeaderId = ref<number|null>(null)

const empHeaders = [
  { title: '사번', key: 'emp_no', width: 100 },
  { title: '이름', key: 'name', minWidth: 140 },
  { title: '직책', key: 'title', width: 110 },
  { title: '부서', key: 'dept', width: 100 },
  { title: '현 팀장', key: 'is_leader', width: 90, align: 'center' },
]

async function loadDepartments() {
  const r:any = await http.get('/master/departments')
  departments.value = r?.items || []
}
function selectDept(dept:any) {
  selectedDept.value = dept
  selectedLeaderId.value = null
  loadEmployees(dept)
}
async function loadEmployees(dept:any) {
  empLoading.value = true
  const res:any = await http.get(`/employees/by-department/${dept.dept_code}?property_code=MOP`)
  employees.value = res?.items || []
  empLoading.value = false
}
async function confirmLeader() {
  const emp = employees.value.find(e => e.id === selectedLeaderId.value)
  if (!emp || !selectedDept.value) return
  const ok = await confirmApi.ask(`'${emp.name}' 직원을 ${selectedDept.value.dept_name} 팀장으로 지정할까요?`)
  if (!ok) return
  await http.put(`/master/departments/${selectedDept.value.id}/leader`, { leader_emp_id: emp.id })
  toast.success('팀장이 지정되었습니다.')
  await loadDepartments()
  selectedDept.value = departments.value.find(d => d.id === selectedDept.value.id)
}

/* ─────────────────────────────
 * 전체 새로고침
 * ────────────────────────────*/
async function reloadAll() {
  loading.value = true
  try {
    await Promise.all([loadMenuMatrix(), loadDepartments()])
  } finally {
    loading.value = false
  }
}
onMounted(reloadAll)
</script>

<style scoped>
.brand-subbar {
  border: 1px solid var(--color-line);
  background: var(--color-surface);
  border-radius: 12px;
  padding: 12px 20px;
  box-shadow: var(--shadow-sm);
}
.cursor-pointer { cursor: pointer; transition: 0.2s; }
.cursor-pointer:hover { transform: translateY(-2px); }

/* 색상 매핑 스타일 (행 배경) */
.row-all-view { background-color: #e3f2fd !important; }
.row-all-edit { background-color: #ffebee !important; }
.row-fr       { background-color: #e0f2f1 !important; }
.row-hk       { background-color: #fff3e0 !important; }
.row-ad       { background-color: #e8eaf6 !important; }
.row-fm       { background-color: #f3e5f5 !important; }
.row-mg       { background-color: #f5f5f5 !important; }
</style>
