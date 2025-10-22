<!-- ============================================================================
  File    : src/ui/components/user/DialogUserCreate.vue
  Version : 2025.10 Final Stable (Refined UI + Role Simplified)
  Purpose : Hotel Admin — 신규 사용자 등록 다이얼로그
  ------------------------------------------------------------------------------
  목적:
    • 신규 사용자(계정) 등록
    • 이름 / 이메일 / 역할(Role) 입력
  ------------------------------------------------------------------------------
  변경사항 (2025-10-23)
    ✅ 역할(Role) 목록 정리 → ADMIN / USER 만 표시
    ✅ UI 일원화 (Rounded · Gap 정리)
    ✅ 필수 입력 검증 및 메시지 개선
    ✅ 등록 완료 시 부모 emit('created') 호출
  ------------------------------------------------------------------------------
  연결 백엔드:
    • POST /api/users  → 신규 사용자 등록
============================================================================ -->
<template>
  <v-dialog v-model="localOpen" max-width="520" persistent>
    <v-card class="rounded-xl elevation-3">
      <!-- ▣ 헤더 -->
      <v-card-title class="d-flex align-center justify-space-between py-3 px-4">
        <div class="d-flex align-center gap8">
          <v-icon icon="mdi-account-plus" color="primary" size="22" />
          <span class="font-weight-bold text-h6">신규 사용자 등록</span>
        </div>
        <v-btn icon="mdi-close" variant="text" color="grey" @click="close" />
      </v-card-title>

      <v-divider />

      <!-- ▣ 입력 폼 -->
      <v-card-text class="pt-4 pb-2 px-5">
        <v-form ref="formRef" v-model="valid" lazy-validation>
          <v-text-field
            v-model.trim="form.name"
            label="이름"
            placeholder="이름을 입력하세요"
            density="comfortable"
            variant="outlined"
            :rules="[req]"
            hide-details="auto"
            clearable
            class="mb-3"
          />

          <v-text-field
            v-model.trim="form.email"
            label="이메일"
            placeholder="example@hotel.com"
            density="comfortable"
            variant="outlined"
            :rules="[req]"
            hide-details="auto"
            clearable
            class="mb-3"
          />

          <v-select
            v-model="form.role"
            label="역할(Role)"
            :items="roleItems"
            density="comfortable"
            variant="outlined"
            hide-details="auto"
            class="mb-3"
          >
            <template #prepend-inner>
              <v-icon icon="mdi-shield-account-outline" color="primary" size="18" />
            </template>
          </v-select>
        </v-form>
      </v-card-text>

      <v-divider />

      <!-- ▣ 액션 버튼 -->
      <v-card-actions class="px-5 py-3 d-flex justify-end">
        <v-btn variant="text" color="grey" @click="close">
          취소
        </v-btn>
        <v-btn
          color="primary"
          class="px-5"
          :loading="saving"
          :disabled="!valid"
          @click="onSubmit"
        >
          저장
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
/* ============================================================================
   Script Logic — 신규 사용자 등록
   ---------------------------------------------------------------------------
   구성:
     • props: modelValue / open → v-model 양방향 지원
     • emit: created (등록 후 부모 갱신)
     • validate: 이름 / 이메일 필수 검증
============================================================================ */
import { ref, reactive, watch } from 'vue'
import http from '@/services/http'
import { useToast } from '@/ui/composables/useToast'

// ▣ Props / Emits 정의
const props = defineProps({
  modelValue: { type: Boolean, default: undefined },
  open: { type: Boolean, default: undefined },
})
const emit = defineEmits(['update:modelValue', 'update:open', 'created'])

// ▣ 상태
const localOpen = ref(false)
const formRef = ref()
const valid = ref(false)
const saving = ref(false)

// 기본 입력 폼
const form = reactive({
  name: '',
  email: '',
  role: 'USER',
})

// Role 목록 (ADMIN / USER)
const roleItems = ['ADMIN', 'USER']

// 토스트 유틸
const { success, error } = useToast()

// 필수 입력 검증
const req = (v: any) => !!String(v ?? '').trim() || '필수 입력 항목입니다.'

// ▣ Props → localOpen 동기화
watch(
  () => props.modelValue ?? props.open,
  v => (localOpen.value = !!v),
  { immediate: true }
)

// ▣ localOpen → 부모로 반영
watch(localOpen, v => {
  emit('update:modelValue', v)
  emit('update:open', v)
})

// ▣ 다이얼로그 닫기
function close() {
  localOpen.value = false
  form.name = ''
  form.email = ''
  form.role = 'USER'
}

// ▣ 등록 처리
async function onSubmit() {
  const ok = await formRef.value?.validate?.()
  if (!ok?.valid) return
  try {
    saving.value = true
    const res = await http.post('/users', form)
    success('신규 사용자가 등록되었습니다.')
    emit('created', res)
    close()
  } catch (err) {
    console.error('user create failed:', err)
    error('등록 중 오류가 발생했습니다.')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.v-card {
  border-radius: 16px;
  overflow: hidden;
}
.v-card-title {
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}
.v-card-actions {
  border-top: 1px solid #e5e7eb;
}
.v-btn {
  font-weight: 600;
}
</style>
