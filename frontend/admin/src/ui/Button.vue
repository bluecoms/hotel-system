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
import { computed } from 'vue'   /* ★ 추가 */

const props = defineProps<{
  variant?: 'solid' | 'soft' | 'outline' | 'ghost'
  size?: 'sm' | 'md'
}>()

const variantClass = computed(() => `v-${props.variant ?? 'solid'}`)
const sizeClass = computed(() => `s-${props.size ?? 'md'}`)
</script>

<style scoped>
.btn{
  border-radius: var(--radius-sm);
  border:1px solid transparent;
  height: var(--control-h);
  padding: 0 12px;
  cursor: pointer;
  font-weight: 600;
  transition: .15s ease;
}
.btn:disabled{opacity:.6; cursor:not-allowed}

.v-solid{ background:var(--brand-600); color:#fff; box-shadow:var(--shadow-sm) }
.v-solid:hover{ background:var(--brand-700) }

.v-soft{ background:var(--brand-50); color:var(--brand-700); border-color:var(--brand-100) }
.v-soft:hover{ background:var(--brand-100) }

.v-outline{ background:#fff; color:var(--brand-700); border-color:var(--brand-300) }
.v-outline:hover{ background:var(--brand-50) }

.v-ghost{ background:transparent; color:var(--text); border-color:var(--line) }
.v-ghost:hover{ background:#fff }

.s-sm{ height:32px; padding:0 10px; font-size:.9rem }
.s-md{ height:var(--control-h) }
</style>
