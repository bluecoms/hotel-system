import { createI18n } from 'vue-i18n'
import ko from './messages.ko'

export const i18n = createI18n({
  legacy: false,
  locale: 'ko-KR',
  fallbackLocale: 'ko-KR',
  messages: { 'ko-KR': ko }
})
