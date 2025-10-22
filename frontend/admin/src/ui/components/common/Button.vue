<template>
  <button
    class="btn"
    :class="[variantClass, sizeClass]"
    v-bind="$attrs"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  variant?: 'solid' | 'soft' | 'outline' | 'ghost'
  size?: 'sm' | 'md'
}>()

const variantClass = computed(() => `v-${props.variant ?? 'solid'}`)
const sizeClass = computed(() => `s-${props.size ?? 'md'}`)
</script>

<style scoped>
.btn {
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  font-weight: 600;
  cursor: pointer;
  transition: background .15s ease, color .15s ease;
  padding: 0 14px;
  height: var(--control-h);
}
.btn:disabled { opacity: .6; cursor: not-allowed }

/* Variants */
.v-solid { background: rgb(var(--v-theme-primary)); color: #fff; box-shadow: var(--shadow-sm); }
.v-solid:hover { background: color-mix(in oklab, rgb(var(--v-theme-primary)) 85%, black); }

.v-soft { background: rgb(var(--v-theme-primary-light)); color: rgb(var(--v-theme-primary-dark)); }
.v-soft:hover { background: color-mix(in oklab, rgb(var(--v-theme-primary-light)) 90%, white); }

.v-outline { background: transparent; color: rgb(var(--v-theme-primary)); border-color: rgb(var(--v-theme-primary)); }
.v-outline:hover { background: rgba(var(--v-theme-primary), .05); }

.v-ghost { background: transparent; color: rgb(var(--v-theme-on-surface)); }
.v-ghost:hover { background: rgba(var(--v-theme-primary), .08); }

/* Sizes */
.s-sm { height: 32px; font-size: .88rem; padding: 0 10px; }
.s-md { height: var(--control-h); }
</style>
