// src/router/index.ts
import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import Closing from '@/views/Closing.vue'
import Board from '@/views/closing/Board.vue'
import Users from '@/views/Users.vue'
import Login from '@/views/Login.vue'
import Forbidden from '@/views/Forbidden.vue'
import { useAuthStore, ROLES } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  { path: '/login', name: 'login', component: Login, meta: { public: true } },
  { path: '/403',   name: 'forbidden', component: Forbidden, meta: { public: true } },
  { path: '/', redirect: { name: 'dashboard' } },

  {
    path: '/dashboard',
    name: 'dashboard',
    component: Dashboard,
    meta: { requiresAuth: true, roles: [ROLES.ADMIN, ROLES.SUPERADMIN] },
  },
  {
    path: '/closing',
    name: 'closing',
    component: Closing,
    meta: { requiresAuth: true, roles: [ROLES.ADMIN, ROLES.SUPERADMIN] },
  },
  {
    path: '/closing/board',
    name: 'closing-board',
    component: Board,
    meta: { requiresAuth: true, roles: [ROLES.ADMIN, ROLES.SUPERADMIN] },
  },
  {
    path: '/employees',
    name: 'employees',
    component: () => import('@/views/Employees.vue'),
    meta: { requiresAuth: true, roles: [ROLES.ADMIN, ROLES.SUPERADMIN] },
  },
  {
    path: '/admin/users',
    name: 'users',
    component: Users,
    meta: { requiresAuth: true, roles: [ROLES.SUPERADMIN] },
  },
  {
    path: '/ota',
    name: 'ota',
    component: () => import('@/views/Ota.vue'),
    meta: { requiresAuth: true, roles: [ROLES.ADMIN, ROLES.SUPERADMIN] },
  },
  {
    path: '/keywords',
    name: 'keywords',
    component: () => import('@/views/Keywords.vue'),
    meta: { requiresAuth: true, roles: [ROLES.ADMIN, ROLES.SUPERADMIN] },
  },

  { path: '/:pathMatch(.*)*', redirect: { name: 'dashboard' } },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // 퍼블릭 라우트
  if (to.meta.public) {
    // 로그인 페이지에서 이미 로그인되어 있으면 리디렉트
    if (to.name === 'login') {
      if (!auth.user) { try { await auth.bootstrap() } catch {} }
      if (auth.user) {
        const redirect = (to.query.redirect as string) || '/dashboard'
        return { path: redirect }
      }
    }
    return true
  }

  // 인증 필요 라우트
  if (!auth.user) {
    try { await auth.bootstrap() } catch {}
  }
  if (!auth.user) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  // 역할 체크
  const need = (to.meta.roles as string[] | undefined) ?? []
  if (need.length && !need.some(r => auth.user!.roles.includes(r))) {
    return { name: 'forbidden' }
  }

  return true
})

export default router
