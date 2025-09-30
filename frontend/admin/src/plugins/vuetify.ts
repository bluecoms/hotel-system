// src/plugins/vuetify.ts
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

// (아이콘 사용 시)
import '@mdi/font/css/materialdesignicons.css'

export default createVuetify({
  components,
  directives,
  // 필요 시 테마/아이콘 설정:
  // theme: { defaultTheme: 'light' },
  // icons: { defaultSet: 'mdi' },
})
