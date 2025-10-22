// ============================================================================
// File      : src/router/menu.ts
// Version   : 2025.10-31 · v3.5 (SSOT Router 동기화 · DeptAccess Key 정합성)
// Purpose   : Hotel Admin — Sidebar Menu (DeptAccess 기반 / SSOT 완전판)
// ----------------------------------------------------------------------------
// 목적:
//   • router/index.ts 의 meta.routeName 과 100% 일치하는 메뉴 정의
//   • /admin/users/master 단일 진입점으로 기준정보 통합 (Rank/SalaryGrade 제거)
//   • DeptAccess 키(routeName) 오탈자/접두어 불일치로 인한 Forbidden 루프 예방
// ----------------------------------------------------------------------------
// 정책:
//   • SUPERADMIN: 전 메뉴 접근 가능 (FULL)
//   • ADMIN     : 대시보드/마감/리포트/계정 등 접근 가능
//   • HRADMIN   : HR(인사관리) 전용 메뉴 접근 가능
// ----------------------------------------------------------------------------
// SSOT 규칙:
//   • routeName 은 반드시 router/index.ts 의 meta.routeName 과 동일
//   • 라벨/아이콘은 UI 목적, 접근 판단은 DeptAccess + roles 로만 수행
// ============================================================================

export type NavItem = {
  label: string
  to?: string
  icon?: string
  roles?: string[]           // 접근 허용 역할 (UI 표시 필터용)
  routeName?: string         // ✅ DeptAccess 권한 키 (router meta.routeName 과 일치)
  children?: NavItem[]       // 하위 메뉴
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
    routeName: 'dashboard-kpi', // router: meta.routeName='dashboard-kpi'
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
        routeName: 'closing-calendar', // router와 일치
      },
      {
        label: '일별 보드',
        to: '/closing/board',
        icon: 'mdi-clipboard-text-clock-outline',
        routeName: 'closing-day', // router와 일치
      },
      {
        label: '병합 이력',
        to: '/closing/merge',
        icon: 'mdi-database-sync',
        roles: ['SUPERADMIN'],
        routeName: 'closing-merge', // router와 일치
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
  // 인사 관리 (HR)
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
        routeName: 'hr-dashboard', // ✅ admin-hr-dashboard → hr-dashboard 로 교정
      },
      {
        label: '직원 목록',
        to: '/admin/hr/employees',
        icon: 'mdi-account-tie',
        routeName: 'hr-employees', // ✅ admin-hr-employees → hr-employees
      },
      {
        label: '계약 관리',
        to: '/admin/hr/contracts',
        icon: 'mdi-file-sign',
        routeName: 'hr-contracts', // ✅ admin-hr-contracts → hr-contracts
      },
      {
        label: '근태 기록',
        to: '/admin/hr/records',
        icon: 'mdi-file-document-multiple-outline',
        routeName: 'hr-records', // ✅ admin-hr-records → hr-records
      },
      {
        label: '계정 매핑',
        to: '/admin/hr/account-link',
        icon: 'mdi-account-arrow-right',
        routeName: 'hr-account-link', // ✅ admin-hr-account-link → hr-account-link
      },
    ],
  },

  // ─────────────────────────────
  // 사용자 / 기준정보 관리
  // ─────────────────────────────
  {
    label: '시스템 관리',
    icon: 'mdi-account-cog-outline',
    roles: ['SUPERADMIN'],
    children: [
      {
        label: '사용자 목록',
        to: '/admin/users',
        icon: 'mdi-account-multiple-outline',
        routeName: 'users', // ✅ admin-users → users
      },
      {
        // 통합 기준정보 관리 (MasterData)
        label: '기준정보 관리',
        to: '/admin/users/master',
        icon: 'mdi-database-cog-outline',
        routeName: 'users-master', // ✅ router: meta.routeName='users-master'
      },
      {
        label: '비밀번호 초기화',
        to: '/admin/users/password-reset',
        icon: 'mdi-lock-reset',
        routeName: 'users-password-reset', // router와 일치
      },
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
    routeName: 'role-access', // router와 일치
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
        label: '내 정보',
        to: '/account/info',
        icon: 'mdi-account-circle',
        routeName: 'account-info', // router와 일치
      },
    ],
  },
]

// ============================================================================
// Export (SSOT 단일 메뉴 객체)
// ----------------------------------------------------------------------------
// • App.vue → Sidebar 로 전달
// • 필터링: useMenuStore → normalizeNav() → filterNav() → routeExists()
// • DeptAccess 판단은 meta.routeName(=이 파일의 routeName)으로 이뤄짐
// ============================================================================
export default menu
