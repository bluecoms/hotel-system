// src/plugins/vuetify.ts
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

import { aliases, mdi } from 'vuetify/iconsets/mdi'
import '@mdi/font/css/materialdesignicons.css'

const brandTheme = {
  dark: false,
  colors: {
    primary:   '#C99B69', // ✅ GOLD as primary
    secondary: '#46A5A8', // 기존 틸은 보조색으로
    accent:    '#71757C', // 차콜(보조)
    error:     '#CE3E3E',
    success:   '#10B981',
    warning:   '#F59E0B',
    info:      '#46A5A8',
    background:'#F5F6F8',
    surface:   '#FFFFFF',
  },
}

export default createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: { mdi },
  },
  theme: {
    defaultTheme: 'brand',
    themes: { brand: brandTheme },
  },
  defaults: {
    global: {
      ripple: false,
//       class: 'font-pd',
      style: {
        fontFamily: "inherit"
          'Inter, "Noto Sans KR", system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      },
    },
    VAppBar:   { color: 'primary' },
    VBtn:      { rounded: 'lg', height: 40, color: 'primary' },
    VChip:     { rounded: 'lg', color: 'primary' },
    VSwitch:   { color: 'primary' },
    VCheckbox: { color: 'primary' },
    VRadio:    { color: 'primary' },
    VTextField:{ density: 'comfortable', variant: 'outlined', color: 'primary' },
    VSelect:   { density: 'comfortable', variant: 'outlined', color: 'primary' },
    VTabs:     { color: 'primary' },
    VCard:     { elevation: 1, rounded: 'lg' },
    VProgressLinear: { color: 'primary' },
  },
})
