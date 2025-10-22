// ============================================================================
// File      : src/router/index.ts
// Version   : 2025.11-02 · v3.7 (DeptAccess Guard 안정판 · 권한관리 라우트 추가)
// Purpose   : Hotel Admin — Router (DeptAccess 기반 접근제어 / 무한루프 완전 차단)
// ----------------------------------------------------------------------------
// 설계 요약
//   1) Title 세팅
//   2) forbidden ↔ forbidden 루프 차단
//   3) bootstrap 최초 1회 보장 (실패해도 isInitialized=true 강제)
//   4) 인증 필요 라우트: 미인증이면 /login (redirect 파라미터 포함)
//   5) SUPERADMIN 즉시 통과
//   6) DeptAccess 캐시 없으면 API 1회 호출 (실패시 1번만 /forbidden, 이후 중단)
//   7) routeName 계산(meta.routeName > name > path) → canAccessRoute 검사
//   8) 접근 거부 시 /forbidden (이미 forbidden이면 네비게이션 중단)
// ----------------------------------------------------------------------------
// 왜 next(false) ?
/*
  - Router 가드 내부에서 redirect(next({ name: 'forbidden' }))를 수행하면
    그 다음 네비게이션에도 beforeEach가 다시 불리며, 또 실패 → 또 redirect…
    이런 “실패-리다이렉트-가드재실행”의 연쇄를 끊기 위해
    ‘마지막 forbidden 화면에 도달했을 때’는 next(false)로 “이번 네비게이션만 중지”한다.
    (주소창/히스토리는 그대로 유지되며, 루프가 발생하지 않는다)
*/
// ----------------------------------------------------------------------------
// 용어 정리
//   • effectiveDeptAccess : /api/roles/access/effective 응답을 반영한 실효 접근맵
//   • routeName           : DeptAccess 판단 키(백엔드 키와 반드시 동일하게 유지)
// ============================================================================

import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getEffectiveDeptAccess, canAccessRoute } from '@/services/auth'

// ─────────────────────────────────────────────
// Lazy Imports (필요 화면만 발췌, 나머지는 기존과 동일)
// ─────────────────────────────────────────────
const Login             = () => import('@/views/Auth/Login.vue')
const Forbidden         = () => import('@/views/Forbidden.vue')
const Dashboard         = () => import('@/views/Dashboard.vue')
const MyInfo            = () => import('@/views/Users/MyInfo.vue')
const Users             = () => import('@/views/Users/Users.vue')
const ResetUserPassword = () => import('@/views/Admin/ResetUserPassword.vue')

// ✅ 권한 관리(DeptAccess 관리) 화면 추가
const RoleAccess        = () => import('@/views/Admin/RoleAccess.vue')

// ─────────────────────────────────────────────
// Routes 정의
//   • meta.requiresAuth === false : 로그인 불필요
//   • meta.routeName              : DeptAccess 검사 키(백엔드 정의와 동일해야 함)
//   • title                       : 브라우저 탭 타이틀 (Hotel Admin — {title})
// ─────────────────────────────────────────────
const routes: RouteRecordRaw[] = [
  // 인증/예외
  { path: '/login',     name: 'login',     component: Login,     meta: { requiresAuth: false, title: '로그인',     hideInMenu: true } },
  { path: '/forbidden', name: 'forbidden', component: Forbidden, meta: { requiresAuth: false, title: '접근 거부',   hideInMenu: true } },

  // 기본(대시보드)
  { path: '/', name: 'dashboard', component: Dashboard, meta: { title: '대시보드', requiresAuth: true, routeName: 'dashboard-kpi' } },

  // 내 계정
  { path: '/account/info', name: 'account-info', component: MyInfo, meta: { title: '내 정보', requiresAuth: true, routeName: 'account-info' } },

  // 사용자/시스템
  { path: '/admin/users',                name: 'admin-users',               component: Users,             meta: { title: '사용자 목록',     requiresAuth: true, routeName: 'users' } },
  { path: '/admin/users/password-reset', name: 'admin-users-password-reset', component: ResetUserPassword, meta: { title: '비밀번호 초기화',   requiresAuth: true, routeName: 'users-password-reset' } },

  // ✅ 권한 관리(DeptAccess) — 백엔드 키와 정확히 일치: routeName = 'role-access'
  { path: '/admin/role-access',          name: 'role-access',               component: RoleAccess,        meta: { title: '권한 관리',       requiresAuth: true, routeName: 'role-access' } },

  // 예외
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

// ─────────────────────────────────────────────
// Router 생성
// ─────────────────────────────────────────────
const router = createRouter({
  history: createWebHistory(),
  routes,
})

/**
 * DeptAccess API 실패 플래그
 * - 실패 후 forbidden으로 “한 번” 보낸 뒤, 연쇄 네비게이션을 차단하기 위한 상태.
 * - 새로고침(전체 리로드) 전까지 유지된다.
 */
let isAccessError = false

// ============================================================================
// Global Router Guard (DeptAccess 기반 접근제어)
// ============================================================================
// “단 하나의 진입점”에서 인증/권한/루프 방지를 모두 처리한다.
router.beforeEach(async (to, from, next) => {
  // ① 문서 타이틀
  if (to.meta?.title) document.title = `Hotel Admin — ${to.meta.title}`

  const auth = useAuthStore()

  // ② forbidden → forbidden 루프 차단
  //   - 이미 /forbidden에 머무는 중이면 더 이상 진행하지 않는다.
  if (to.name === 'forbidden' && from.name === 'forbidden') {
    return next(false) // 현재 네비게이션만 중단
  }

  // ③ 부트스트랩(최초 1회)
  //   - 실패해도 isInitialized=true 로 마킹하여 재시도 루프를 막는다.
  if (!auth.isInitialized) {
    try {
      await auth.bootstrap()
    } catch (err) {
      console.warn('[RouterGuard] bootstrap failed:', err)
    } finally {
      auth.isInitialized = true
    }
  }

  // ④ 인증 요구 라우트인가?
  //   - requiresAuth가 명시적으로 false가 아니면 인증 필요로 본다.
  const requiresAuth = to.meta?.requiresAuth !== false
  if (requiresAuth && !auth.isAuthenticated) {
    // 로그인 페이지로 이동 (원래 경로는 redirect 파라미터로 보존)
    if (to.name !== 'login') {
      const redirect = encodeURIComponent(to.fullPath || '/')
      return next({ name: 'login', query: { redirect } })
    }
    return next()
  }

  // ⑤ SUPERADMIN 전면 통과
  //   - SUPERADMIN은 DeptAccess 검사 자체를 건너뛴다.
  const roles = (auth.user?.roles || []).map(r => r.toUpperCase())
  if (roles.includes('SUPERADMIN')) return next()

  // ⑥ DeptAccess 로드 (캐시 미존재 시 1회 호출)
  //   - 실패 시: 최초 1회만 /forbidden으로 보낸다.
  //   - /forbidden 도착 이후에는 next(false)로 네비게이션을 중단하여 루프 방지.
  if (!(auth as any).effectiveDeptAccess && !isAccessError) {
    try {
      ;(auth as any).effectiveDeptAccess = await getEffectiveDeptAccess()
    } catch (err) {
      console.error('[RouterGuard] DeptAccess load failed:', err)
      isAccessError = true
      if (to.name !== 'forbidden') return next({ name: 'forbidden' })
      return next(false)
    }
  }

  // ⑦ DeptAccess 키(routeName) 계산
  //   - 우선순위: meta.routeName > name → path
  //   - name/path 기반이면 슬래시를 하이픈으로 정규화하여 서버 키와 동일하게 맞춘다.
  const routeName: string =
    (to.meta?.routeName as string) ||
    (typeof to.name === 'string'
      ? to.name.replaceAll('/', '-').toLowerCase()
      : String(to.path).slice(1).replaceAll('/', '-').toLowerCase())

  // ⑧ 실효 접근맵으로 접근 가능 여부 검사
  //   - 접근 거부 시 /forbidden으로 1회 이동
  //   - 이미 forbidden이라면 더 이상 진행하지 않고 중단(next(false))
  const hasAccess = canAccessRoute(
    routeName,
    (auth as any).effectiveDeptAccess,
    auth.user?.roles || null // v3.8: SUPERADMIN 우선 통과 추가 파라미터(services/auth.ts 호환)
  )

  if (requiresAuth && !hasAccess) {
    if (to.name !== 'forbidden') return next({ name: 'forbidden' })
    return next(false)
  }

  // ⑨ 통과
  next()
})

// ============================================================================
// End of File — src/router/index.ts
// ============================================================================
export default router
