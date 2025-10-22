<!-- ============================================================================
# File      : src/ui/components/layout/SidebarNav.vue
# Version   : 2025.10-28 · v3.4 (Sync menu.ts v3.3 · SSOT Unified)
# Purpose   : Hotel Admin — 사이드바 네비게이션 (DeptAccess 기반)
# ----------------------------------------------------------------------------
# 목적:
#   • 좌측 Drawer 내 네비게이션 표시 및 사용자/지점 정보 렌더
#   • menu.ts 기반으로 Router와 권한(RoleAccess/DeptAccess) 필터링 수행
#   • PropertyStore 연동으로 현재 선택된 지점 정보 표시
# ----------------------------------------------------------------------------
# 주요 변경사항 (v3.4)
#   ✅ menu.ts v3.3 구조 반영 — “시스템 관리” 그룹명 및 필터 로직 수정
#   ✅ Breadcrumbs 개선 (route.meta.title 기반 우선)
#   ✅ 권한 필터 can() 보강 — SUPERADMIN 예외 / 타입 안정화
#   ✅ 주석 규격 SSOT 통일
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
        버전: <strong>v2025.10</strong>
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
        <span v-if="currentProperty?.code" class="text-caption text-grey-darken-2">
          ({{ currentProperty.code }})
        </span>
      </div>
    </div>
  </v-navigation-drawer>
</template>

<script setup lang="ts">
/* ============================================================================
# Script Logic — Sidebar Navigation (SSOT v3.4)
# ----------------------------------------------------------------------------
# 구성요소:
#   • menu.ts (v3.3) 기반 메뉴 필터링 및 렌더링
#   • DeptAccess / Role 기반 권한 필터
#   • Breadcrumbs 자동 생성
#   • 하단에 사용자 / Property 표시
# ============================================================================ */
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePropertyStore } from '@/stores/property'
import menu, { type NavItem } from '@/router/menu'

/* Drawer 상태 바인딩 */
const props = defineProps<{ modelValue: boolean }>()
const emit = defineEmits(['update:modelValue'])
const drawer = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

/* Store / Router / Property 연동 */
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const property = usePropertyStore()

/* 현재 지점 정보 */
const currentProperty = computed(() => property.current)

/* ─────────────────────────────
   Router 활성 상태 판단 함수
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
   권한 필터 로직 (DeptAccess/Role)
────────────────────────────── */
function can(roles?: string[]) {
  if (!roles?.length) return true
  const userRoles = (auth.user?.roles || []).map(r => r.toUpperCase())
  if (userRoles.includes('SUPERADMIN')) return true
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

/* 대시보드 (고정 상단) */
const dashboardItem = computed<NavItem | undefined>(() =>
  filteredMenu.value.find(m => m.to === '/' || m.routeName === 'dashboard-kpi')
)

/* 업무 섹션 */
const workGroups = computed(() =>
  filteredMenu.value.filter(m =>
    ['마감 관리', '리포트', '인사 관리'].includes(m.label)
  )
)

/* 관리 섹션 — 단일 항목(권한관리) */
const adminSingles = computed(() =>
  filteredMenu.value.filter(m => m.label === '권한 관리' && !Array.isArray(m.children))
)

/* 관리 섹션 — 하위 메뉴 포함 그룹 (시스템 관리/내 계정 등) */
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
