<template>
  <v-container class="py-8" style="max-width: 720px;">
    <div class="d-flex align-center justify-space-between mb-4">
      <h2 class="text-h6 font-weight-bold">사용자 비밀번호 초기화</h2>
      <v-btn color="secondary" variant="text" size="small" @click="clearForm">
        초기화 폼 지우기
      </v-btn>
    </div>

    <v-alert type="info" variant="tonal" class="mb-6">
      <div>이메일을 입력하면 해당 사용자의 비밀번호를 재설정할 수 있습니다.</div>
      <div>새 비밀번호를 직접 지정하지 않으면, <strong>임시 비밀번호가 자동 생성</strong>됩니다.</div>
    </v-alert>

    <v-text-field
      v-model="email"
      label="사용자 이메일"
      type="email"
      variant="outlined"
      hide-details="auto"
      density="comfortable"
      color="primary"
      class="mb-3"
      autofocus
      @keyup.enter="focusNext('password')"
    />

    <v-text-field
      v-model="newPassword"
      label="새 비밀번호 (선택)"
      :type="show ? 'text' : 'password'"
      variant="outlined"
      hide-details="auto"
      density="comfortable"
      color="primary"
      class="mb-6"
      ref="passwordInput"
      :append-inner-icon="show ? 'mdi-eye-off' : 'mdi-eye'"
      @click:append-inner="show = !show"
      @keyup.enter="confirmReset"
    />

    <v-btn
      color="primary"
      size="large"
      :loading="loading"
      :disabled="!email"
      @click="confirmReset"
    >
      비밀번호 초기화
    </v-btn>

    <v-alert v-if="tempPassword" type="success" variant="tonal" class="mt-6">
      <div class="d-flex align-center justify-space-between">
        <div>
          임시 비밀번호가 생성되었습니다.<br />
          <strong>{{ tempPassword }}</strong>
        </div>
        <v-btn icon="mdi-content-copy" variant="text" color="primary" @click="copyTempPwd" />
      </div>
    </v-alert>
  </v-container>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { resetUserPassword } from '@/services/auth'
import { useToast } from '@/ui/composables/useToast'
import { useConfirm } from '@/ui/composables/useConfirm'

const toast = useToast()
const confirmApi = useConfirm()

const email = ref('')
const newPassword = ref('')
const show = ref(false)
const loading = ref(false)
const tempPassword = ref<string | null>(null)
const passwordInput = ref<HTMLInputElement>()

function focusNext(refName: string) {
  if (refName === 'password') nextTick(() => passwordInput.value?.focus())
}

function clearForm() {
  email.value = ''
  newPassword.value = ''
  tempPassword.value = null
}

async function confirmReset() {
  if (!email.value) {
    toast.info('이메일을 입력하세요.')
    return
  }
  const ok = await confirmApi.ask(
    `${email.value} 사용자의 비밀번호를 정말 초기화하시겠습니까?`,
    { title: '비밀번호 초기화 확인', okText: '초기화', cancelText: '취소' }
  )
  if (ok) resetPwd()
}

async function resetPwd() {
  loading.value = true
  tempPassword.value = null
  try {
    const res: any = await resetUserPassword(email.value, newPassword.value || undefined)
    tempPassword.value = res?.temp_password || newPassword.value || null
    toast.success('비밀번호가 성공적으로 초기화되었습니다.')
  } catch (e: any) {
    toast.error(e?.message || '비밀번호 초기화에 실패했습니다.')
  } finally {
    loading.value = false
  }
}

function copyTempPwd() {
  if (!tempPassword.value) return
  navigator.clipboard.writeText(tempPassword.value)
  toast.info('임시 비밀번호가 복사되었습니다.')
}
</script>

<style scoped>
.v-alert {
  border-radius: 12px;
}
.v-btn {
  font-weight: 600;
  letter-spacing: 0.3px;
}
</style>
