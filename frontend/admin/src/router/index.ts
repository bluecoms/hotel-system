// ============================================================================
// File      : src/router/index.ts
// Version   : 2025.10-28 · v3.3 (SSOT Master 통합판 · DeptAccess 안정화)
// Purpose   : Hotel Admin — Router (DeptAccess 기반 접근제어 / SSOT 완성형)
// ----------------------------------------------------------------------------
// 목적:
//   • 부서 기반 접근제어(DeptAccess) 체계로 전체 라우팅 관리
//   • SUPERADMIN → 전면 접근 허용
//   • 일반 사용자는 /api/roles/access/effective 기반으로 routeName 단위 접근 제어
// ----------------------------------------------------------------------------
// 변경사항 (v3.3)
//   ✅ RankTable / SalaryGradeTable 라우트 제거 (MasterData.vue 통합)
//   ✅ MasterData.vue 단일 경로 유지 (/admin/users/master)
//   ✅ ContractTab.vue 누락 대응 (주석처리/파일 보강 안내 주석 추가)
//   ✅ DeptAccess Guard 로직 안정화 (bootstrap + effectiveDeptAccess 캐시)
// ----------------------------------------------------------------------------
// 주석 규칙 (SSOT):
//   • 주요 기능별 섹션(대시보드 / HR / 리포트 / 시스템 등)을 명확히 구분
//   • meta.routeName 은 백엔드 DeptAccess 정책의 key 값과 일치
//   • title 은 브라우저 탭 타이틀용 (Hotel Admin — {title})
// ============================================================================

import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getEffectiveDeptAccess, canAccessRoute } from '@/services/auth'

// ─────────────────────────────────────────────
// Lazy Imports (화면별 코드 스플리팅)
// ─────────────────────────────────────────────
const Login             = () => import('@/views/Auth/Login.vue')
const Forbidden         = () => import('@/views/Forbidden.vue')
const Dashboard         = () => import('@/views/Dashboard.vue')
const MyInfo            = () => import('@/views/Users/MyInfo.vue')
const Users             = () => import('@/views/Users/Users.vue')
const ResetUserPassword = () => import('@/views/Admin/ResetUserPassword.vue')

// 마감 관리
const ClosingBoard      = () => import('@/views/closing/Board.vue')
const ClosingCal        = () => import('@/views/closing/Closing.vue')
const ClosingMerge      = () => import('@/views/closing/merge/MergeHistory.vue')

// 리포트
const ReportsTags       = () => import('@/views/Reports/SalesTags.vue')
const ReportsBank       = () => import('@/views/Reports/BankLedger.vue')
const ReportsExp        = () => import('@/views/Reports/Expenses.vue')
const ReportsFnb        = () => import('@/views/Reports/FnbDaily.vue')
const ReportsRooms      = () => import('@/views/Reports/RoomsSummary.vue')

// HR (인사관리)
const HrDashboard       = () => import('@/views/Admin/HR/Dashboard.vue')
const HrEmployees       = () => import('@/views/Admin/HR/Employees.vue')
const HrContracts       = () => import('@/views/Admin/HR/Contracts.vue')
const HrRecords         = () => import('@/views/Admin/HR/Records.vue')
const HrAccountLink     = () => import('@/views/Admin/HR/AccountLink.vue')
// const ContractTab    = () => import('@/views/Admin/HR/ContractTab.vue') // ⚠️ 파일 존재 시만 사용

// 시스템 관리 / 기준정보
const UsersMaster       = () => import('@/views/Users/master/MasterData.vue')
const RoleAccess        = () => import('@/views/Admin/RoleAccess.vue')

// ============================================================================
// Routes 정의
// ----------------------------------------------------------------------------
// • meta.requresAuth = false → 로그인 필요 없음
// • meta.routeName    → DeptAccess 검사 키 (백엔드 권한 키와 동일해야 함)
// ============================================================================
const routes: RouteRecordRaw[] = [
  // ────────────── 인증 관련 ──────────────
  {
    path: '/login',
    name: 'login',
    component: Login,
    meta: { requiresAuth: false, title: '로그인', hideInMenu: true },
  },
  {
    path: '/forbidden',
    name: 'forbidden',
    component: Forbidden,
    meta: { requiresAuth: false, title: '접근 권한 없음', hideInMenu: true },
  },

  // ────────────── 대시보드 ──────────────
  {
    path: '/',
    name: 'dashboard',
    component: Dashboard,
    meta: { title: '대시보드', requiresAuth: true, routeName: 'dashboard-kpi' },
  },

  // ────────────── 마감 관리 ──────────────
  {
    path: '/closing',
    name: 'closing-cal',
    component: ClosingCal,
    meta: { title: '마감 캘린더', requiresAuth: true, routeName: 'closing-calendar' },
  },
  {
    path: '/closing/board',
    name: 'closing-board',
    component: ClosingBoard,
    meta: { title: '일별 마감 보드', requiresAuth: true, routeName: 'closing-day' },
  },
  {
    path: '/closing/merge',
    name: 'closing-merge',
    component: ClosingMerge,
    meta: { title: '병합 이력', requiresAuth: true, routeName: 'closing-merge' },
  },

  // ────────────── 리포트 ──────────────
  {
    path: '/admin/reports/sales-tags',
    name: 'reports-sales-tags',
    component: ReportsTags,
    meta: { title: '리포트 — 태그별 매출', requiresAuth: true, routeName: 'reports-sales-tags' },
  },
  {
    path: '/admin/reports/bank-ledger',
    name: 'reports-bank-ledger',
    component: ReportsBank,
    meta: { title: '리포트 — 입금 내역', requiresAuth: true, routeName: 'reports-bank-ledger' },
  },
  {
    path: '/admin/reports/expenses',
    name: 'reports-expenses',
    component: ReportsExp,
    meta: { title: '리포트 — 지출 내역', requiresAuth: true, routeName: 'reports-expenses' },
  },
  {
    path: '/admin/reports/fnb-daily',
    name: 'reports-fnb-daily',
    component: ReportsFnb,
    meta: { title: '리포트 — F&B 일별 매출', requiresAuth: true, routeName: 'reports-fnb-daily' },
  },
  {
    path: '/admin/reports/rooms-summary',
    name: 'reports-rooms-summary',
    component: ReportsRooms,
    meta: { title: '리포트 — 객실 매출 요약', requiresAuth: true, routeName: 'reports-rooms-summary' },
  },

  // ────────────── 인사 관리 (HR) ──────────────
  {
    path: '/admin/hr/dashboard',
    name: 'admin-hr-dashboard',
    component: HrDashboard,
    meta: { title: 'HR 대시보드', requiresAuth: true, routeName: 'hr-dashboard' },
  },
  {
    path: '/admin/hr/employees',
    name: 'admin-hr-employees',
    component: HrEmployees,
    meta: { title: '직원 목록', requiresAuth: true, routeName: 'hr-employees' },
  },
  {
    path: '/admin/hr/contracts',
    name: 'admin-hr-contracts',
    component: HrContracts,
    meta: { title: '계약 관리', requiresAuth: true, routeName: 'hr-contracts' },
  },
  {
    path: '/admin/hr/records',
    name: 'admin-hr-records',
    component: HrRecords,
    meta: { title: '근태 기록 관리', requiresAuth: true, routeName: 'hr-records' },
  },
  {
    path: '/admin/hr/account-link',
    name: 'admin-hr-account-link',
    component: HrAccountLink,
    meta: { title: '직원 ↔ 계정 매핑', requiresAuth: true, routeName: 'hr-account-link' },
  },

  // ────────────── 사용자 / 시스템 관리 ──────────────
  {
    path: '/admin/users',
    name: 'admin-users',
    component: Users,
    meta: { title: '사용자 목록', requiresAuth: true, routeName: 'users' },
  },
  {
    path: '/admin/users/master',
    name: 'admin-users-master',
    component: UsersMaster,
    meta: { title: '기준정보 관리', requiresAuth: true, routeName: 'users-master' },
  },
  {
    path: '/admin/users/password-reset',
    name: 'admin-users-password-reset',
    component: ResetUserPassword,
    meta: { title: '비밀번호 초기화', requiresAuth: true, routeName: 'users-password-reset' },
  },

  // ────────────── 권한 관리 ──────────────
  {
    path: '/admin/role-access',
    name: 'admin-role-access',
    component: RoleAccess,
    meta: { title: '권한 관리', requiresAuth: true, routeName: 'role-access' },
  },

  // ────────────── 내 계정 ──────────────
  {
    path: '/account/info',
    name: 'account-info',
    component: MyInfo,
    meta: { title: '내 정보', requiresAuth: true, routeName: 'account-info' },
  },

  // ────────────── 예외/기타 ──────────────
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

// ============================================================================
// Router 생성 및 Guard 설정 (DeptAccess 기반)
// ----------------------------------------------------------------------------
// • 로그인 체크 → bootstrap() 1회 호출 (auth 상태 복원)
// • SUPERADMIN 은 모든 route 통과
// • 일반 사용자는 effectiveDeptAccess 로 routeName 단위 접근 검증
// ============================================================================
const router = createRouter({
  history: createWebHistory(),
  routes,
})

// ────────────── DeptAccess Guard ──────────────
router.beforeEach(async (to, _from, next) => {
  // ① 페이지 타이틀 세팅
  if (to.meta?.title) document.title = `Hotel Admin — ${to.meta.title}`

  const auth = useAuthStore()

  // ② 초기화되지 않은 경우 → bootstrap 수행
  if (!auth.isInitialized) {
    try {
      await auth.bootstrap()
      auth.isInitialized = true
    } catch (err) {
      console.error('[RouterGuard] bootstrap failed:', err)
    }
  }

  // ③ 인증 필요 여부 확인
  const requiresAuth = to.meta?.requiresAuth !== false
  if (requiresAuth && !auth.isAuthenticated) {
    const redirect = encodeURIComponent(to.fullPath || '/')
    return next({ name: 'login', query: { redirect } })
  }

  // ④ SUPERADMIN → 전면 접근 허용
  const roles = (auth.user?.roles || []).map(r => r.toUpperCase())
  if (roles.includes('SUPERADMIN')) return next()

  // ⑤ DeptAccess 정보가 없으면 API 호출
  if (!(auth as any).effectiveDeptAccess) {
    try {
      ;(auth as any).effectiveDeptAccess = await getEffectiveDeptAccess()
    } catch (err) {
      console.error('[RouterGuard] DeptAccess load failed:', err)
      return next({ name: 'forbidden' })
    }
  }

  // ⑥ routeName 계산 (meta.routeName > name > path)
  const routeName: string =
    (to.meta?.routeName as string) ||
    (typeof to.name === 'string'
      ? to.name.replaceAll('/', '-').toLowerCase()
      : String(to.path).slice(1).replaceAll('/', '-').toLowerCase())

  // ⑦ DeptAccess 기반 접근권한 검사
  const hasAccess = canAccessRoute(routeName, (auth as any).effectiveDeptAccess)
  if (requiresAuth && !hasAccess) return next({ name: 'forbidden' })

  // ⑧ 통과
  next()
})

export default router
