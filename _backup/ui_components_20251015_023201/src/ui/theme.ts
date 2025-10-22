// src/ui/theme.ts
// -----------------------------------------------------------
// Hotel Admin — Vuetify Theme Bridge (Light Only)
// tokens.ts 기반 색상 시스템과 Vuetify Theme 연결
// -----------------------------------------------------------

import type { ThemeDefinition } from 'vuetify'
import tokens from './tokens'

export const BRAND_THEME_NAME = 'hotelLight'

// 1) ThemeDefinition
export const brandTheme: ThemeDefinition = {
  dark: false,
  colors: {
    primary: '#3B82F6',                 // Blue-500
    secondary: tokens.color.secondary(),  // Blue-800
    success: tokens.color.success(),      // Emerald-500
    warning: tokens.color.warning(),      // Amber-500
    error: tokens.color.error(),          // Red-500
    info: tokens.color.info(),            // Blue-500
    background: tokens.color.background(),// BG
    surface: tokens.color.surface(),      // Panel
  },
}

// 2) ThemeOptions — 타입 직접 지정 안 함
export const themeOptions = {
  defaultTheme: BRAND_THEME_NAME,
  themes: {
    [BRAND_THEME_NAME]: brandTheme,
  },
} as const

// -----------------------------------------------------------
// Vuetify Component Defaults
// -----------------------------------------------------------
export const defaults = {
  VBtn: {
    rounded: 'lg',
    elevation: 0,
    color: 'primary',
    variant: 'flat',
    height: 40,
    style: {
      fontWeight: 600,
      textTransform: 'none',
    },
    class: 'btn-default',
  },
  VCard: { rounded: 'xl', elevation: 1 },
  VTextField: { density: 'comfortable', variant: 'outlined' },
  VTable: { density: 'comfortable' },
  VAlert: { density: 'comfortable' },
} as const
