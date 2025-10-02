import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import Closing from '@/views/Closing.vue'
import Board from '@/views/closing/Board.vue'
import Users from '@/views/Users.vue'
import Login from '@/views/Login.vue'
import Forbidden from '@/views/Forbidden.vue'
import { useAuthStore } from '@/stores/auth'
import { getToken } from '@/services/http'   // 토큰 존재 여부 우선 확인

const routes: RouteRecordRaw[] = [
  { path: '/login', name: 'login', component: Login, meta: { public: true } },
  { path: '/403',   name: 'forbidden', component: Forbidden, meta: { public: true } },
  { path: '/', redirect: { name: 'dashboard' } },

  // 기본 메뉴들
  { path: '/dashboard',     name: 'dashboard',     component: Dashboard, meta: { requiresAuth: true, roles: ['ADMIN','SUPERADMIN'] } },
  { path: '/closing',       name: 'closing',       component: Closing,   meta: { requiresAuth: true, roles: ['ADMIN','SUPERADMIN'] } },
  { path: '/closing/board', name: 'closing-board', component: Board,     meta: { requiresAuth: true, roles: ['ADMIN','SUPERADMIN'] } },
  { path: '/employees',     name: 'employees',     component: () => import('@/views/Employees.vue'), meta: { requiresAuth: true, roles: ['ADMIN','SUPERADMIN'] } },
  { path: '/admin/users',   name: 'users',         component: Users,     meta: { requiresAuth: true, roles: ['SUPERADMIN'] } },

  // ■ ADMIN 전용 고정
  { path: '/ota', name: 'ota', component: () => import('@/views/Ota.vue'), meta: { requiresAuth: true, roles: ['ADMIN'] } },
  {
    path: '/admin/ota/list',
    name: 'OTAList',
    component: () => import('@/views/OTA/OTAList.vue'),
    meta: { requiresAuth: true, roles: ['ADMIN'] },
  },
  {
    path: '/admin/ota/commission',
    name: 'OTACommission',
    component: () => import('@/views/OTA/Commission.vue'),
    meta: { requiresAuth: true, roles: ['ADMIN'] },
  },
  {
    path: '/admin/reports/sales-tags',
    name: 'ReportSalesTags',
    component: () => import('@/views/Reports/SalesTags.vue'),
    meta: { requiresAuth: true, roles: ['ADMIN'] },
  },

  { path: '/keywords', name: 'keywords', component: () => import('@/views/Keywords.vue'), meta: { requiresAuth: true, roles: ['ADMIN','SUPERADMIN'] } },

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
    if (to.name === 'login' && auth.user) {
      const redirect = (to.query.redirect as string) || '/dashboard'
      return { path: redirect }
    }
    return true
  }

  // 인증 필요 라우트: 토큰 없으면 로그인
  const token = getToken()
  if (!token) {
    auth.user = null
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  // 토큰 있을 때만 me 로드(1회)
  if (!auth.user) {
    try { await auth.bootstrap() } catch {}
  }
  if (!auth.user) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  // ─ 권한 체크 (SUPERADMIN 무조건 패스)
  const needRaw = (to.meta.roles as string[] | undefined) ?? []
  const need = needRaw.map(r => String(r).toUpperCase())
  const roles = (auth.user?.roles ?? []).map(r => String(r).toUpperCase())

  if (roles.includes('SUPERADMIN')) return true
  if (need.length && !need.some(r => roles.includes(r))) {
    return { name: 'forbidden' }
  }
  return true
})

export default router
