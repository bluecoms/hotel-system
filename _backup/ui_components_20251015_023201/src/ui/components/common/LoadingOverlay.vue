<template>
  <transition name="fade">
    <div v-if="show" class="overlay">
      <v-progress-circular indeterminate color="primary" size="32" />
    </div>
  </transition>
</template>

<script setup lang="ts">
defineProps<{ show: boolean }>()
</script>

<style scoped>
.overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255,255,255,.5);
  backdrop-filter: blur(1px);
  z-index: 999;
}
.fade-enter-active, .fade-leave-active { transition: opacity .2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
