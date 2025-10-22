# /ui/components/common/ToastHost.vue
<template>
  <template v-for="item in items" :key="item.id">
    <v-snackbar
      :model-value="true"
      :timeout="hovering.has(item.id) ? 0 : (item.timeout ?? 2500)"
      :color="colorOf(item.kind)"
      location="bottom right"
      elevation="8"
      class="toast-host"
      :role="item.kind==='error' ? 'alert' : 'status'"
      :aria-live="item.ariaLive ?? (item.kind==='error' ? 'assertive' : 'polite')"
      @update:modelValue="(v:boolean)=>{ if(!v) remove(item.id) }"
      @timeout="remove(item.id)"
      @mouseenter="hovering.add(item.id)"
      @mouseleave="hovering.delete(item.id)"
    >
      <div class="toast-row">
        <v-icon :icon="iconOf(item.kind)" size="18" class="mr-2" />
        <span class="toast-msg">{{ item.message }}</span>
        <v-spacer />
        <v-btn
          variant="text"
          density="comfortable"
          icon="mdi-close"
          class="ml-2"
          @click="remove(item.id)"
          :aria-label="$t ? $t('cta.close') : '닫기'"
        />
      </div>
    </v-snackbar>
  </template>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ToastItem, ToastKind } from '@/ui/composables/useToast'
import { useToast } from '@/ui/composables/useToast'

const { queue, remove } = useToast()

// 하단 우측에 3개까지만 스택
const items = computed<ToastItem[]>(() => queue.value.slice(0, 3))

// 호버 시 자동닫힘 일시정지
const hovering = ref<Set<number>>(new Set())

function colorOf(kind: ToastKind) {
  switch (kind) {
    case 'success': return 'success'
    case 'error':   return 'error'
    case 'warning': return 'warning'
    default:        return 'primary'
  }
}
function iconOf(kind: ToastKind) {
  switch (kind) {
    case 'success': return 'mdi-check-circle'
    case 'error':   return 'mdi-alert-circle'
    case 'warning': return 'mdi-alert'
    default:        return 'mdi-information'
  }
}
</script>

<style scoped>
.toast-host :deep(.v-snackbar__wrapper){ min-width: 320px; }
.toast-row{ display:flex; align-items:center; }
.toast-msg{
  display:inline-block;
  max-width: 520px;
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
}
@media (max-width: 640px){
  .toast-host :deep(.v-snackbar__wrapper){ min-width: 260px; }
  .toast-msg{ max-width: 240px; }
}
</style>
