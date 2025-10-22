# /ui/components/common/StatPill.vue
<template>
  <v-chip
    :color="color"
    variant="tonal"
    size="small"
    class="font-weight-600 stat-pill"
  >
    <slot />
  </v-chip>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ color?: string }>(), { color: 'info' })
</script>

<style scoped>
.stat-pill {
  border-radius: var(--radius-xs);
  font-size: 0.85rem;
  padding: 0 8px;
  letter-spacing: -0.01em;
  color: var(--color-text);
}
</style>