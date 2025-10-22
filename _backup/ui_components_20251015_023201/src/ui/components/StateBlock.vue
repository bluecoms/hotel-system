<template>
  <div class="pa-6 text-center text-medium-emphasis" role="status" :aria-live="loading ? 'polite' : 'off'">
    <v-progress-linear v-if="loading" indeterminate class="mb-3" />
    <div v-else-if="error">{{ $t('state.error') }}</div>
    <div v-else>{{ $t('state.empty') }}</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  loading?: boolean
  error?: boolean
}>()
</script>
