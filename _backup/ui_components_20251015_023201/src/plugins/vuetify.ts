// src/plugins/vuetify.ts
// ===========================================================
// Hotel Admin — Vuetify Plugin (Light Only 2025)
// ===========================================================

import 'vuetify/styles'
import { createVuetify, type ThemeDefinition } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { aliases, mdi } from 'vuetify/iconsets/mdi'
import '@mdi/font/css/materialdesignicons.css'

import { brandTheme, defaults } from '@/ui/theme'

// ===========================================================
// Vuetify 인스턴스 생성 (정상 타입 대응)
// ===========================================================
export default createVuetify({
  components,
  directives,
  defaults,
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: { mdi },
  },
  theme: {
    defaultTheme: 'hotel',
    themes: {
      hotel: brandTheme as ThemeDefinition,
    },
  },
})
