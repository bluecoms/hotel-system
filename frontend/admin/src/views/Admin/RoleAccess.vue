<!-- ============================================================================
# File      : src/views/Admin/RoleAccess.vue
# Version   : 2025.11-04 · v4.3 (라우터 메뉴 동기화: '@/router/menu' 사용)
# Purpose   : Hotel Admin — 권한 관리 (부서별 접근권한 + 팀장 지정 UI)
# ----------------------------------------------------------------------------
# 이번 패치 요약
#  ✅ 전역 토스트(useToast) 연결 — 저장/지정 시 공통 토스트 노출
#  ✅ "부서별 접근권한" 열 드롭박스를 **정중앙** 배치(헤더와 수직 정렬)
#  ✅ 라우터 정적 메뉴('@/router/menu')를 플래튼하여 **행 순서 동기화**
#  ✅ TS 타입 안정화(http.get<T>()), i18n 의존 X (useToast 내부에서 처리)
#  ✅ 팀장 카드형 UI 유지(사진·이메일·셀렉트)
#  ✅ '*' 전역 레코드는 UX 혼란 방지를 위해 목록에서 **숨김**
# ========================================================================= -->
<template>
  <v-container fluid class="py-6 page-shell">
    <!-- ─────── 헤더 ─────── -->
    <v-card flat class="pa-4 mb-4">
      <h2 class="text-h6 font-weight-bold mb-1">권한 관리</h2>
      <p class="text-body-2 text-medium-emphasis">
        부서별 접근권한 및 팀장 지정 통합 관리
      </p>

      <!-- 탭 -->
      <v-tabs v-model="activeTab" class="mt-2" density="compact">
        <v-tab value="roles">부서별 접근권한</v-tab>
        <v-tab value="leads">부서별 팀장 관리</v-tab>
      </v-tabs>
    </v-card>

    <!-- ─────── 탭 콘텐츠 ─────── -->
    <v-window v-model="activeTab" class="rounded-xl elevation-1">

      <!-- ▣ 부서별 접근권한 탭 -->
      <v-window-item value="roles">
        <v-card flat class="pa-4 rounded-xl elevation-1">

          <!-- 상단 부서 칩 팔레트 (가이드용) -->
          <div class="d-flex flex-wrap gap-2 mb-4">
            <v-chip
              v-for="(label, code) in deptLabels"
              :key="code"
              :color="colorMap[code]"
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
                  :style="{
                    backgroundColor:
                      item.access_scope.length === 1
                        ? colorMap[item.access_scope[0]] || '#E0E0E0'
                        : '#F3F4F6',
                  }"
                  @update:model-value="updateAccess(item)"
                >
                  <template #selection="{ item: sel }">
                    <v-chip
                      size="x-small"
                      variant="flat"
                      class="ma-1 role-chip-inner"
                      :color="colorMap[sel.value] || '#E0E0E0'"
                      text-color="black"
                    >
                      {{ sel.title }}
                    </v-chip>
                  </template>
                </v-select>
              </div>
            </template>
          </v-data-table>
        </v-card>
      </v-window-item>

      <!-- ▣ 부서별 팀장 관리 탭 (카드형) -->
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
                <v-avatar size="72" class="mb-2">
                  <img :src="lead.photo || '/images/avatar-default.png'" />
                </v-avatar>

                <h4 class="font-weight-bold mb-1">
                  {{ deptLabels[lead.dept_code] || lead.dept_code }}
                </h4>

                <p class="text-caption text-medium-emphasis mb-2">
                  {{ lead.lead_email || '이메일 없음' }}
                </p>

                <v-select
                  :items="employeeOptions"
                  v-model="lead.lead_name"
                  label="팀장 선택"
                  density="comfortable"
                  variant="outlined"
                  hide-details
                  class="mb-2"
                  @update:model-value="saveLead(lead)"
                />

                <v-chip color="primary" variant="flat" size="x-small" class="mt-1">
                  현재: {{ lead.lead_name || '미지정' }}
                </v-chip>
              </v-card>
            </v-col>
          </v-row>

          <div v-if="!loadingLeads && deptLeads.length === 0" class="text-center py-10 text-medium-emphasis">
            부서별 팀장 정보가 없습니다.
          </div>
        </v-card>
      </v-window-item>

    </v-window>
  </v-container>
</template>

<script setup lang="ts">
/* =============================================================================
   Hotel Admin — RoleAccess (DeptAccess + DeptLeads)
   - 전역토스트(useToast) 사용
   - 라우터 정적 메뉴('@/router/menu') 기반으로 행 순서 동기화
   - 드롭박스 중앙 배치
============================================================================= */
import { ref, onMounted, watch } from 'vue'
import http from '@/services/http'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/ui/composables/useToast'   // ✅ 전역 토스트 연결
import menu from '@/router/menu'                        // ✅ 정적 메뉴 배열(SSOT)
type NavItem = { label: string; to?: string; icon?: string; roles?: string[]; routeName?: string; children?: NavItem[] }

const auth = useAuthStore()
const toast = useToast()

// 탭/로딩/데이터 상태
const activeTab = ref<'roles' | 'leads'>('roles')
const loading = ref(false)
const loadingLeads = ref(false)
const rows = ref<any[]>([])        // DeptAccess 목록
const deptLeads = ref<any[]>([])   // 부서별 팀장 목록

// ───────────────────────────────────────────────
// 부서/색상/옵션
// ───────────────────────────────────────────────
const deptLabels: Record<string, string> = {
  ALL_VIEW: 'ALL 보기',
  ALL_EDIT: 'ALL 권한',
  FR: 'FR (프론트)',
  HK: 'HK (하우스키핑)',
  AD: 'AD (경영지원)',
  FM: 'FM (시설관리)',
  MG: 'MG (관리)',
}
const colorMap: Record<string, string> = {
  ALL_VIEW: '#BFDBFE',
  ALL_EDIT: '#FECACA',
  FR: '#A7F3D0',
  HK: '#FDE68A',
  AD: '#C7D2FE',
  FM: '#E9D5FF',
  MG: '#E5E7EB',
}
const deptOptions = Object.entries(deptLabels).map(([k, v]) => ({ title: v, value: k }))

// ───────────────────────────────────────────────
// 메뉴 라벨 매핑(한글표시) + 헤더 정의
// ───────────────────────────────────────────────
const labelMap: Record<string, string> = {
  'account-info': '내 계정 정보',
  'closing-calendar': '마감 캘린더',
  'closing-day': '일별 보드',
  'closing-merge': '병합 이력',
  'dashboard-kpi': '대시보드',
  'hr-account-link': '계정 매핑',
  'hr-contracts': '계약 관리',
  'hr-dashboard': 'HR 대시보드',
  'hr-employees': '직원 목록',
  'hr-records': '근태 기록',
  'reports-sales-tags': '태그별 매출',
  'reports-bank-ledger': '입금내역',
  'reports-expenses': '지출내역',
  'reports-fnb-daily': 'F&B 일별 매출',
  'reports-rooms-summary': '객실 매출 요약',
  'role-access': '권한 관리',
  'users': '사용자 관리',
}
const headers = [
  { title: 'Label', key: 'label', align: 'start' },
  { title: 'Route', key: 'route_name', align: 'center' },
  { title: '부서별 접근권한', key: 'access_scope', align: 'center' },
]

// 직원(팀장 후보) 더미 — 실제로는 /api/employees로 교체 가능
const employeeOptions = [
  { title: '김프론트', value: '김프론트' },
  { title: '이하우스', value: '이하우스' },
  { title: '박지원', value: '박지원' },
  { title: '최시설', value: '최시설' },
  { title: '정관리', value: '정관리' },
]

// ───────────────────────────────────────────────
// 정적 메뉴에서 routeName 순서를 플래튼하여 추출 (중첩 children 포함)
// - menu: '@/router/menu' 기본 export 배열을 탐색
// - 반환: routeName 문자열 배열 (상위→하위 순서 유지)
// ───────────────────────────────────────────────
function flattenRouteOrder(list: NavItem[], acc: string[] = []): string[] {
  for (const m of list) {
    if (m.routeName) acc.push(m.routeName)
    if (Array.isArray(m.children) && m.children.length) flattenRouteOrder(m.children, acc)
  }
  return acc
}
const MENU_ORDER = flattenRouteOrder(menu as unknown as NavItem[])

// ───────────────────────────────────────────────
// 데이터 로드: DeptAccess
//  - '*' 전역 레코드는 목록에서 숨김 (개별 라우트 권한에 집중)
//  - 라우터 메뉴 순서(MENU_ORDER)로 정렬
// ───────────────────────────────────────────────
async function loadAccess() {
  loading.value = true
  try {
    const res = await http.get<any[]>('roles/access')
    const raw = (res || [])
      .filter(r => r.route_name !== '*')
      .map((r: any) => ({ ...r, label: labelMap[r.route_name] || r.route_name }))

    rows.value = raw.sort((a, b) => {
      const ia = MENU_ORDER.indexOf(a.route_name)
      const ib = MENU_ORDER.indexOf(b.route_name)
      return (ia === -1 ? 9999 : ia) - (ib === -1 ? 9999 : ib)
    })
  } catch (e) {
    toast.fromError(e)
  } finally {
    loading.value = false
  }
}

// ───────────────────────────────────────────────
// 저장: DeptAccess Upsert
// ───────────────────────────────────────────────
async function updateAccess(item: any) {
  try {
    const payload = { route_name: item.route_name, access_scope: item.access_scope }
    await http.put('roles/access', payload)
    await auth.bootstrap() // 저장 즉시 접근권한 반영
    toast.success(`『${labelMap[item.route_name] || item.route_name}』 권한이 저장되었습니다.`)
  } catch (e) {
    toast.fromError(e)
  }
}

// ───────────────────────────────────────────────
// 팀장 관리: 조회/저장
// ───────────────────────────────────────────────
async function loadDeptLeads() {
  loadingLeads.value = true
  try {
    const res = await http.get<{ items?: any[] }>('roles/dept-leads')
    deptLeads.value = Array.isArray(res?.items) ? res.items : []
  } catch (e) {
    toast.fromError(e)
    deptLeads.value = []
  } finally {
    loadingLeads.value = false
  }
}

async function saveLead(dept: any) {
  try {
    const payload = {
      dept_code: dept.dept_code,
      lead_name: dept.lead_name,
      lead_email: dept.lead_email || `${dept.lead_name}@hotel.com`,
    }
    await http.put('roles/dept-leads', payload)
    toast.success(`『${deptLabels[dept.dept_code] || dept.dept_code}』 팀장이 ‘${dept.lead_name}’ 으로 지정되었습니다.`)
  } catch (e) {
    toast.fromError(e)
  }
}

// ───────────────────────────────────────────────
// 라이프사이클
// ───────────────────────────────────────────────
onMounted(() => {
  loadAccess()
})
watch(activeTab, (v) => {
  if (v === 'leads') loadDeptLeads()
})
</script>

<style scoped>
/* ============================================================================
   페이지 배경
============================================================================ */
.page-shell {
  background-color: #f9fafb;
}

/* ============================================================================
   드롭박스 중앙 배치
   - '부서별 접근권한' 열의 셀 전체를 중앙 정렬
   - 드롭박스 자체 폭을 고정/일관(가독)
============================================================================ */
.access-table :deep(th:nth-child(3)) {
  text-align: center;           /* 헤더 중앙 */
}
.access-cell {
  display: flex;
  justify-content: center;      /* ✅ 드롭박스 중앙 배치 */
  align-items: center;
  width: 100%;
}
.role-chip {
  width: 220px;                 /* ✅ 일관된 폭으로 정렬 안정 */
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 600;
  text-align: center;
  box-shadow: 0 0 0 1px #d1d5db inset;
}
.role-chip-inner {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
}

/* ============================================================================
   팀장 카드형 UI
============================================================================ */
.dept-lead-cards {
  margin-top: 8px;
  justify-content: center;  /* 가운데 그리드 배치 */
  align-items: stretch;
  gap: 24px;
}
.lead-card {
  border-radius: 16px;
  background: linear-gradient(180deg, #fff, #f9fafb);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.06);
  padding: 16px;
  max-width: 300px;
  margin: 0 auto;
}
.v-avatar img {
  border-radius: 50%;
  object-fit: cover;
}

/* ============================================================================
   테이블 기본 폰트/여백
============================================================================ */
.v-data-table th {
  font-weight: 700;
  color: #374151;
}
.v-data-table td {
  padding-top: 6px !important;
  padding-bottom: 6px !important;
}
</style>
