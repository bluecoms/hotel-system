// src/main.ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import vuetify from '@/plugins/vuetify'
import { useAuthStore } from '@/stores/auth'

import './styles/global.css'
import '@/styles/theme.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(vuetify)

// 최초 1회 유저 상태 싱크
const auth = useAuthStore()
try { await auth.bootstrap() } catch {/* ignore */}

app.mount('#app')
