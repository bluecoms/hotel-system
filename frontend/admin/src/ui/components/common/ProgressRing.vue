<template>
  <div class="ring" :style="{ '--size': size + 'px' }" role="img" :aria-label="`${percent}%`">
    <svg :width="size" :height="size" viewBox="0 0 44 44">
      <circle class="bg" cx="22" cy="22" r="19.5" />
      <circle
        class="fg"
        cx="22" cy="22" r="19.5"
        :style="{ 'stroke-dasharray': dash, 'stroke-dashoffset': offset }"
      />
    </svg>
    <div class="center">
      <div class="val">{{ Math.round(percent) }}%</div>
      <div class="sub">Progress</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
const props = withDefaults(defineProps<{ percent: number; size?: number }>(), { size: 96 })
const CIRC = 2 * Math.PI * 19.5
const dash = `${CIRC} ${CIRC}`
const offset = computed(() =>
  `${CIRC * (1 - Math.max(0, Math.min(1, props.percent / 100)))}`
)
</script>

<style scoped>
.ring { --size: 96px; position: relative; width: var(--size); height: var(--size); }
svg { transform: rotate(-90deg); }
.bg { fill: none; stroke: rgb(var(--v-theme-surface-variant)); stroke-width: 5; }
.fg { fill: none; stroke: rgb(var(--v-theme-primary)); stroke-width: 5; stroke-linecap: round; transition: stroke-dashoffset .5s ease; }
.center { position: absolute; inset: 0; display: grid; place-items: center; text-align: center; }
.val { font-weight: 700; font-size: 1rem; color: rgb(var(--v-theme-on-surface)); }
.sub { font-size: .75rem; color: var(--color-muted); margin-top: .1rem; }
</style>
