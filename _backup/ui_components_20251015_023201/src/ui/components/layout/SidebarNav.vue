<!-- src/ui/components/layout/SidebarNav.vue -->
<template>
  <v-navigation-drawer
    v-model="drawer"
    app
    fixed
    width="260"
    class="drawer--brand"
  >
    <div class="nav-header px-4 pt-4 pb-3">
      <v-breadcrumbs :items="crumbs" class="breadcrumbs text-caption" divider="›">
        <template #prepend>
          <v-icon size="14" color="primary" class="mr-1">mdi-home</v-icon>
        </template>
      </v-breadcrumbs>
    </div>

    <v-divider class="mb-3" />

    <v-list density="comfortable" nav>
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

      <div class="section-label px-4 py-1 text-grey text-caption font-weight-bold mt-3">
        관리
      </div>
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

    <div class="px-4 py-3 text-caption">
      <div class="mb-1">버전: <strong>v2025.10</strong></div>
      <div v-if="auth.user" class="d-flex align-center mb-1 text-truncate">
        <v-icon size="14" color="primary" class="mr-1">mdi-account</v-icon>
        <strong>{{ auth.user.name || auth.user.email }}</strong>
      </div>
      <div class="text-grey-darken-1">
        <v-icon size="14" color="grey" class="mr-1">mdi-shield-account-outline</v-icon>
        {{ (auth.user?.roles || []).join(', ') || '—' }}
      </div>
    </div>
  </v-navigation-drawer>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import menu, { type NavItem } from '@/router/menu'

const props = defineProps<{ modelValue: boolean }>()
const emit = defineEmits(['update:modelValue'])
const drawer = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

function isActive(path?: string) {
  return path ? route.path.startsWith(path) : false
}
function isGroupActive(items: NavItem[]) {
  return items.some(it => isActive(it.to))
}
function routeExists(to?: string): boolean {
  if (!to) return false
  return router.getRoutes().some(r => r.path === to)
}

const can = (roles?: string[]) => {
  if (!roles?.length) return true
  if (auth.user?.roles?.includes('SUPERADMIN')) return true
  return roles.some(r => auth.user?.roles?.includes(r))
}

const filteredMenu = computed<NavItem[]>(() => {
  const deep = (items: NavItem[]): NavItem[] =>
    items
      .filter(m => can(m.roles))
      .map(m => (m.children ? { ...m, children: deep(m.children) } : m))
      .filter(m => !m.children || m.children.length > 0)
  return deep(menu)
})

const workGroups = computed(() => filteredMenu.value.filter(m =>
  ['마감 관리', 'OTA 관리', '리포트', '인사 관리'].includes(m.label)
))
const adminGroups = computed(() => filteredMenu.value.filter(m =>
  ['사용자 관리', '시스템 설정', '내 계정'].includes(m.label)
))

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
.text-disabled {
  opacity: 0.5;
  pointer-events: none;
}
.nav-header {
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}
.breadcrumbs {
  color: var(--color-muted);
  font-weight: 500;
}
</style>
