# /ui/components/common/LoadingOverlay.vue
<template>
  <div v-if="show" class="pos">
    <v-progress-circular indeterminate size="28" />
  </div>
</template>
<script setup lang="ts">
defineProps<{ show:boolean }>()
</script>
<style scoped>
.pos{ position:absolute; inset:0; display:flex; align-items:center; justify-content:center; background:rgba(255,255,255,.5); z-index:5; }
</style>
