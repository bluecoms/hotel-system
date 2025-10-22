<template>
  <template v-for="t in items" :key="t.id">
    <v-snackbar
      v-model="t.active"
      :timeout="t.timeout ?? 2500"
      :color="colorOf(t.kind)"
      location="bottom right"
      elevation="6"
      class="toast"
    >
      <v-icon :icon="iconOf(t.kind)" size="18" class="mr-2" />
      <span>{{ t.message }}</span>
      <template #actions>
        <v-btn icon="mdi-close" variant="text" @click="remove(t.id)" />
      </template>
    </v-snackbar>
  </template>
</template>

<script setup lang="ts">
import { ref } from 'vue'

type ToastKind = 'info' | 'success' | 'error' | 'warning'
interface ToastItem { id: number; message: string; kind: ToastKind; timeout?: number; active: boolean }

const items = ref<ToastItem[]>([])
let counter = 0

function push(message: string, kind: ToastKind = 'info', timeout = 2500) {
  const id = ++counter
  items.value.unshift({ id, message, kind, timeout, active: true })
  if (items.value.length > 3) items.value.pop()
}

function remove(id: number) {
  items.value = items.value.filter(t => t.id !== id)
}

function colorOf(k: ToastKind) {
  return { info: 'primary', success: 'success', error: 'error', warning: 'warning' }[k]
}
function iconOf(k: ToastKind) {
  return { info: 'mdi-information', success: 'mdi-check-circle', error: 'mdi-alert-circle', warning: 'mdi-alert' }[k]
}

// 전역 접근용 (useToast)
export function useToast() {
  return {
    info: (m: string) => push(m, 'info'),
    success: (m: string) => push(m, 'success'),
    error: (m: string) => push(m, 'error'),
    warning: (m: string) => push(m, 'warning'),
  }
}
</script>

<style scoped>
.toast :deep(.v-snackbar__wrapper){ min-width:320px; }
</style>
