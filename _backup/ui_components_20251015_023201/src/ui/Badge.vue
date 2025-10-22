<template>
  <span class="badge" :class="kind">
    <slot />
  </span>
</template>

<script setup lang="ts">
const props = defineProps<{ kind?: 'neutral'|'success'|'warn'|'danger' }>()
</script>

<style scoped>
.badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: .22rem .55rem;
  border-radius: 999px;
  font-size: .82rem;
  font-weight: 600;
  border: 1px solid var(--color-line);
  background: rgb(var(--v-theme-surface));
  color: rgb(var(--v-theme-on-surface));
  box-shadow: var(--shadow-xs);
  transition: .15s ease;
}
.success {
  color: rgb(var(--v-theme-success));
  border-color: color-mix(in oklab, rgb(var(--v-theme-success)) 40%, white);
}
.warn {
  color: rgb(var(--v-theme-warning));
  border-color: color-mix(in oklab, rgb(var(--v-theme-warning)) 40%, white);
}
.danger {
  color: rgb(var(--v-theme-error));
  border-color: color-mix(in oklab, rgb(var(--v-theme-error)) 40%, white);
}
</style>
