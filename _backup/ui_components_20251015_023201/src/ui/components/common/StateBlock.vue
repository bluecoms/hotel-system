<template>
  <div class="pa-6 text-center" role="status" :aria-live="loading ? 'polite' : 'off'">
    <v-progress-linear v-if="loading" indeterminate class="mb-3" />
    <div v-else-if="error" class="text-error">{{ error }}</div>
    <div v-else-if="empty">{{ $t('state.empty') }}</div>
    <slot v-else />
  </div>
</template>

<script setup lang="ts">
defineProps<{ loading?: boolean; error?: string | null; empty?: boolean }>()
</script>
