<!-- ============================================================================
  File    : src/views/Login.vue
  Version : 2025.10 Stable (Property Sync + Fullscreen)
  Purpose : Hotel Admin — 내부 관리자 로그인 화면
  ------------------------------------------------------------------------------
  목적:
    • 관리자 / 직원 로그인 (지점 선택 + 내부 토큰 인증)
    • 인증 헤더: X-Internal-Token (http.ts)
    • UI: Vuetify 3 기반 / 모바일 대응 / 풀스크린 고정
    • 기능:
        ✅ 로그인 전 지점(property_code) 선택 가능
        ✅ CapsLock 감지 및 안내
        ✅ 이메일 저장(rememberLogin)
        ✅ redirect 지원 (/login?redirect=xxx)

  주요 개선사항:
    ✅ App.vue 의 일반 컨테이너 여백 영향 제거 (v-main 제거)
    ✅ 100vh / 100dvh 고정 레이아웃 적용
    ✅ 지점 선택 추가 (property_code → localStorage 저장)
============================================================================ -->
<template>
  <div class="login-wrap d-flex align-center justify-center" spellcheck="false" role="main">
    <v-card class="login-card pa-8" elevation="8" width="420">
      <div class="text-center mb-6">
        <h2 class="text-h5 font-weight-bold mb-1">호텔 관리자 시스템</h2>
        <div class="text-body-2 text-medium-emphasis">관리자 계정으로 로그인하세요</div>
      </div>

      <!-- ✅ 지점 선택 (Property Selector) -->
      <v-select
        v-model="selectedProperty"
        :items="propertyItems"
        item-title="name"
        item-value="code"
        label="지점 선택"
        variant="outlined"
        density="comfortable"
        clearable
        hide-details
        class="mb-4"
      />

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
        autocomplete="current-password"
        @keyup.enter="go"
        @keyup="checkCaps"
        :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
        @click:append-inner="showPassword = !showPassword"
      />

      <v-alert v-if="capsOn" type="warning" density="compact" variant="tonal" class="mb-2">
        Caps Lock이 켜져 있습니다. (대문자 입력 주의)
      </v-alert>

      <v-checkbox v-model="remember" label="이메일 기억하기" hide-details color="primary" class="mb-4" />

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
        <strong>v0.3.0</strong> · © 2025 <span class="text-primary">Hotel Admin</span><br />
        <span class="text-grey">보안 강화를 위해 공용 PC에서는 자동 로그인 기능을 사용하지 마세요.</span>
      </div>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import http from '@/services/http'
import { useToast } from '@/ui/composables/useToast'
import * as PropertyApi from '@/services/property'

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
const passwordField = ref<any>(null)

/** ✅ 지점 선택 상태 */
const propertyItems = ref<{ code: string; name: string }[]>([])
const selectedProperty = ref(localStorage.getItem('property_code') || '')

/** CapsLock 감지 */
function checkCaps(e: KeyboardEvent) {
  capsOn.value = !!e.getModifierState?.('CapsLock')
}

/** 비밀번호 필드 포커스 이동 */
function focusNext(key: 'password') {
  if (key === 'password') {
    nextTick(() => {
      const el = passwordField.value?.$el?.querySelector('input') as HTMLInputElement | null
      el?.focus()
    })
  }
}

/** 이메일 복원 */
onMounted(async () => {
  const saved = localStorage.getItem('rememberLogin')
  if (saved) {
    try {
      const obj = JSON.parse(saved)
      email.value = obj.email || ''
      remember.value = !!obj.email
    } catch {}
  }

  /** ✅ 지점 목록 로드 */
  try {
    const list = await PropertyApi.listActive()
    propertyItems.value = list
  } catch {
    propertyItems.value = [{ code: 'MOP', name: 'Mokpo Ocean Hotel' }]
  }
})

/** 로그인 실행 */
async function go() {
  if (!email.value || !password.value) {
    info('이메일과 비밀번호를 입력하세요.')
    return
  }

  if (!selectedProperty.value) {
    info('로그인할 지점을 선택하세요.')
    return
  }

  loading.value = true
  try {
    const res: any = await http.post('login', { email: email.value.trim(), password: password.value })
    const token: string | undefined = res?.token
    if (!token) throw new Error('서버에서 토큰을 받지 못했습니다.')

    /** ✅ 토큰 & 지점 저장 */
    http.setToken(token)
    localStorage.setItem('property_code', selectedProperty.value)

    await auth.bootstrap()
    if (remember.value) {
      localStorage.setItem('rememberLogin', JSON.stringify({ email: email.value }))
    } else {
      localStorage.removeItem('rememberLogin')
    }

    const redirect = (route.query.redirect as string) || '/dashboard'
    router.replace(redirect)
    success(`${selectedProperty.value} 로그인 성공! 환영합니다.`)
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
  min-height: 100dvh;
  width: 100%;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
}

.login-card {
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 4px 20px rgba(30, 58, 138, 0.25);
}

.btn-login {
  font-weight: 700;
  height: 46px;
  text-transform: none;
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
