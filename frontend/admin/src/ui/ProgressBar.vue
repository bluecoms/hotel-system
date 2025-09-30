<template>
  <div class="wrap" :title="`${percent}%`">
    <div class="bar" :style="{ width: `${Math.max(0, Math.min(100, percent))}%` }" />
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ percent: number }>()
</script>

<style scoped>
.wrap{height:10px; background:#f1f5f9; border-radius:999px; overflow:hidden; border:1px solid var(--line)}
.bar{height:100%; background:linear-gradient(90deg,var(--brand-400),var(--brand-600))}
</style>
