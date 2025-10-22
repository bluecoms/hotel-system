<template>
  <div class="wrap" :title="`${percent}%`">
    <div class="bar" :style="{ width: `${Math.max(0, Math.min(100, percent))}%` }" />
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ percent: number }>()
</script>

<style scoped>
.wrap {
  height: 10px;
  background: rgb(var(--v-theme-surface-variant));
  border-radius: 999px;
  overflow: hidden;
  border: 1px solid var(--color-line);
}
.bar {
  height: 100%;
  background: linear-gradient(90deg,
    rgb(var(--v-theme-primary-light)),
    rgb(var(--v-theme-primary))
  );
  transition: width .4s ease;
}
</style>
