import { tokens } from './tokens'
export const brandTheme = {
  defaultTheme: 'light',
  themes: {
    light: {
      dark: false,
      colors: {
        primary: tokens.color.primary,
        secondary: tokens.color.secondary,
        success: tokens.color.success,
        warning: tokens.color.warning,
        error:   tokens.color.error,
        background: tokens.color.background,
        surface: tokens.color.surface,
      },
    },
  },
}

export const defaults = {
  VBtn:       { rounded: 'xl', elevation: 0, color: 'primary' },
  VCard:      { rounded: 'xl', elevation: 1 },
  VTextField: { density: 'comfortable', variant: 'outlined' },
  VTable:     { density: 'comfortable' },
  VAlert:     { density: 'comfortable' },
}
