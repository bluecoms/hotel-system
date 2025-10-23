// ============================================================================
// File      : src/router/index.ts
// Version   : 2025.11-04 · v4.0 (Menu=Router 1:1 동기화 · DeptAccess Guard Reactive)
// Purpose   : Hotel Admin — Router (DeptAccess 기반 접근제어 / 무한루프 완전 차단)
// ----------------------------------------------------------------------------
// 설계 요약 (SSOT 동기화)
//   • menu.ts 의 routeName / 경로(path)와 100% 동일하도록 라우트 정의
//   • meta.routeName 은 DeptAccess 권한 키와 반드시 일치
//   • 전역 가드는 스토어의 반응형 상태(auth.effectiveDeptAccess)만을 사용
//   • SUPERADMIN 즉시 통과, forbidden 루프 차단, 최초 bootstrap 보장
// ----------------------------------------------------------------------------
// 용어 정리
//   • effectiveDeptAccess : /api/roles/access/effective 응답(서버 계산) 반영 맵
//   • routeName           : DeptAccess 판단 키(백엔드 키와 동일)
//   • requiresAuth        : 로그인 필요 플래그(기본 true)
// ============================================================================

import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getEffectiveDeptAccess, canAccessRoute } from '@/services/auth'

// ─────────────────────────────────────────────
// Lazy Imports — menu.ts와 동일한 실제 경로 구성
//   • 대시보드/Closing/Reports/HR/Users/Role/Account 전부 명시
//   • 파일 경로는 현 구조 기준(프로젝트 실제 파일 존재 가정)
// ─────────────────────────────────────────────
const Login                 = () => import('@/views/Auth/Login.vue')
const Forbidden             = () => import('@/views/Forbidden.vue')
const Dashboard             = () => import('@/views/Dashboard.vue')

// Closing
const ClosingCal            = () => import('@/views/closing/Closing.vue')               // /closing
const ClosingBoard          = () => import('@/views/closing/Board.vue')                 // /closing/board
const ClosingMerge          = () => import('@/views/closing/merge/MergeHistory.vue')    // /closing/merge

// Reports
const ReportsTags           = () => import('@/views/Reports/SalesTags.vue')             // /admin/reports/sales-tags
const ReportsBank           = () => import('@/views/Reports/BankLedger.vue')            // /admin/reports/bank-ledger
const ReportsExp            = () => import('@/views/Reports/Expenses.vue')              // /admin/reports/expenses
const ReportsFnb            = () => import('@/views/Reports/FnbDaily.vue')              // /admin/reports/fnb-daily
const ReportsRooms          = () => import('@/views/Reports/RoomsSummary.vue')          // /admin/reports/rooms-summary

// HR
const HrDashboard           = () => import('@/views/Admin/HR/Dashboard.vue')            // /admin/hr/dashboard
const HrEmployees           = () => import('@/views/Admin/HR/Employees.vue')            // /admin/hr/employees
const HrContracts           = () => import('@/views/Admin/HR/Contracts.vue')            // /admin/hr/contracts
const HrRecords             = () => import('@/views/Admin/HR/Records.vue')              // /admin/hr/records
const HrAccountLink         = () => import('@/views/Admin/HR/AccountLink.vue')          // /admin/hr/account-link

// System / Users
const UsersList             = () => import('@/views/Users/Users.vue')                   // /admin/users
const MasterData            = () => import('@/views/Users/master/MasterData.vue')       // /admin/users/master
const ResetUserPassword     = () => import('@/views/Admin/ResetUserPassword.vue')       // /admin/users/password-reset

// Role / Account
const RoleAccess            = () => import('@/views/Admin/RoleAccess.vue')              // /admin/role-access
const MyInfo                = () => import('@/views/Users/MyInfo.vue')                  // /account/info

// ─────────────────────────────────────────────
// Routes — menu.ts 의 routeName/경로와 100% 일치
//   • meta.routeName 은 menu.ts의 routeName과 동일 문자열
//   • title 은 브라우저 탭 타이틀
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
  { path: '/admin/hr/dashboard',    name: 'hr-dashboard',    component: HrDashboard,  meta: { title: 'HR 대시보드', requiresAuth: true, routeName: 'hr-dashboard' } },
  { path: '/admin/hr/employees',    name: 'hr-employees',    component: HrEmployees,  meta: { title: '직원 목록',   requiresAuth: true, routeName: 'hr-employees' } },
  { path: '/admin/hr/contracts',    name: 'hr-contracts',    component: HrContracts,  meta: { title: '계약 관리',   requiresAuth: true, routeName: 'hr-contracts' } },
  { path: '/admin/hr/records',      name: 'hr-records',      component: HrRecords,    meta: { title: '근태 기록',   requiresAuth: true, routeName: 'hr-records' } },
  { path: '/admin/hr/account-link', name: 'hr-account-link', component: HrAccountLink,meta: { title: '계정 매핑',   requiresAuth: true, routeName: 'hr-account-link' } },

  // System / Users
  { path: '/admin/users',                name: 'users',                component: UsersList,        meta: { title: '사용자 목록',    requiresAuth: true, routeName: 'users' } },
  { path: '/admin/users/master',         name: 'users-master',         component: MasterData,       meta: { title: '기준정보 관리',  requiresAuth: true, routeName: 'users-master' } },
  { path: '/admin/users/password-reset', name: 'users-password-reset', component: ResetUserPassword,meta: { title: '비밀번호 초기화',  requiresAuth: true, routeName: 'users-password-reset' } },

  // Role / Account
  { path: '/admin/role-access', name: 'role-access', component: RoleAccess, meta: { title: '권한 관리', requiresAuth: true, routeName: 'role-access' } },
  { path: '/account/info',      name: 'account-info',component: MyInfo,     meta: { title: '내 정보',   requiresAuth: true, routeName: 'account-info' } },

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
// DeptAccess 기반 전역 가드 — 반응형 스토어만 사용(임시 캐시 금지)
//   • 저장 후 auth.bootstrap()이 갱신한 effectiveDeptAccess 가드가 즉시 사용
//   • SUPERADMIN 우선 통과, forbidden 루프 차단, 최초 bootstrap 보장
// ============================================================================
let isAccessError = false

router.beforeEach(async (to, from, next) => {
  // ① Title
  if (to.meta?.title) document.title = `Hotel Admin — ${to.meta.title}`

  const auth = useAuthStore()

  // ② forbidden 루프 차단
  if (to.name === 'forbidden' && from.name === 'forbidden') return next(false)

  // ③ bootstrap 1회 보장
  if (!auth.isInitialized) {
    try { await auth.bootstrap() } catch (err) { console.warn('[guard] bootstrap failed:', err) }
    auth.isInitialized = true
  }

  // ④ 인증 필요 검사
  const requiresAuth = to.meta?.requiresAuth !== false
  if (requiresAuth && !auth.isAuthenticated) {
    if (to.name !== 'login') return next({ name: 'login', query: { redirect: encodeURIComponent(to.fullPath || '/') } })
    return next()
  }

  // ⑤ SUPERADMIN 즉시 통과
  if ((auth.user?.roles || []).map(r => r.toUpperCase()).includes('SUPERADMIN')) return next()

  // ⑥ 권한맵 확보(반응형 스토어만 사용)
  if (!auth.effectiveDeptAccess && !isAccessError) {
    try { auth.effectiveDeptAccess = await getEffectiveDeptAccess() }
    catch (err) {
      console.error('[guard] effective access load failed:', err)
      isAccessError = true
      if (to.name !== 'forbidden') return next({ name: 'forbidden' })
      return next(false)
    }
  }

  // ⑦ routeName 계산(meta.routeName > name > path → 하이픈화)
  const routeName: string =
    (to.meta?.routeName as string) ||
    (typeof to.name === 'string'
      ? to.name.replaceAll('/', '-').toLowerCase()
      : String(to.path).slice(1).replaceAll('/', '-').toLowerCase())

  // ⑧ 접근 허용 여부 판단
  const ok = canAccessRoute(routeName, auth.effectiveDeptAccess, auth.user?.roles || null)
  if (requiresAuth && !ok) {
    if (to.name !== 'forbidden') return next({ name: 'forbidden' })
    return next(false)
  }

  // ⑨ 통과
  next()
})

export default router
