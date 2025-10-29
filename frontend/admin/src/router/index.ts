// ============================================================================
// File      : src/router/index.ts
// Version   : 2025.11-10 · v4.3 (Housekeeping History/Assign Added · HR Cleanup)
// Purpose   : Hotel Admin — Router (DeptAccess 기반 접근제어 / SSOT 완전 동기화)
// ----------------------------------------------------------------------------
// 주요 변경사항 (v4.3)
//   ✅ HR: 계정 매핑(AccountLink) 라우트 제거
//   ✅ Housekeeping: 현황(Board) + 이력(History) + 배정(Assign) 추가
//   ✅ menu.ts 완전 동기화 (routeName 기준 일치)
// ----------------------------------------------------------------------------
// 전제:
//   • menu.ts 와 routeName / path 100% 동일
//   • DeptAccess 권한 키(routeName)는 백엔드 DeptAccess 정책 키와 동일
//   • SUPERADMIN / 개발환경(dev): 전면 접근 허용
// ============================================================================

import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getEffectiveDeptAccess, canAccessRoute } from '@/services/auth'

// ─────────────────────────────────────────────
// Lazy Imports
// ─────────────────────────────────────────────
const Login             = () => import('@/views/Auth/Login.vue')
const Forbidden         = () => import('@/views/Forbidden.vue')
const Dashboard         = () => import('@/views/Dashboard.vue')

// Closing
const ClosingCal        = () => import('@/views/closing/Closing.vue')
const ClosingBoard      = () => import('@/views/closing/Board.vue')
const ClosingMerge      = () => import('@/views/closing/merge/MergeHistory.vue')

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

// System / Users
const UsersList         = () => import('@/views/Users/Users.vue')
const MasterData        = () => import('@/views/Users/master/MasterData.vue')
const ResetUserPassword = () => import('@/views/Admin/ResetUserPassword.vue')

// Role / Account
const RoleAccess        = () => import('@/views/Admin/RoleAccess.vue')
const MyInfo            = () => import('@/views/Users/MyInfo.vue')

// ✅ Housekeeping
const HousekeepingBoard   = () => import('@/views/HousekeepingBoard.vue')
const HousekeepingHistory = () => import('@/views/HousekeepingHistory.vue')
const HousekeepingAssign  = () => import('@/views/HousekeepingAssign.vue')

// ─────────────────────────────────────────────
// Routes
// ─────────────────────────────────────────────
const routes: RouteRecordRaw[] = [
  // 인증/예외
  { path: '/login', name: 'login', component: Login, meta: { requiresAuth: false, title: '로그인', hideInMenu: true } },
  { path: '/forbidden', name: 'forbidden', component: Forbidden, meta: { requiresAuth: false, title: '접근 거부', hideInMenu: true } },

  // 대시보드
  { path: '/', name: 'dashboard', component: Dashboard, meta: { title: '대시보드', requiresAuth: true, routeName: 'dashboard-kpi' } },

  // Closing
  { path: '/closing',        name: 'closing-calendar', component: ClosingCal,   meta: { title: '마감 캘린더',  requiresAuth: true, routeName: 'closing-calendar' } },
  { path: '/closing/board',  name: 'closing-day',      component: ClosingBoard, meta: { title: '일별 보드',    requiresAuth: true, routeName: 'closing-day' } },
  { path: '/closing/merge',  name: 'closing-merge',    component: ClosingMerge, meta: { title: '병합 이력',    requiresAuth: true, routeName: 'closing-merge' } },

  // Reports
  { path: '/admin/reports/sales-tags',    name: 'reports-sales-tags',    component: ReportsTags,  meta: { title: '태그별 매출',     requiresAuth: true, routeName: 'reports-sales-tags' } },
  { path: '/admin/reports/bank-ledger',   name: 'reports-bank-ledger',   component: ReportsBank,  meta: { title: '입금내역',       requiresAuth: true, routeName: 'reports-bank-ledger' } },
  { path: '/admin/reports/expenses',      name: 'reports-expenses',      component: ReportsExp,   meta: { title: '지출내역',       requiresAuth: true, routeName: 'reports-expenses' } },
  { path: '/admin/reports/fnb-daily',     name: 'reports-fnb-daily',     component: ReportsFnb,   meta: { title: 'F&B 일별 매출',  requiresAuth: true, routeName: 'reports-fnb-daily' } },
  { path: '/admin/reports/rooms-summary', name: 'reports-rooms-summary', component: ReportsRooms, meta: { title: '객실 매출 요약', requiresAuth: true, routeName: 'reports-rooms-summary' } },

  // HR
  { path: '/admin/hr/dashboard', name: 'hr-dashboard', component: HrDashboard, meta: { title: 'HR 대시보드', requiresAuth: true, routeName: 'hr-dashboard' } },
  { path: '/admin/hr/employees', name: 'hr-employees', component: HrEmployees, meta: { title: '직원 목록',   requiresAuth: true, routeName: 'hr-employees' } },
  { path: '/admin/hr/contracts', name: 'hr-contracts', component: HrContracts, meta: { title: '계약 관리',   requiresAuth: true, routeName: 'hr-contracts' } },
  { path: '/admin/hr/records',   name: 'hr-records',   component: HrRecords,   meta: { title: '근태 기록',   requiresAuth: true, routeName: 'hr-records' } },

  // System / Users
  { path: '/admin/users',                name: 'users',                component: UsersList,        meta: { title: '사용자 목록',    requiresAuth: true, routeName: 'users' } },
  { path: '/admin/users/master',         name: 'users-master',         component: MasterData,       meta: { title: '기준정보 관리',  requiresAuth: true, routeName: 'users-master' } },
  { path: '/admin/users/password-reset', name: 'users-password-reset', component: ResetUserPassword,meta: { title: '비밀번호 초기화',  requiresAuth: true, routeName: 'users-password-reset' } },

  // Role / Account
  { path: '/admin/role-access', name: 'role-access', component: RoleAccess, meta: { title: '권한 관리', requiresAuth: true, routeName: 'role-access' } },
  { path: '/account/info',      name: 'account-info',component: MyInfo,     meta: { title: '내 정보',   requiresAuth: true, routeName: 'account-info' } },

  // ✅ Housekeeping
  { path: '/admin/housekeeping',             name: 'housekeeping',          component: HousekeepingBoard,   meta: { title: '객실 정비 현황', requiresAuth: true, routeName: 'housekeeping' } },
  { path: '/admin/housekeeping/history',     name: 'housekeeping-history',  component: HousekeepingHistory, meta: { title: '정비 이력',       requiresAuth: true, routeName: 'housekeeping-history' } },
  { path: '/admin/housekeeping/assign',      name: 'housekeeping-assign',   component: HousekeepingAssign,  meta: { title: '정비 배정',       requiresAuth: true, routeName: 'housekeeping-assign' } },

  // Fallback
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

// ─────────────────────────────────────────────
// Router 생성
// ─────────────────────────────────────────────
const router = createRouter({
  history: createWebHistory(),
  routes,
})

// ============================================================================
// 전역 가드 (DeptAccess + SUPERADMIN 예외 + DEV AutoAllow)
// ============================================================================
let isAccessError = false

router.beforeEach(async (to, from, next) => {
  if (to.meta?.title) document.title = `Hotel Admin — ${to.meta.title}`

  const auth = useAuthStore()
  if (to.name === 'forbidden' && from.name === 'forbidden') return next(false)

  // 초기 부트스트랩
  if (!auth.isInitialized) {
    try { await auth.bootstrap() } catch (err) { console.warn('[guard] bootstrap failed:', err) }
    auth.isInitialized = true
  }

  // 인증 필요 라우트 검사
  const requiresAuth = to.meta?.requiresAuth !== false
  if (requiresAuth && !auth.isAuthenticated) {
    if (to.name !== 'login')
      return next({ name: 'login', query: { redirect: encodeURIComponent(to.fullPath || '/') } })
    return next()
  }

  // SUPERADMIN / DEV 모드 예외처리
  const isSuper = (auth.user?.roles || []).map(r => r.toUpperCase()).includes('SUPERADMIN')
  const isDevMode = import.meta.env.MODE === 'development' || import.meta.env.DEV
  if (isSuper || isDevMode) return next()

  // 권한맵 로드
  if (!auth.effectiveDeptAccess && !isAccessError) {
    try { auth.effectiveDeptAccess = await getEffectiveDeptAccess() }
    catch (err) {
      console.error('[guard] effective access load failed:', err)
      isAccessError = true
      if (to.name !== 'forbidden') return next({ name: 'forbidden' })
      return next(false)
    }
  }

  // DeptAccess 검증
  const routeName: string =
    (to.meta?.routeName as string) ||
    (typeof to.name === 'string'
      ? to.name.replaceAll('/', '-').toLowerCase()
      : String(to.path).slice(1).replaceAll('/', '-').toLowerCase())

  const ok = canAccessRoute(routeName, auth.effectiveDeptAccess, auth.user?.roles || null)
  if (requiresAuth && !ok) {
    if (to.name !== 'forbidden') return next({ name: 'forbidden' })
    return next(false)
  }

  next()
})

export default router
