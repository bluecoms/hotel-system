// ============================================================================
// File      : src/router/menu.ts
// Version   : 2025.11-08 · v3.7 (Housekeeping Grouped · Sidebar Expand Fix)
// Purpose   : Hotel Admin — Sidebar Menu (DeptAccess 기반 / SSOT 완전판)
// ----------------------------------------------------------------------------
// 목적:
//   • router/index.ts 의 meta.routeName 과 100% 일치하는 메뉴 정의
//   • DeptAccess 권한 키(routeName) 정합성 유지
//   • 하우스키핑(객실정비) 업무 메뉴를 그룹(children) 구조로 변경하여
//     사이드바에서 하위 메뉴가 펼쳐지도록 수정
// ----------------------------------------------------------------------------
// 정책:
//   • SUPERADMIN: 전 메뉴 접근 가능
//   • ADMIN     : 일반 운영 메뉴 접근 가능
//   • HK        : 하우스키핑 부서 전용 메뉴 접근 가능
// ----------------------------------------------------------------------------
// 구조 요약:
//   - 대시보드: 단일
//   - 마감 관리: 그룹(children)
//   - 리포트: 그룹(children)
//   - 하우스키핑: 그룹(children) ← 이번 수정의 핵심
//   - 인사 관리: 그룹(children)
//   - 시스템 관리: 그룹(children)
//   - 권한 관리: 단일
//   - 내 계정: 그룹(children)
// ============================================================================

export type NavItem = {
  label: string
  to?: string
  icon?: string
  roles?: string[]
  routeName?: string
  children?: NavItem[]
}

// ----------------------------------------------------------------------------
// Sidebar 메뉴 정의 (router.meta.routeName 과 완전 동기화)
// ----------------------------------------------------------------------------
const menu: NavItem[] = [
  // ─────────────────────────────
  // 대시보드
  // ─────────────────────────────
  {
    label: '대시보드',
    to: '/',
    icon: 'mdi-view-dashboard-outline',
    roles: ['ADMIN', 'SUPERADMIN'],
    routeName: 'dashboard-kpi',
  },

  // ─────────────────────────────
  // 마감 관리
  // ─────────────────────────────
  {
    label: '마감 관리',
    icon: 'mdi-calendar-check-outline',
    roles: ['ADMIN', 'SUPERADMIN'],
    children: [
      { label: '마감 캘린더', to: '/closing', icon: 'mdi-calendar-month-outline', routeName: 'closing-calendar' },
      { label: '일별 보드', to: '/closing/board', icon: 'mdi-clipboard-text-clock-outline', routeName: 'closing-day' },
      { label: '병합 이력', to: '/closing/merge', icon: 'mdi-database-sync', roles: ['SUPERADMIN'], routeName: 'closing-merge' },
    ],
  },

  // ─────────────────────────────
  // 리포트
  // ─────────────────────────────
  {
    label: '리포트',
    icon: 'mdi-chart-areaspline',
    roles: ['ADMIN', 'SUPERADMIN'],
    children: [
      { label: '태그별 매출', to: '/admin/reports/sales-tags', icon: 'mdi-tag-text-outline', routeName: 'reports-sales-tags' },
      { label: '입금내역', to: '/admin/reports/bank-ledger', icon: 'mdi-bank-transfer', routeName: 'reports-bank-ledger' },
      { label: '지출내역', to: '/admin/reports/expenses', icon: 'mdi-cash-multiple', routeName: 'reports-expenses' },
      { label: 'F&B 일별 매출', to: '/admin/reports/fnb-daily', icon: 'mdi-silverware-fork-knife', routeName: 'reports-fnb-daily' },
      { label: '객실 매출 요약', to: '/admin/reports/rooms-summary', icon: 'mdi-bed-outline', routeName: 'reports-rooms-summary' },
    ],
  },

  // ─────────────────────────────
  // ✅ 하우스키핑 (Housekeeping)
  // ----------------------------------------------------------------------------
  // • 단일 메뉴에서 그룹(children) 구조로 변경
  // • 사이드바에서 하위 메뉴(현황/이력) 펼침 가능
  // ----------------------------------------------------------------------------
  {
    label: '하우스키핑',
    icon: 'mdi-broom',
    roles: ['HK', 'ADMIN', 'SUPERADMIN'],
    children: [
      {
        label: '객실 정비 현황',
        to: '/admin/housekeeping',
        icon: 'mdi-broom',
        roles: ['HK', 'ADMIN', 'SUPERADMIN'],
        routeName: 'housekeeping',
      },
      {
        label: '정비 이력',
        to: '/admin/housekeeping/history',
        icon: 'mdi-clipboard-text-clock-outline',
        roles: ['HK', 'ADMIN', 'SUPERADMIN'],
        routeName: 'housekeeping-history',
      },
    ],
  },

  // ─────────────────────────────
  // 인사 관리 (HR)
  // ─────────────────────────────
  {
    label: '인사 관리',
    icon: 'mdi-account-group-outline',
    roles: ['HRADMIN', 'SUPERADMIN'],
    children: [
      { label: 'HR 대시보드', to: '/admin/hr/dashboard', icon: 'mdi-view-dashboard-variant-outline', routeName: 'hr-dashboard' },
      { label: '직원 목록', to: '/admin/hr/employees', icon: 'mdi-account-tie', routeName: 'hr-employees' },
      { label: '계약 관리', to: '/admin/hr/contracts', icon: 'mdi-file-sign', routeName: 'hr-contracts' },
      { label: '근태 기록', to: '/admin/hr/records', icon: 'mdi-file-document-multiple-outline', routeName: 'hr-records' },
      { label: '계정 매핑', to: '/admin/hr/account-link', icon: 'mdi-account-arrow-right', routeName: 'hr-account-link' },
    ],
  },

  // ─────────────────────────────
  // 시스템 관리
  // ─────────────────────────────
  {
    label: '시스템 관리',
    icon: 'mdi-account-cog-outline',
    roles: ['SUPERADMIN'],
    children: [
      { label: '사용자 목록', to: '/admin/users', icon: 'mdi-account-multiple-outline', routeName: 'users' },
      { label: '기준정보 관리', to: '/admin/users/master', icon: 'mdi-database-cog-outline', routeName: 'users-master' },
      { label: '비밀번호 초기화', to: '/admin/users/password-reset', icon: 'mdi-lock-reset', routeName: 'users-password-reset' },
    ],
  },

  // ─────────────────────────────
  // 권한 관리
  // ─────────────────────────────
  {
    label: '권한 관리',
    to: '/admin/role-access',
    icon: 'mdi-shield-account-outline',
    roles: ['SUPERADMIN'],
    routeName: 'role-access',
  },

  // ─────────────────────────────
  // 내 계정
  // ─────────────────────────────
  {
    label: '내 계정',
    icon: 'mdi-account-cog-outline',
    roles: ['ADMIN', 'SUPERADMIN'],
    children: [
      { label: '내 정보', to: '/account/info', icon: 'mdi-account-circle', routeName: 'account-info' },
    ],
  },
]

// ============================================================================
// Export
// ============================================================================
export default menu
