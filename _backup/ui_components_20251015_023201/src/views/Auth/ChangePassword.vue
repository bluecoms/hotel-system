<template>
  <v-container class="py-8" style="max-width: 560px;">
    <div class="d-flex align-center justify-space-between mb-4">
      <h2 class="text-h6 font-weight-bold">비밀번호 변경</h2>
      <v-btn color="secondary" variant="text" size="small" @click="clearForm">입력 초기화</v-btn>
    </div>

    <v-alert type="info" variant="tonal" class="mb-6">
      <div>현재 비밀번호를 입력하고 새 비밀번호를 설정하세요.</div>
      <div class="text-caption">비밀번호는 <strong>8자 이상</strong>이어야 하며, 영문+숫자 조합을 권장합니다.</div>
    </v-alert>

    <v-text-field
      v-model="current"
      label="현재 비밀번호"
      :type="showCur ? 'text' : 'password'"
      variant="outlined"
      density="comfortable"
      hide-details="auto"
      color="primary"
      class="mb-3"
      :append-inner-icon="showCur ? 'mdi-eye-off' : 'mdi-eye'"
      @click:append-inner="showCur = !showCur"
      @keyup.enter="focusNext('next1')"
      ref="curInput"
      @keyup="checkCaps($event)"
    />

    <v-text-field
      v-model="next1"
      label="새 비밀번호"
      :type="showNew ? 'text' : 'password'"
      variant="outlined"
      density="comfortable"
      hide-details="auto"
      color="primary"
      class="mb-3"
      :append-inner-icon="showNew ? 'mdi-eye-off' : 'mdi-eye'"
      @click:append-inner="showNew = !showNew"
      ref="nextInput1"
      @keyup.enter="focusNext('next2')"
      @keyup="checkCaps($event)"
    />

    <v-text-field
      v-model="next2"
      label="새 비밀번호 확인"
      :type="showNew ? 'text' : 'password'"
      variant="outlined"
      density="comfortable"
      hide-details="auto"
      color="primary"
      class="mb-2"
      ref="nextInput2"
      @keyup.enter="submit"
    />

    <v-alert
      v-if="capsOn"
      type="warning"
      variant="tonal"
      density="comfortable"
      class="mb-2"
    >
      Caps Lock이 켜져 있습니다.
    </v-alert>

    <v-progress-linear
      v-if="next1"
      :model-value="strength"
      :color="strengthColor"
      height="6"
      rounded
      class="mb-4"
    ></v-progress-linear>

    <v-btn
      color="primary"
      size="large"
      :loading="loading"
      :disabled="disabled"
      block
      @click="submit"
    >
      비밀번호 변경
    </v-btn>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { changePassword } from '@/services/auth'
import { useToast } from '@/ui/composables/useToast'
import { useConfirm } from '@/ui/composables/useConfirm'

const toast = useToast()
const confirmApi = useConfirm()

const current = ref('')
const next1 = ref('')
const next2 = ref('')
const showCur = ref(false)
const showNew = ref(false)
const loading = ref(false)
const capsOn = ref(false)
const curInput = ref<HTMLInputElement>()
const nextInput1 = ref<HTMLInputElement>()
const nextInput2 = ref<HTMLInputElement>()

// CapsLock 감지
function checkCaps(e: KeyboardEvent) {
  const caps = e.getModifierState && e.getModifierState('CapsLock')
  capsOn.value = !!caps
}

function focusNext(refName: string) {
  if (refName === 'next1') nextTick(() => nextInput1.value?.focus())
  else if (refName === 'next2') nextTick(() => nextInput2.value?.focus())
}

// 비밀번호 강도 계산
const strength = computed(() => {
  if (!next1.value) return 0
  let s = 0
  if (next1.value.length >= 8) s += 30
  if (/[A-Z]/.test(next1.value)) s += 20
  if (/[0-9]/.test(next1.value)) s += 25
  if (/[^A-Za-z0-9]/.test(next1.value)) s += 25
  return Math.min(s, 100)
})
const strengthColor = computed(() => {
  if (strength.value < 40) return 'error'
  if (strength.value < 70) return 'warning'
  return 'success'
})

const disabled = computed(
  () =>
    !current.value ||
    !next1.value ||
    next1.value !== next2.value ||
    next1.value.length < 8
)

function clearForm() {
  current.value = ''
  next1.value = ''
  next2.value = ''
  capsOn.value = false
}

async function submit() {
  if (disabled.value) {
    toast.info('입력값을 확인하세요.')
    return
  }

  const ok = await confirmApi.ask('비밀번호를 변경하시겠습니까?', {
    title: '비밀번호 변경 확인',
    okText: '변경',
    cancelText: '취소',
  })
  if (!ok) return

  loading.value = true
  try {
    await changePassword(current.value, next1.value)
    toast.success('비밀번호가 변경되었습니다.')
    clearForm()
  } catch (e: any) {
    toast.error(e?.message || '비밀번호 변경에 실패했습니다.')
  } finally {
    loading.value = false
  }
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
