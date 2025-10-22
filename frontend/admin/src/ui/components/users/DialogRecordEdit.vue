<template>
  <v-dialog v-model="model" max-width="480" persistent>
    <v-card rounded="lg">
      <v-card-title class="d-flex align-center justify-space-between">
        <span class="text-h6 font-weight-bold">근태 기록 수정</span>
        <v-btn icon="mdi-close" variant="text" @click="close" />
      </v-card-title>

      <v-divider />

      <v-card-text>
        <v-form ref="formRef">
          <v-text-field
            v-model="form.employee_name"
            label="직원명"
            readonly
            density="comfortable"
          />
          <v-text-field
            v-model="form.work_date"
            label="근무일자"
            readonly
            density="comfortable"
          />
          <v-select
            v-model="form.status"
            :items="statusItems"
            label="근무 상태"
            density="comfortable"
          />
          <v-textarea
            v-model="form.memo"
            label="메모"
            rows="2"
            density="comfortable"
          />
        </v-form>
      </v-card-text>

      <v-card-actions class="justify-end">
        <v-btn variant="text" @click="close">취소</v-btn>
        <v-btn color="primary" variant="flat" :loading="saving" @click="save">
          저장
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch, reactive } from 'vue'
import * as RecordsApi from '@/services/records'
import { useToast } from '@/ui/composables/useToast'

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  record: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue', 'saved'])
const toast = useToast()

const model = ref(props.modelValue)
watch(() => props.modelValue, v => (model.value = v))
watch(model, v => emit('update:modelValue', v))

const form = reactive({
  id: 0,
  employee_name: '',
  work_date: '',
  status: '',
  memo: '',
})
const statusItems = [
  { title: '출근', value: 'present' },
  { title: '결근', value: 'absent' },
  { title: '휴무', value: 'off' },
]

watch(() => props.record, (r) => {
  if (!r) return
  form.id = r.id
  form.employee_name = r.employee_name
  form.work_date = r.work_date
  form.status = r.status
  form.memo = r.memo || ''
})

const saving = ref(false)

async function save() {
  saving.value = true
  try {
    await RecordsApi.update(form.id, {
      status: form.status,
      memo: form.memo,
    })
    toast.success('기록이 저장되었습니다.')
    emit('saved')
    close()
  } catch {
    toast.error('저장 실패')
  } finally {
    saving.value = false
  }
}

function close() {
  model.value = false
}
</script>
