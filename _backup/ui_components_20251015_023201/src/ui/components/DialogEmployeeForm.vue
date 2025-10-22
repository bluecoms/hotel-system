<template>
  <v-dialog v-model="open" max-width="640" persistent>
    <v-card>
      <v-card-title class="d-flex align-center justify-space-between">
        <div class="d-flex align-center gap-2">
          <v-icon icon="mdi-account-plus" color="primary" />
          신규 직원 등록
        </div>
        <v-btn icon="mdi-close" variant="text" @click="close" />
      </v-card-title>

      <v-divider />

      <v-card-text>
        <v-form ref="formRef" v-model="valid" class="pt-2">
          <v-row dense>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="form.name"
                label="이름"
                :rules="[req]"
                hide-details="auto"
              />
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model="form.emp_no"
                label="사번"
                hide-details="auto"
              />
            </v-col>

            <v-col cols="12" md="6">
              <v-select
                v-model="form.dept"
                :items="deptItems"
                label="부서"
                :rules="[req]"
                hide-details="auto"
              />
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model="form.title"
                label="직책"
                hide-details="auto"
              />
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model="form.hire_date"
                type="date"
                label="입사일"
                :rules="[req]"
                hide-details="auto"
              />
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model="form.email"
                label="이메일 (선택)"
                hide-details="auto"
              />
            </v-col>

            <v-col cols="12">
              <v-textarea
                v-model="form.memo"
                label="비고"
                rows="2"
                hide-details="auto"
              />
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>

      <v-divider />

      <v-card-actions class="justify-end">
        <v-btn variant="text" @click="close">취소</v-btn>
        <v-btn color="primary" variant="flat" :loading="saving" @click="onSubmit">
          저장
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import http from '@/services/http'
import { useToast } from '@/ui/composables/useToast'

const props = defineProps<{ modelValue: boolean }>()
const emit = defineEmits(['update:modelValue', 'saved'])

const open = ref(props.modelValue)
watch(() => props.modelValue, v => (open.value = v))
watch(open, v => emit('update:modelValue', v))

const { success, error } = useToast()
const formRef = ref()
const valid = ref(false)
const saving = ref(false)

const form = reactive({
  name: '',
  emp_no: '',
  dept: '',
  title: '',
  hire_date: '',
  email: '',
  memo: '',
})

const deptItems = ['FRONT', 'FNB', 'ENG', 'HK', 'SUPPORT']
const req = (v: any) => !!String(v ?? '').trim() || '필수 입력 항목입니다.'

function close() {
  emit('update:modelValue', false)
}

async function onSubmit() {
  const ok = await formRef.value?.validate?.()
  if (!ok?.valid) return
  try {
    saving.value = true
    const payload = { ...form }
    const res = await http.post('/api/hr/employees', payload)
    success('직원이 등록되었습니다.')
    emit('saved', res)
    close()
  } catch (e: any) {
    error('등록 실패: ' + (e?.message || '서버 오류'))
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.v-card-text {
  padding-top: 16px;
}
</style>
