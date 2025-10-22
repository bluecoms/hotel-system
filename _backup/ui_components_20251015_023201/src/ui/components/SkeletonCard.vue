<template>
  <div class="sk-wrap">
    <div class="sk-line sk-title" />
    <div v-for="n in lines" :key="n" class="sk-line" />
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ lines?: number }>(), { lines: 3 })
</script>

<style scoped>
.sk-wrap{ display:flex; flex-direction:column; gap:10px }
.sk-line{
  height:14px; border-radius:8px;
  background: linear-gradient(90deg, #eee 0%, #f5f5f5 50%, #eee 100%);
  animation: sk 1.2s infinite;
}
.sk-title{ width:60%; height:16px; margin-bottom:4px }
@keyframes sk{
  0%{ background-position:0% 50% }
  100%{ background-position:200% 50% }
}
</style>
