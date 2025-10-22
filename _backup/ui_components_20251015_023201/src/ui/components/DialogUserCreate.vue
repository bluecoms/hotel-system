<template>
  <v-dialog v-model="localOpen" max-width="520" persistent>
    <v-card>
      <v-card-title class="d-flex align-center justify-space-between">
        <div class="d-flex align-center gap8">
          <v-icon icon="mdi-account-plus" color="primary" />
          신규 사용자 등록
        </div>
        <v-btn icon="mdi-close" variant="text" @click="close" />
      </v-card-title>

      <v-divider />

      <v-card-text>
        <v-form ref="formRef" v-model="valid" class="pt-2">
          <v-text-field v-model="form.name" label="이름" :rules="[req]" />
          <v-text-field v-model="form.email" label="이메일" :rules="[req]" />
          <v-select v-model="form.role" :items="roleItems" label="역할(Role)" />
        </v-form>
      </v-card-text>

      <v-card-actions class="justify-end">
        <v-btn variant="text" @click="close">취소</v-btn>
        <v-btn color="primary" :loading="saving" @click="onSubmit">저장</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import http from '@/services/http'
import { useToast } from '@/ui/composables/useToast'

/**
 *  v-model / v-model:open 양쪽 모두 지원
 */
const props = defineProps({
  modelValue: { type: Boolean, default: undefined },
  open: { type: Boolean, default: undefined },
})
const emit = defineEmits(['update:modelValue', 'update:open', 'created'])

const localOpen = ref(false)
const formRef = ref()
const valid = ref(false)
const saving = ref(false)
const form = reactive({ name: '', email: '', role: 'ADMIN' })
const roleItems = ['ADMIN', 'FRONT', 'HK', 'FNB']
const { success, error } = useToast()
const req = (v: any) => !!String(v ?? '').trim() || '필수 입력 항목입니다.'

//  props → localOpen 반영
watch(
  () => props.modelValue ?? props.open,
  v => { localOpen.value = !!v },
  { immediate: true }
)

//  localOpen → 부모로 전달
watch(localOpen, v => {
  emit('update:modelValue', v)
  emit('update:open', v)
})

//  닫기 함수
function close() {
  localOpen.value = false
  form.name = ''
  form.email = ''
  form.role = 'ADMIN'
}

//  등록 처리
async function onSubmit() {
  const ok = await formRef.value?.validate?.()
  if (!ok?.valid) return
  try {
    saving.value = true
    const r = await http.post('/users', form)
    success('등록 완료')
    emit('created', r)
    close()
  } catch {
    error('등록 실패')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.v-card-title {
  font-weight: 600;
}
</style>
