// --- BEGIN FILE: src/i18n/index.ts ---
import { createI18n } from 'vue-i18n'
import ko from './messages.ko'

export const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: 'ko',
  fallbackLocale: 'ko',
  messages: { ko },
})
// --- END FILE ---
