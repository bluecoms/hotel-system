<template>
  <span class="badge" :class="kind">
    <slot />
  </span>
</template>

<script setup lang="ts">
const props = defineProps<{ kind?: 'neutral'|'success'|'warn'|'danger' }>()
</script>

<style scoped>
.badge{
  display:inline-flex; align-items:center; gap:6px;
  padding:.22rem .55rem;
  border-radius:999px;
  font-size:.82rem; font-weight:600;
  border:1px solid var(--line);
  background:#fff; color:var(--text);
}
.success{ color:var(--ok); border-color:color-mix(in oklab, var(--ok) 50%, #ffffff) }
.warn{ color:var(--warn); border-color:color-mix(in oklab, var(--warn) 50%, #ffffff) }
.danger{ color:var(--danger); border-color:color-mix(in oklab, var(--danger) 50%, #ffffff) }
</style>
