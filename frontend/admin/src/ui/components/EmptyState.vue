<template>
  <div class="text-center text-medium-emphasis py-8">
    <div class="text-h6 mb-1">{{ title }}</div>
    <div class="text-body-2">{{ subtitle }}</div>
    <div class="mt-3"><slot /></div>
  </div>
</template>
<script setup lang="ts">
defineProps<{ title?:string; subtitle?:string }>()
</script>
