// src/ui/tokens.ts
// -----------------------------------------------------------
// Hotel Admin Design Tokens Adapter (Light Only · Neutral Blue 2025)
// CSS vars → JS bridge (SSOT: src/styles/tokens.css)
// -----------------------------------------------------------

/**
 * CSS 변수 읽기 헬퍼
 * @param name CSS variable name (예: --brand-primary)
 * @param fallback 기본값 (CSS var이 없을 때)
 */
function cssVar(name: string, fallback = ''): string {
  if (typeof window === 'undefined') return fallback
  const v = getComputedStyle(document.documentElement).getPropertyValue(name)
  return (v || fallback).trim()
}

/**
 * tokens: CSS 변수 기반 디자인 토큰 집합
 * - 2025 토큰명 우선(--color-*, --brand-*)
 * - 레거시 호환(--bg, --panel, --text, --muted, --line) 보조
 */
export const tokens = {
  brand: {
    primary:   () => cssVar('--brand-primary',  '#2563EB'),  // Blue-600
    secondary: () => cssVar('--brand-secondary','#1E40AF'),  // Blue-800
    accent:    () => cssVar('--brand-accent',   '#60A5FA'),  // Blue-400
    accent2:   () => cssVar('--brand-accent-2', '#93C5FD'),  // Blue-300
  },

  neutral: {
    bg:     () => cssVar('--color-bg',     cssVar('--bg',    '#F8FAFC')),
    panel:  () => cssVar('--color-surface',cssVar('--panel', '#FFFFFF')),
    text:   () => cssVar('--color-text',   cssVar('--text',  '#0F172A')),
    muted:  () => cssVar('--color-muted',  cssVar('--muted', '#64748B')),
    line:   () => cssVar('--color-line',   cssVar('--line',  '#E5E7EB')),
  },

  effects: {
    radius:    () => cssVar('--radius-sm', '12px'),
    radiusSm:  () => cssVar('--radius-xs', '10px'),
    shadowSm:  () => cssVar('--shadow-sm', '0 2px 10px rgba(16,24,40,.06)'),
    shadow1:   () => cssVar('--shadow-md', '0 6px 22px rgba(16,24,40,.08)'),
    shadow2:   () => cssVar('--shadow-lg', '0 12px 40px rgba(16,24,40,.12)'),
  },

  control: {
    h:   () => cssVar('--control-h', '40px'),
    gap: () => cssVar('--space-3', '12px'),
  },

  font: {
    base:  () => cssVar('--font-base'),
    kr:    () => cssVar('--font-kr'),
    en:    () => cssVar('--font-en'),
    serif: () => cssVar('--font-serif'),
  },
}

export { cssVar }

/**
 * color: Vuetify theme bridge용 alias
 * - Primary = brand.primary (Blue)
 * - Accent = brand.accent (Light Blue)
 */
export const color = {
  primary:    () => tokens.brand.primary(),
  secondary:  () => tokens.brand.secondary(),
  success:    () => cssVar('--color-success', '#10B981'),
  warning:    () => cssVar('--color-warning', '#F59E0B'),
  error:      () => cssVar('--color-error',   '#EF4444'),
  info:       () => cssVar('--color-info',    '#3B82F6'),
  background: () => tokens.neutral.bg(),
  surface:    () => tokens.neutral.panel(),
}

// ---- tokens.color.* 호환성 부착 ----
// eslint-disable-next-line @typescript-eslint/no-explicit-any
;(tokens as any).color = color

type TokensWithColor = typeof tokens & { color: typeof color }
const tokensWithColor = tokens as TokensWithColor

export default tokensWithColor
