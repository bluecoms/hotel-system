<template>
  <div class="cs-wrap">
    <slot />
    <div class="cs-overlay">
      <div class="cs-chip">{{ label }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ label?: string }>()
</script>

<style scoped>
.cs-wrap{ position:relative }
.cs-overlay{
  position:absolute; inset:0;
  background:rgba(0,0,0,.35);
  backdrop-filter:saturate(60%) blur(1px);
  display:flex; align-items:center; justify-content:center;
  border-radius:12px;
  pointer-events:none;
}
.cs-chip{
  color:#fff; font-weight:700; letter-spacing:.2px;
  background:rgba(0,0,0,.55);
  border:1px solid rgba(255,255,255,.25);
  padding:8px 12px; border-radius:999px;
  text-transform:uppercase; font-size:12px;
}
</style>
