// src/router/menu.ts
// ===========================================================
// Hotel Admin — Sidebar Menu (v2025 Full Spec, Updated 2025-10)
//  - 통합 HR/Users/OTA/Closing/Reports/System
//  - SUPERADMIN / HRADMIN / ADMIN Role 기반
// ===========================================================

export type NavItem = {
  label: string
  to?: string
  icon?: string
  roles?: string[]
  routeName?: string
  children?: NavItem[]
}

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
      {
        label: '마감 캘린더',
        to: '/closing',
        icon: 'mdi-calendar-month-outline',
        routeName: 'closing-calendar',
      },
      {
        label: '일별 보드',
        to: '/closing/board',
        icon: 'mdi-clipboard-text-clock-outline',
        routeName: 'closing-day',
      },
      {
        label: '병합 이력',
        to: '/closing/merge',
        icon: 'mdi-database-sync',
        roles: ['SUPERADMIN'],
        routeName: 'closing-merge',
      },
    ],
  },

  // ─────────────────────────────
  // OTA 관리
  // ─────────────────────────────
  {
    label: 'OTA 관리',
    icon: 'mdi-earth',
    roles: ['ADMIN', 'SUPERADMIN'],
    children: [
      {
        label: '판매 채널 요약',
        to: '/ota',
        icon: 'mdi-chart-timeline-variant-shimmer',
        routeName: 'ota-sales',
      },
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
      {
        label: '태그별 매출',
        to: '/admin/reports/sales-tags',
        icon: 'mdi-tag-text-outline',
        routeName: 'reports-sales-tags',
      },
      {
        label: '입금내역',
        to: '/admin/reports/bank-ledger',
        icon: 'mdi-bank-transfer',
        routeName: 'reports-bank-ledger',
      },
      {
        label: '지출내역',
        to: '/admin/reports/expenses',
        icon: 'mdi-cash-multiple',
        routeName: 'reports-expenses',
      },
      {
        label: 'F&B 일별 매출',
        to: '/admin/reports/fnb-daily',
        icon: 'mdi-silverware-fork-knife',
        routeName: 'reports-fnb-daily',
      },
      {
        label: '객실 매출 요약',
        to: '/admin/reports/rooms-summary',
        icon: 'mdi-bed-outline',
        routeName: 'reports-rooms-summary',
      },
    ],
  },

  // ─────────────────────────────
  // 인사 관리
  // ─────────────────────────────
  {
    label: '인사 관리',
    icon: 'mdi-account-group-outline',
    roles: ['HRADMIN', 'SUPERADMIN'],
    children: [
      {
        label: 'HR 대시보드',
        to: '/admin/hr/dashboard',
        icon: 'mdi-view-dashboard-variant-outline',
        routeName: 'hr-dashboard',
      },
      {
        label: '직원 목록',
        to: '/admin/hr/employees',
        icon: 'mdi-account-tie',
        routeName: 'hr-employees',
      },
      {
        label: '계약 관리',
        to: '/admin/hr/contracts',
        icon: 'mdi-file-sign',
        routeName: 'hr-contracts',
      },
      {
        label: '인사 기록',
        to: '/admin/hr/records',
        icon: 'mdi-file-document-multiple-outline',
        routeName: 'hr-records',
      },
      {
        label: '계정 매핑',
        to: '/admin/hr/account-link',
        icon: 'mdi-account-arrow-right-outline',
        routeName: 'hr-account-link',
      },
    ],
  },

  // ─────────────────────────────
  // 사용자 관리
  // ─────────────────────────────
  {
    label: '사용자 관리',
    icon: 'mdi-account-multiple-outline',
    roles: ['SUPERADMIN'],
    children: [
      {
        label: '사용자 목록',
        to: '/admin/users',
        icon: 'mdi-account-cog-outline',
        routeName: 'users',
      },
      {
        label: '비밀번호 초기화',
        to: '/admin/users/password-reset',
        icon: 'mdi-lock-reset',
        routeName: 'users-password-reset',
      },
      {
        label: '기준정보 관리',
        to: '/admin/users/master',
        icon: 'mdi-database-cog-outline',
        routeName: 'users-master',
      },
    ],
  },

  // ─────────────────────────────
  // 시스템 설정
  // ─────────────────────────────
  {
    label: '시스템 설정',
    icon: 'mdi-shield-crown-outline',
    roles: ['SUPERADMIN'],
    children: [
      {
        label: '역할별 접근 권한',
        to: '/admin/role-access',
        icon: 'mdi-lock-check-outline',
        routeName: 'role-access',
      },
    ],
  },

  // ─────────────────────────────
  // 내 계정
  // ─────────────────────────────
  {
    label: '내 계정',
    icon: 'mdi-account-cog-outline',
    roles: ['ADMIN', 'SUPERADMIN'],
    children: [
      {
        label: '비밀번호 변경',
        to: '/account/password',
        icon: 'mdi-key-change',
        routeName: 'account-password',
      },
    ],
  },
]

export default menu
