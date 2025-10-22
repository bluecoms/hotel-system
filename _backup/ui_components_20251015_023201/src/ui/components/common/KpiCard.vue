<template>
  <v-card class="kpi-card" :elevation="elevated ? 2 : 0">
    <v-card-text class="pa-4">
      <div class="d-flex align-center justify-space-between mb-2">
        <div class="d-flex align-center gap4">
          <v-icon v-if="icon" :icon="icon" size="18" class="mr-1 text-medium-emphasis" />
          <span class="text-subtitle-2 font-weight-700 text-medium-emphasis">{{ label }}</span>
        </div>
        <v-chip v-if="badge" size="x-small" color="primary" variant="tonal">{{ badge }}</v-chip>
      </div>

      <div class="d-flex align-baseline gap6">
        <span v-if="prefix" class="prefix text-medium-emphasis">{{ prefix }}</span>
        <span class="value">{{ formattedValue }}</span>
        <span v-if="suffix" class="suffix text-medium-emphasis">{{ suffix }}</span>
      </div>

      <div v-if="delta !== undefined && delta !== null" class="mt-1 d-flex align-center" :class="deltaClass">
        <v-icon :icon="deltaIcon" size="14" class="mr-1" />
        <span class="font-weight-600">{{ formattedDelta }}</span>
        <span v-if="deltaLabel" class="ml-1 text-caption text-medium-emphasis">{{ deltaLabel }}</span>
      </div>

      <div v-if="hint || $slots.footer" class="mt-3 text-caption text-medium-emphasis">
        <slot name="footer">{{ hint }}</slot>
      </div>
    </v-card-text>

    <v-progress-linear
      v-if="progress !== undefined"
      :model-value="progress"
      height="6"
      color="primary"
      bg-color="grey-lighten-3"
      class="rounded-b-lg"
    />
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  label: string
  value?: number | string
  format?: 'number' | 'currency' | 'percent' | 'raw'
  prefix?: string
  suffix?: string
  badge?: string
  icon?: string
  hint?: string
  delta?: number
  deltaIsPercent?: boolean
  deltaLabel?: string
  positiveGood?: boolean
  progress?: number
  elevated?: boolean
}>()

const formattedValue = computed(() => {
  const v = props.value
  if (v === undefined || v === null || v === '') return '—'
  if (props.format === 'currency') return new Intl.NumberFormat('ko-KR', { style: 'currency', currency: 'KRW', maximumFractionDigits: 0 }).format(Number(v))
  if (props.format === 'percent') return `${Number(v).toFixed(1)}%`
  if (props.format === 'number') return new Intl.NumberFormat('ko-KR').format(Number(v))
  return String(v)
})

const deltaIcon = computed(() => props.delta && props.delta > 0 ? 'mdi-arrow-up-bold' : props.delta && props.delta < 0 ? 'mdi-arrow-down-bold' : 'mdi-minus')
const isGood = computed(() => props.delta == null ? null : props.positiveGood ? props.delta > 0 : props.delta < 0)
const deltaClass = computed(() => isGood.value === null ? '' : isGood.value ? 'text-success' : 'text-error')
const formattedDelta = computed(() => props.deltaIsPercent ? `${props.delta > 0 ? '+' : ''}${props.delta.toFixed(1)}%` : `${props.delta > 0 ? '+' : ''}${props.delta}`)
</script>

<style scoped>
.kpi-card {
  border-radius: var(--radius);
  border: 1px solid var(--color-line);
  background: rgb(var(--v-theme-surface));
  color: rgb(var(--v-theme-on-surface));
}
.value {
  font-size: 1.8rem;
  font-weight: 800;
  letter-spacing: -0.02em;
}
.prefix, .suffix {
  font-size: 1rem;
  font-weight: 600;
}
</style>
