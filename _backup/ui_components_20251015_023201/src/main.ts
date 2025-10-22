// ============================================================
// Hotel Admin — Main Entry (Light-only)
// ============================================================

import './styles/_index.scss'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import vuetify from '@/plugins/vuetify'
import { i18n } from '@/i18n'
import { useAuthStore } from '@/stores/auth'
import { getToken } from '@/services/http'
import '@/styles/overlay.scss'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(vuetify)
app.use(i18n)

;(async () => {
  const auth = useAuthStore()

  // 토큰 존재 시 사용자 부트스트랩
  if (getToken()) {
    try {
      await auth.bootstrap()
    } catch (err) {
      console.warn('Auth bootstrap failed:', err)
    }
  }

  app.mount('#app')
})()
