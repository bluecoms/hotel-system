import '@/styles/_index.scss'
// src/main.ts (수정 후)
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import vuetify from '@/plugins/vuetify'
import { useAuthStore } from '@/stores/auth'
import { i18n } from '@/i18n'
import { getToken } from '@/services/http'


const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(vuetify)
app.use(i18n)

;(async () => {
  const auth = useAuthStore()
  if (getToken()) {
    try {
      await auth.bootstrap()
    } catch {}
  }
  app.mount('#app')
})()
