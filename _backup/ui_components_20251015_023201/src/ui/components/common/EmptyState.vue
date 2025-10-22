<template>
  <div class="empty text-center text-medium-emphasis py-8">
    <v-icon icon="mdi-database-off" size="28" class="mb-2" />
    <div class="text-subtitle-2 font-weight-600">{{ title }}</div>
    <div class="text-body-2">{{ subtitle }}</div>
    <div class="mt-3"><slot /></div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ title?: string; subtitle?: string }>()
</script>

<style scoped>
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
</style>
