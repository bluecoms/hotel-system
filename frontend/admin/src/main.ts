// src/main.ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import vuetify from '@/plugins/vuetify'
import { useAuthStore } from '@/stores/auth'
import { i18n } from '@/i18n'

import './styles/global.css'
import '@/styles/theme.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(vuetify)
app.use(i18n) // 한 번만 등록

;(async () => {
  // 최초 1회 유저 상태 싱크 (top-level await 지양 → IIFE 내부에서 처리)
  const auth = useAuthStore()
  try { await auth.bootstrap() } catch {/* ignore */}

  app.mount('#app') // 한 번만 호출
})()
