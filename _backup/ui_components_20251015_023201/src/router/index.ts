// src/router/index.ts
// ===========================================================
// Vue Router — Hotel Admin v2025 Full (ReportsShell Updated)
// ===========================================================

import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// ────────────── Lazy Imports ──────────────
const Login             = () => import('@/views/Auth/Login.vue')
const Forbidden         = () => import('@/views/Forbidden.vue')
const Dashboard         = () => import('@/views/Dashboard.vue')

// Closing
const ClosingBoard      = () => import('@/views/closing/Board.vue')
const ClosingCal        = () => import('@/views/closing/Closing.vue')
const ClosingMerge      = () => import('@/views/closing/merge/MergeHistory.vue')

// OTA
const OTA               = () => import('@/views/OTA/Ota.vue')

// Reports
const ReportsTags       = () => import('@/views/Reports/SalesTags.vue')
const ReportsBank       = () => import('@/views/Reports/BankLedger.vue')
const ReportsExp        = () => import('@/views/Reports/Expenses.vue')
const ReportsFnb        = () => import('@/views/Reports/FnbDaily.vue')
const ReportsRooms      = () => import('@/views/Reports/RoomsSummary.vue')

// HR
const HrDashboard       = () => import('@/views/Admin/HR/Dashboard.vue')
const HrEmployees       = () => import('@/views/Admin/HR/Employees.vue')
const HrContracts       = () => import('@/views/Admin/HR/Contracts.vue')
const HrRecords         = () => import('@/views/Admin/HR/Records.vue')
const HrAccountLink     = () => import('@/views/Admin/HR/AccountLink.vue')

// Users
const Users             = () => import('@/views/Users/Users.vue')
const UsersMaster       = () => import('@/views/Users/master/MasterData.vue')
const ResetUserPassword = () => import('@/views/Admin/ResetUserPassword.vue')

// System
const RoleAccess        = () => import('@/views/Admin/RoleAccess.vue')

// Auth
const ChangePassword    = () => import('@/views/Auth/ChangePassword.vue')

// Misc
const Blank             = () => import('@/views/Blank.vue')

// ────────────── Route Map ──────────────
const routes: RouteRecordRaw[] = [
  // Auth
  { path: '/login', name: 'login', component: Login, meta: { requiresAuth: false, title: 'Login', hideInMenu: true } },
  { path: '/forbidden', name: 'forbidden', component: Forbidden, meta: { requiresAuth: false, title: 'Forbidden', hideInMenu: true } },

  // Dashboard
  { path: '/', name: 'dashboard', component: Dashboard, meta: { title: 'Dashboard', requiresAuth: true, roles: ['ADMIN', 'SUPERADMIN'], routeName: 'dashboard-kpi', need: 'view' } },

  // Closing
  { path: '/closing', name: 'closing-cal', component: ClosingCal, meta: { title: 'Closing Calendar', requiresAuth: true, roles: ['ADMIN', 'SUPERADMIN'], routeName: 'closing-calendar', need: 'view' } },
  { path: '/closing/board', name: 'closing-board', component: ClosingBoard, meta: { title: 'Closing Board', requiresAuth: true, roles: ['ADMIN', 'SUPERADMIN'], routeName: 'closing-day', need: 'view' } },
  { path: '/closing/merge', name: 'closing-merge', component: ClosingMerge, meta: { title: 'Merge History', requiresAuth: true, roles: ['SUPERADMIN'], routeName: 'closing-merge', need: 'view' } },

  // OTA
  { path: '/ota', name: 'ota', component: OTA, meta: { title: 'OTA', requiresAuth: true, roles: ['ADMIN', 'SUPERADMIN'], routeName: 'ota-sales', need: 'view' } },

  // Reports (5종)
  { path: '/admin/reports/sales-tags', name: 'reports-sales-tags', component: ReportsTags, meta: { title: 'Reports — Sales Tags', requiresAuth: true, roles: ['ADMIN', 'SUPERADMIN'], routeName: 'reports-sales-tags', need: 'view' } },
  { path: '/admin/reports/bank-ledger', name: 'reports-bank-ledger', component: ReportsBank, meta: { title: 'Reports — Bank Ledger', requiresAuth: true, roles: ['ADMIN', 'SUPERADMIN'], routeName: 'reports-bank-ledger', need: 'view' } },
  { path: '/admin/reports/expenses', name: 'reports-expenses', component: ReportsExp, meta: { title: 'Reports — Expenses', requiresAuth: true, roles: ['ADMIN', 'SUPERADMIN'], routeName: 'reports-expenses', need: 'view' } },
  { path: '/admin/reports/fnb-daily', name: 'reports-fnb-daily', component: ReportsFnb, meta: { title: 'Reports — FNB Daily', requiresAuth: true, roles: ['ADMIN', 'SUPERADMIN'], routeName: 'reports-fnb-daily', need: 'view' } },
  { path: '/admin/reports/rooms-summary', name: 'reports-rooms-summary', component: ReportsRooms, meta: { title: 'Reports — Rooms Summary', requiresAuth: true, roles: ['ADMIN', 'SUPERADMIN'], routeName: 'reports-rooms-summary', need: 'view' } },

  // HR
  { path: '/admin/hr/dashboard', name: 'admin-hr-dashboard', component: HrDashboard, meta: { title: 'HR Dashboard', requiresAuth: true, roles: ['HRADMIN', 'SUPERADMIN'], routeName: 'hr-dashboard', need: 'view' } },
  { path: '/admin/hr/employees', name: 'admin-hr-employees', component: HrEmployees, meta: { title: 'HR Employees', requiresAuth: true, roles: ['HRADMIN', 'SUPERADMIN'], routeName: 'hr-employees', need: 'view' } },
  { path: '/admin/hr/contracts', name: 'admin-hr-contracts', component: HrContracts, meta: { title: 'HR Contracts', requiresAuth: true, roles: ['HRADMIN', 'SUPERADMIN'], routeName: 'hr-contracts', need: 'edit' } },
  { path: '/admin/hr/records', name: 'admin-hr-records', component: HrRecords, meta: { title: 'HR Records', requiresAuth: true, roles: ['HRADMIN', 'SUPERADMIN'], routeName: 'hr-records', need: 'view' } },
  { path: '/admin/hr/account-link', name: 'admin-hr-account-link', component: HrAccountLink, meta: { title: 'HR Account Link', requiresAuth: true, roles: ['HRADMIN', 'SUPERADMIN'], routeName: 'hr-account-link', need: 'edit' } },

  // Users
  { path: '/admin/users', name: 'admin-users', component: Users, meta: { title: 'Users', requiresAuth: true, roles: ['SUPERADMIN'], routeName: 'users', need: 'admin' } },
  { path: '/admin/users/master', name: 'admin-users-master', component: UsersMaster, meta: { title: '사용자 기준정보 관리', requiresAuth: true, roles: ['SUPERADMIN'], routeName: 'users-master', need: 'admin' } },
  { path: '/admin/users/password-reset', name: 'admin-users-password-reset', component: ResetUserPassword, meta: { title: 'Reset Password', requiresAuth: true, roles: ['SUPERADMIN'], routeName: 'users-password-reset', need: 'admin' } },

  // System
  { path: '/admin/role-access', name: 'admin-role-access', component: RoleAccess, meta: { title: 'Role Access', requiresAuth: true, roles: ['SUPERADMIN'], routeName: 'role-access', need: 'admin' } },

  // Account
  { path: '/account/password', name: 'account-password', component: ChangePassword, meta: { title: 'Change Password', requiresAuth: true, roles: ['ADMIN', 'SUPERADMIN'], routeName: 'account-password', need: 'edit' } },

  // Fallback
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

// ────────────── Router Guard ──────────────
const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, _from, next) => {
  if (to.meta?.title) document.title = `Hotel Admin — ${to.meta.title}`

  const auth = useAuthStore()
  try { await auth.bootstrap() } catch {}

  const requiresAuth = to.meta?.requiresAuth !== false
  if (requiresAuth && !auth.isAuthenticated) {
    const redirect = encodeURIComponent(to.fullPath || '/')
    return next({ name: 'login', query: { redirect } })
  }

  if (requiresAuth && auth.isAuthenticated) {
    const tasks: Promise<any>[] = []
    if (!auth._effectiveLoaded) tasks.push(auth.loadEffectiveAccess())
    if (!auth._accessLoaded) tasks.push(auth.loadAccessMatrix())
    if (tasks.length) await Promise.allSettled(tasks)
  }

  const needRoles = (to.meta?.roles as string[] | undefined) || []
  const userRoles = (auth.user?.roles ?? []).map(r => r.toUpperCase())
  const isSuper = userRoles.includes('SUPERADMIN')
  const hasRole =
    isSuper || needRoles.length === 0 || needRoles.some(r => userRoles.includes(r.toUpperCase()))

  const needLevel: 'view' | 'edit' | 'admin' = (to.meta?.need as any) || 'view'
  const routeName: string =
    (to.meta?.routeName as string) ||
    (typeof to.name === 'string'
      ? to.name.replaceAll('/', '-').toLowerCase()
      : String(to.path).slice(1).replaceAll('/', '-').toLowerCase())

  const hasAccess = isSuper || auth.hasAccess(routeName, needLevel)

  if (requiresAuth && (!hasRole || !hasAccess)) return next({ name: 'forbidden' })
  next()
})

export default router
