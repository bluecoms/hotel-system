export type NavItem = {
  label: string
  to?: string
  icon?: string
  roles?: string[]
  children?: NavItem[]
}

const menu: NavItem[] = [
  { label: 'Dashboard', to: '/', icon: 'mdi-view-dashboard' },

  {
    label: 'Users',               // ← 대메뉴 하나만 유지
    icon: 'mdi-account-cog',
    roles: ['ADMIN', 'SUPERADMIN'],
    children: [
      { label: 'Users',          to: '/admin/users',                 roles: ['SUPERADMIN'] },
      { label: 'Employees',      to: '/admin/employees',             roles: ['ADMIN','SUPERADMIN'] },
      { label: 'Reset Password', to: '/admin/users/password-reset',  roles: ['SUPERADMIN'] },
    ],
  },

  {
    label: 'Closing',
    icon: 'mdi-calendar-check',
    roles: ['ADMIN', 'SUPERADMIN'],
    children: [
      { label: 'Board',    to: '/closing/board' },
      { label: 'Calendar', to: '/closing' },
    ],
  },

  {
    label: 'OTA',
    icon: 'mdi-web',
    roles: ['ADMIN', 'SUPERADMIN'],
    children: [{ label: 'Overview', to: '/ota' }],
  },

  {
    label: 'Reports',
    icon: 'mdi-chart-areaspline',
    roles: ['ADMIN', 'SUPERADMIN'],
    children: [{ label: 'Sales Tags', to: '/admin/reports/sales-tags' }],
  },

  {
    label: 'Admin',
    icon: 'mdi-office-building',
    roles: ['ADMIN', 'SUPERADMIN'],
    children: [
      { label: 'HR',        to: '/admin/hr' },
      { label: 'Finance',   to: '/admin/finance' },
      { label: 'Inventory', to: '/admin/inventory' },
    ],
  },

  {
    label: 'My Account',
    icon: 'mdi-account',
    roles: ['ADMIN','SUPERADMIN'],
    children: [{ label: 'Change Password', to: '/account/password' }],
  },
]

export default menu
