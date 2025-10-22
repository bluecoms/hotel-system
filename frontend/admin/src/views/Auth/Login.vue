<!-- ============================================================================
  File    : src/views/Login.vue
  Version : 2025.11-01 · v3.6 (DeptAccess Auth · Property Sync · SSOT Final)
  Purpose : Hotel Admin — 내부 관리자 로그인 화면
  ------------------------------------------------------------------------------
  목적:
    • FastAPI 백엔드(/api/login) + X-Internal-Token 기반 로그인
    • 로그인 전 “지점(property_code)” 선택 → Header 자동 동기화
    • 로그인 성공 시 AuthStore.bootstrap() 실행 → DeptAccess 권한 로드
  ------------------------------------------------------------------------------
  개선사항 (v3.6)
    ✅ http → httpEx(fetch 확장) 호환
    ✅ property_code 저장/헤더 전달 일원화
    ✅ redirect 정상화 (/login?redirect=…)
    ✅ rememberLogin (이메일 저장) + CapsLock 감지 + 모바일 대응
  ------------------------------------------------------------------------------
  백엔드 요약:
    POST /api/login   → { token, user:{email,name,roles[] } }
    Header: X-Internal-Token ← token
    Header: X-Property-Code ← 지점 코드(MOP 등)
  ============================================================================
-->
<template>
  <div class="login-wrap d-flex align-center justify-center" spellcheck="false" role="main">
    <v-card class="login-card pa-8" elevation="8" width="420">
      <!-- 타이틀 -->
      <div class="text-center mb-6">
        <h2 class="text-h5 font-weight-bold mb-1">호텔 관리자 시스템</h2>
        <div class="text-body-2 text-medium-emphasis">관리자 계정으로 로그인하세요</div>
      </div>

      <!-- ✅ 지점 선택 -->
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

      <!-- 이메일 -->
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

      <!-- 비밀번호 -->
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
        :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
        @click:append-inner="showPassword = !showPassword"
        @keyup.enter="go"
        @keyup="checkCaps"
      />

      <!-- CapsLock 경고 -->
      <v-alert
        v-if="capsOn"
        type="warning"
        density="compact"
        variant="tonal"
        class="mb-2"
      >Caps Lock이 켜져 있습니다. (대문자 입력 주의)</v-alert>

      <!-- 이메일 기억 -->
      <v-checkbox
        v-model="remember"
        label="이메일 기억하기"
        hide-details
        color="primary"
        class="mb-4"
      />

      <!-- 로그인 버튼 -->
      <v-btn
        color="primary"
        size="large"
        block
        class="btn-login"
        :loading="loading"
        :disabled="!email || !password"
        @click="go"
      >
        로그인
      </v-btn>

      <!-- 푸터 -->
      <div class="text-caption text-medium-emphasis mt-8 text-center">
        <strong>v0.3.6</strong> · © 2025 <span class="text-primary">Hotel Admin</span><br />
        <span class="text-grey">공용 PC에서는 자동로그인 기능을 사용하지 마세요.</span>
      </div>
    </v-card>
  </div>
</template>

<script setup lang="ts">
// ----------------------------------------------------------------------------
// Imports
// ----------------------------------------------------------------------------
import { ref, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePropertyStore } from '@/stores/property'
import { httpEx } from '@/services/http-extended'
import { useToast } from '@/ui/composables/useToast'
import * as PropertyApi from '@/services/property'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const toast = useToast()
const propertyStore = usePropertyStore()

// ----------------------------------------------------------------------------
// States
// ----------------------------------------------------------------------------
const email = ref('')
const password = ref('')
const remember = ref(false)
const loading = ref(false)
const showPassword = ref(false)
const capsOn = ref(false)
const passwordField = ref<any>(null)

const propertyItems = ref<{ code: string; name: string }[]>([])
const selectedProperty = ref(localStorage.getItem('property_code') || '')

// ----------------------------------------------------------------------------
// Utility: CapsLock 감지 + 포커스 이동
// ----------------------------------------------------------------------------
function checkCaps(e: KeyboardEvent) {
  capsOn.value = !!e.getModifierState?.('CapsLock')
}
function focusNext(key: 'password') {
  if (key === 'password') {
    nextTick(() => {
      const el = passwordField.value?.$el?.querySelector('input') as HTMLInputElement | null
      el?.focus()
    })
  }
}

// ----------------------------------------------------------------------------
// 초기 로드: 이메일 복원 + 지점 목록 로드
// ----------------------------------------------------------------------------
onMounted(async () => {
  // 저장된 이메일 복원
  const saved = localStorage.getItem('rememberLogin')
  if (saved) {
    try {
      const obj = JSON.parse(saved)
      email.value = obj.email || ''
      remember.value = !!obj.email
    } catch {}
  }

  // 지점 목록 API 호출
  try {
    const list = await PropertyApi.listActive()
    propertyItems.value = list
  } catch {
    propertyItems.value = [{ code: 'MOP', name: 'Mokpo Ocean Hotel' }]
  }
})

// ----------------------------------------------------------------------------
// 로그인 로직
// ----------------------------------------------------------------------------
async function go() {
  if (!email.value || !password.value)
    return toast.info('이메일과 비밀번호를 입력하세요.')
  if (!selectedProperty.value)
    return toast.info('로그인할 지점을 선택하세요.')

  loading.value = true
  try {
    // ① 로그인 요청
    const res: any = await httpEx.postJSON('login', {
      email: email.value.trim(),
      password: password.value,
    })

    // ② 토큰 추출 + 저장
    const token = res?.token
    if (!token) throw new Error('서버에서 토큰을 받지 못했습니다.')
    httpEx.setToken?.(token) ?? (localStorage.setItem('ADMIN_TOKEN', token))
    localStorage.setItem('property_code', selectedProperty.value)
    propertyStore.set(selectedProperty.value)

    // ③ Auth Store 부트스트랩 → DeptAccess 로드
    await auth.bootstrap()

    // ④ 이메일 기억 설정
    if (remember.value)
      localStorage.setItem('rememberLogin', JSON.stringify({ email: email.value }))
    else localStorage.removeItem('rememberLogin')

    // ⑤ Redirect → 대시보드
    const redirect = (route.query.redirect as string) || '/'
    router.replace(redirect)
    toast.success(`${selectedProperty.value} 로그인 성공!`)
  } catch (e: any) {
    const msg = e?.detail || e?.message || '아이디 또는 비밀번호를 확인하세요.'
    toast.error(msg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* ============================================================================
   Layout / Style
   ==========================================================================*/
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

/* 모바일 대응 */
@media (max-width: 600px) {
  .login-card {
    width: 92%;
    padding: 24px;
  }
}
</style>
