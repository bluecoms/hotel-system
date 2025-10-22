# /ui/components/common/ConfirmDialog.vue
<template>
  <v-dialog v-model="open" max-width="400">
    <v-card>
      <v-card-title class="font-weight-bold">
        <v-icon :icon="icon" size="18" class="mr-1" />
        {{ title }}
      </v-card-title>
      <v-card-text class="text-body-2">
        {{ message }}
      </v-card-text>
      <v-card-actions class="justify-end">
        <v-btn variant="text" @click="cancel">{{ cancelText }}</v-btn>
        <v-btn color="primary" @click="confirm">{{ confirmText }}</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = withDefaults(defineProps<{
  modelValue: boolean
  title?: string
  message?: string
  icon?: string
  confirmText?: string
  cancelText?: string
}>(), {
  title: '확인',
  message: '이 작업을 계속 진행하시겠습니까?',
  icon: 'mdi-help-circle-outline',
  confirmText: '확인',
  cancelText: '취소',
})

const emit = defineEmits(['update:modelValue', 'confirm', 'cancel'])
const open = ref(props.modelValue)

function confirm() {
  emit('confirm')
  emit('update:modelValue', false)
}
function cancel() {
  emit('cancel')
  emit('update:modelValue', false)
}
</script>
