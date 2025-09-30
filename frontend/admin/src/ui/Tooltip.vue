<template>
  <span class="tip-wrap" @mouseenter="open=true" @mouseleave="open=false">
    <slot />
    <transition name="fade">
      <span v-if="open" class="tip" :style="posStyle">{{ text }}</span>
    </transition>
  </span>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'   /* ★ 추가 */

const props = defineProps<{ text: string; placement?: 'top'|'bottom' }>()
const open = ref(false)
const posStyle = computed(() => ({
  transform: props.placement === 'bottom' ? 'translate(-50%, 8px)' : 'translate(-50%, -8px)',
  top: props.placement === 'bottom' ? '100%' : '0',
  bottom: props.placement === 'bottom' ? 'auto' : '100%',
}))
</script>

<style scoped>
.tip-wrap{ position:relative; display:inline-flex; }
.tip{
  position:absolute; left:50%;
  padding:.28rem .5rem; border-radius:8px; font-size:.78rem;
  background:#111827; color:#fff; white-space:nowrap; box-shadow:var(--shadow-md); z-index:5;
}
.fade-enter-active,.fade-leave-active{ transition: opacity .12s ease }
.fade-enter-from,.fade-leave-to{ opacity:0 }
</style>
