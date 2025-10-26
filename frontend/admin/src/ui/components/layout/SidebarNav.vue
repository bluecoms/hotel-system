<!-- ============================================================================
# File      : src/ui/components/layout/SidebarNav.vue
# Version   : 2025.11-01 · v3.6 Final Stable (MG=SUPERADMIN Policy 적용판)
# Purpose   : Hotel Admin — 사이드바 네비게이션 (DeptAccess + MG 슈퍼권한)
# ----------------------------------------------------------------------------
# 목적:
#   • 좌측 Drawer 내 네비게이션 표시 및 사용자/지점 정보 렌더
#   • menu.ts 기반 Router/DeptAccess 필터링 수행
#   • PropertyStore 연동으로 현재 지점 표시
# ----------------------------------------------------------------------------
# 주요 개선사항 (v3.6)
#   ✅ MG 부서 사용자를 SUPERADMIN 동일 권한으로 처리 (can 함수)
#   ✅ router/menu.ts v3.5 구조 완전 반영
#   ✅ routeExists / isGroupActive 안정화
#   ✅ Breadcrumbs 개선 (meta.title 기반)
# ============================================================================ -->

<template>
  <v-navigation-drawer
    v-model="drawer"
    app
    fixed
    width="260"
    class="drawer--brand"
  >
    <!-- ▣ 상단 경로 표시 (Breadcrumbs) -->
    <div class="nav-header px-4 pt-4 pb-3">
      <v-breadcrumbs :items="crumbs" class="breadcrumbs text-caption" divider="›">
        <template #prepend>
          <v-icon size="14" color="primary" class="mr-1">mdi-home</v-icon>
        </template>
      </v-breadcrumbs>
    </div>

    <v-divider class="mb-3" />

    <!-- ▣ 네비게이션 리스트 -->
    <v-list density="comfortable" nav>
      <!-- ─────────────────────────────
           대시보드 (상단 고정)
         ───────────────────────────── -->
      <template v-if="dashboardItem && can(dashboardItem.roles)">
        <v-list-item
          :title="dashboardItem.label"
          :to="routeExists(dashboardItem.to) ? dashboardItem.to : undefined"
          :prepend-icon="dashboardItem.icon || 'mdi-view-dashboard-outline'"
          color="primary"
          :active="isActive(dashboardItem.to)"
          :disabled="!routeExists(dashboardItem.to)"
          link
        />
        <v-divider class="my-1" />
      </template>

      <!-- ▣ 업무 그룹 -->
      <div class="section-label px-4 py-1 text-grey text-caption font-weight-bold">
        업무
      </div>

      <template v-for="g in workGroups" :key="g.label">
        <v-list-group :value="`grp-${g.label}`">
          <template #activator="{ props }">
            <v-list-item
              v-bind="props"
              :title="g.label"
              :prepend-icon="g.icon"
              color="primary"
              :active="isGroupActive(g.children || [])"
            />
          </template>
          <v-slide-y-transition group>
            <v-list-item
              v-for="c in g.children"
              :key="c.to"
              :title="c.label"
              :to="routeExists(c.to) ? c.to : undefined"
              :prepend-icon="c.icon"
              color="primary"
              :active="isActive(c.to)"
              :disabled="!routeExists(c.to)"
              link
            />
          </v-slide-y-transition>
        </v-list-group>
      </template>

      <!-- ▣ 관리 그룹 -->
      <div class="section-label px-4 py-1 text-grey text-caption font-weight-bold mt-3">
        관리
      </div>

      <!-- ▣ 단일 항목(예: 권한 관리) 먼저 렌더 -->
      <template v-for="s in adminSingles" :key="s.to">
        <v-list-item
          :title="s.label"
          :to="routeExists(s.to) ? s.to : undefined"
          :prepend-icon="s.icon"
          color="primary"
          :active="isActive(s.to)"
          :disabled="!routeExists(s.to)"
          link
        />
      </template>

      <!-- ▣ 하위 메뉴를 가진 그룹 렌더 -->
      <template v-for="g in adminGroups" :key="g.label">
        <v-list-group :value="`grp-${g.label}`">
          <template #activator="{ props }">
            <v-list-item
              v-bind="props"
              :title="g.label"
              :prepend-icon="g.icon"
              color="primary"
              :active="isGroupActive(g.children || [])"
            />
          </template>
          <v-slide-y-transition group>
            <v-list-item
              v-for="c in g.children"
              :key="c.to"
              :title="c.label"
              :to="routeExists(c.to) ? c.to : undefined"
              :prepend-icon="c.icon"
              color="primary"
              :active="isActive(c.to)"
              :disabled="!routeExists(c.to)"
              link
            />
          </v-slide-y-transition>
        </v-list-group>
      </template>
    </v-list>

    <v-divider class="my-2" />

    <!-- ▣ 하단 사용자 + 지점 정보 표시 -->
    <div class="px-4 py-3 text-caption">
      <div class="mb-1">
        버전: <strong>v2025.11</strong>
      </div>

      <!-- 사용자 이름 -->
      <div v-if="auth.user" class="d-flex align-center mb-1 text-truncate">
        <v-icon size="14" color="primary" class="mr-1">mdi-account</v-icon>
        <strong>{{ auth.user.name || auth.user.email }}</strong>
      </div>

      <!-- 역할 표시 -->
      <div class="text-grey-darken-1 mb-1">
        <v-icon size="14" color="grey" class="mr-1">mdi-shield-account-outline</v-icon>
        {{ (auth.user?.roles || []).join(', ') || '—' }}
      </div>

      <!-- ✅ 현재 지점 표시 -->
      <div class="text-grey-darken-1">
        <v-icon size="14" color="primary" class="mr-1">mdi-domain</v-icon>
        {{ property.current || '지점 미선택' }}
      </div>
    </div>
  </v-navigation-drawer>
</template>

<script setup lang="ts">
/* ============================================================================
# Script Logic — Sidebar Navigation (v3.6 Final Stable)
# ----------------------------------------------------------------------------
# 구성요소:
#   • menu.ts 기반 메뉴 필터링 및 렌더링
#   • DeptAccess / Role / MG 정책 기반 권한 필터
#   • Breadcrumbs 자동 생성
#   • 하단에 사용자 / Property 표시
# ============================================================================ */
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePropertyStore } from '@/stores/property'
import menu, { type NavItem } from '@/router/menu'

/* Drawer 상태 */
const props = defineProps<{ modelValue: boolean }>()
const emit = defineEmits(['update:modelValue'])
const drawer = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

/* Store / Router / Property */
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const property = usePropertyStore()

/* ─────────────────────────────
   Router 활성 상태 판단
────────────────────────────── */
function isActive(path?: string) {
  if (!path) return false
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
function isGroupActive(items: NavItem[]) {
  return items.some(it => isActive(it.to))
}
function routeExists(to?: string) {
  return !!to && router.getRoutes().some(r => r.path === to)
}

/* ─────────────────────────────
   권한 필터 (DeptAccess + MG 정책)
────────────────────────────── */
function can(roles?: string[]) {
  if (!roles?.length) return true
  const userRoles = (auth.user?.roles || []).map(r => r.toUpperCase())
  const dept = (auth.user?.dept || '').toUpperCase()

  // ✅ SUPERADMIN 또는 MG(관리부서)는 모든 메뉴 접근 허용
  if (userRoles.includes('SUPERADMIN') || dept === 'MG') return true
  return roles.some(r => userRoles.includes(r.toUpperCase()))
}

/* ─────────────────────────────
   메뉴 필터링 및 분류
────────────────────────────── */
const filteredMenu = computed<NavItem[]>(() => {
  const deep = (items: NavItem[]): NavItem[] =>
    items
      .filter(m => can(m.roles))
      .map(m => (m.children ? { ...m, children: deep(m.children) } : m))
  return deep(menu)
})

/* 상단 대시보드 */
const dashboardItem = computed<NavItem | undefined>(() =>
  filteredMenu.value.find(m => m.to === '/' || m.routeName === 'dashboard-kpi')
)

/* 업무 섹션 */
const workGroups = computed(() =>
  filteredMenu.value.filter(m =>
    ['마감 관리', '리포트', '하우스키핑', '인사 관리'].includes(m.label)
  )
)

/* 관리 섹션 — 단일 항목(권한관리) */
const adminSingles = computed(() =>
  filteredMenu.value.filter(m => m.label === '권한 관리' && !Array.isArray(m.children))
)

/* 관리 섹션 — 그룹형 메뉴 */
const adminGroups = computed(() =>
  filteredMenu.value.filter(m =>
    ['시스템 관리', '내 계정'].includes(m.label)
  )
)

/* ─────────────────────────────
   Breadcrumbs 자동 생성
────────────────────────────── */
const crumbs = computed(() => {
  const segments = route.path.split('/').filter(Boolean)
  let acc = ''
  return segments.map(seg => {
    acc += '/' + seg
    const match = router.getRoutes().find(r => r.path === acc)
    return { title: match?.meta?.title || seg, href: acc }
  })
})
</script>

<style scoped>
.drawer--brand {
  background: rgb(var(--v-theme-surface));
  color: rgb(var(--v-theme-on-surface));
}
.section-label {
  opacity: 0.7;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.nav-header {
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}
.breadcrumbs {
  color: var(--color-muted);
  font-weight: 500;
}
</style>
