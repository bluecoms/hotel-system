<template>
  <v-main class="d-flex align-center justify-center login-wrap" spellcheck="false">
    <v-card class="login-card pa-8" elevation="8" width="420">
      <div class="text-center mb-6">
        <h2 class="text-h5 font-weight-bold mb-1">호텔 관리자 시스템</h2>
        <div class="text-body-2 text-medium-emphasis">관리자 계정으로 로그인하세요</div>
      </div>

      <v-text-field
        v-model="email"
        label="이메일"
        type="email"
        density="comfortable"
        variant="outlined"
        color="primary"
        hide-details="auto"
        class="mb-4"
        autofocus
        clearable
        :spellcheck="false"
        autocomplete="username"
        autocapitalize="off"
        @keyup.enter="focusNext('password')"
      />

      <v-text-field
        ref="passwordField"
        v-model="password"
        label="비밀번호"
        :type="showPassword ? 'text' : 'password'"
        density="comfortable"
        variant="outlined"
        color="primary"
        hide-details="auto"
        class="mb-2"
        :spellcheck="false"
        autocomplete="current-password"
        @keyup.enter="go"
        @keyup="checkCaps"
        :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
        @click:append-inner="showPassword = !showPassword"
      />

      <v-alert
        v-if="capsOn"
        type="warning"
        density="comfortable"
        variant="tonal"
        class="mb-2"
      >
        Caps Lock이 켜져 있습니다. (대문자 입력 주의)
      </v-alert>

      <v-checkbox
        v-model="remember"
        label="이메일 기억하기"
        hide-details
        color="primary"
        class="mb-4"
      />

      <v-btn
        color="primary"
        size="large"
        block
        class="btn-login"
        @click="go"
        :loading="loading"
        :disabled="!email || !password"
      >
        로그인
      </v-btn>

      <div class="text-caption text-medium-emphasis mt-8 text-center">
        <strong>v0.2.1</strong> · © 2025 <span class="text-primary">Hotel Admin</span><br />
        ⏤ 보안 강화를 위해 <strong>공용 PC에서는 자동 로그인 기능을 사용하지 마세요.</strong>
      </div>
    </v-card>
  </v-main>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import http from '@/services/http'
import { useToast } from '@/ui/composables/useToast'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const { success, error, info } = useToast()

const email = ref('')
const password = ref('')
const remember = ref(false)
const loading = ref(false)
const showPassword = ref(false)
const capsOn = ref(false)
// Vuetify 3에서 내부 input 포커싱을 위해 template ref 사용
const passwordField = ref<any>(null)

function checkCaps(e: KeyboardEvent) {
  const caps = e.getModifierState?.('CapsLock')
  capsOn.value = !!caps
}

function focusNext(key: 'password') {
  if (key === 'password') {
    nextTick(() => {
      const el = passwordField.value?.$el?.querySelector('input') as HTMLInputElement | null
      el?.focus()
    })
  }
}

// 자동 로그인 복원
onMounted(() => {
  const saved = localStorage.getItem('rememberLogin')
  if (saved) {
    try {
      const obj = JSON.parse(saved)
      email.value = obj.email || ''
      remember.value = !!obj.email
    } catch { /* noop */ }
  }
})

async function go() {
  if (!email.value || !password.value) {
    info('이메일과 비밀번호를 입력하세요.')
    return
  }

  loading.value = true
  try {
    // 1) 로그인 요청
    const res: any = await http.post('/login', {
      email: email.value.trim(),
      password: password.value,
    })
    const token: string | undefined = res?.token
    if (!token) throw new Error('서버에서 토큰을 받지 못했습니다.')

    // 2) 토큰 저장
    http.setToken(token)

    // 3) 유저 정보 부트스트랩
    await auth.bootstrap()

    // 4) remember 처리
    if (remember.value)
      localStorage.setItem('rememberLogin', JSON.stringify({ email: email.value }))
    else
      localStorage.removeItem('rememberLogin')

    // 5) 이동
    const redirect = (route.query.redirect as string) || '/dashboard'
    router.replace(redirect)
    success('로그인 성공! 환영합니다.')
  } catch (e: any) {
    const msg = e?.detail || e?.message || '아이디 또는 비밀번호를 확인하세요.'
    error(msg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrap {
  min-height: 100vh;
  /* 브랜드 그라디언트 */
  background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
}

.login-card {
  border-radius: 16px;
  background: #fff;
}

.btn-login {
  font-weight: 700;
  letter-spacing: 0.3px;
  height: 44px;
}

:deep(.v-text-field input) {
  font-size: 1rem;
}

@media (max-width: 600px) {
  .login-card {
    width: 92%;
    padding: 24px;
  }
}
</style>
