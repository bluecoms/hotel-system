<template>
  <v-card class="kpi-card" :elevation="1" :ripple="false">
    <v-card-text class="pa-4">
      <div class="row head">
        <div class="title">
          <v-icon v-if="icon" :icon="icon" size="18" class="mr-1" />
          {{ label }}
        </div>
        <v-chip v-if="badge" size="x-small" variant="tonal" class="badge">
          {{ badge }}
        </v-chip>
      </div>

      <div class="row main mt-2">
        <div class="value">
          <span v-if="prefix" class="prefix">{{ prefix }}</span>
          <span class="num">{{ formattedValue }}</span>
          <span v-if="suffix" class="suffix">{{ suffix }}</span>
        </div>

        <div class="delta" :class="deltaClass" v-if="delta !== undefined && delta !== null">
          <v-icon :icon="deltaIcon" size="16" class="mr-1" />
          <span class="num">{{ formattedDelta }}</span>
          <span v-if="deltaLabel" class="muted ml-1">{{ deltaLabel }}</span>
        </div>
      </div>

      <div v-if="$slots.footer || hint" class="foot mt-3">
        <slot name="footer">
          <div class="muted">{{ hint }}</div>
        </slot>
      </div>
    </v-card-text>

    <div v-if="progress !== undefined" class="px-4 pb-4">
      <v-progress-linear
        :model-value="progress"
        height="8"
        rounded
        :color="barColor"
        bg-color="grey-lighten-3"
      />
      <div class="muted mt-1 text-right">{{ Math.round(progress) }}%</div>
    </div>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  label: string
  value?: number | string
  prefix?: string
  suffix?: string
  format?: 'number' | 'currency' | 'percent' | 'raw'
  locale?: string
  currency?: string
  decimals?: number
  icon?: string
  badge?: string
  hint?: string
  progress?: number // 0~100
  delta?: number // 증감 (절대값 또는 퍼센트 값)
  deltaIsPercent?: boolean
  deltaLabel?: string
  positiveGood?: boolean // true면 증가가 좋음, false면 감소가 좋음
  color?: string // 카드 강조색(선택)
}>()

const locale = computed(() => props.locale || 'ko-KR')
const decimals = computed(() => props.decimals ?? (props.format === 'currency' ? 0 : 1))

const formattedValue = computed(() => {
  const v = props.value
  if (v === undefined || v === null || v === '') return '-'
  if (props.format === 'raw') return String(v)
  if (props.format === 'currency') {
    const cur = props.currency || 'KRW'
    return new Intl.NumberFormat(locale.value, { style: 'currency', currency: cur, maximumFractionDigits: decimals.value }).format(Number(v))
  }
  if (props.format === 'percent') {
    const n = Number(v)
    return `${n.toFixed(decimals.value)}%`
  }
  // default number (compact)
  return new Intl.NumberFormat(locale.value, {
    notation: 'compact',
    maximumFractionDigits: decimals.value,
  }).format(Number(v))
})

const deltaIcon = computed(() => {
  if (props.delta === undefined || props.delta === null) return ''
  const up = props.delta > 0
  return up ? 'mdi-arrow-up-bold' : (props.delta < 0 ? 'mdi-arrow-down-bold' : 'mdi-minus')
})

const isGood = computed(() => {
  if (props.delta === undefined || props.delta === null) return null
  const up = props.delta > 0
  return props.positiveGood ? up : !up
})

const deltaClass = computed(() => {
  if (props.delta === undefined || props.delta === null) return ''
  return isGood.value === null
    ? ''
    : (isGood.value ? 'good' : 'bad')
})

const formattedDelta = computed(() => {
  const d = props.delta
  if (d === undefined || d === null) return ''
  const sign = d > 0 ? '+' : ''
  if (props.deltaIsPercent) return `${sign}${Number(d).toFixed(1)}%`
  return `${sign}${new Intl.NumberFormat(locale.value, { notation: 'compact', maximumFractionDigits: 1 }).format(Number(d))}`
})

const barColor = computed(() => props.color || (isGood.value === null ? 'primary' : (isGood.value ? 'success' : 'error')))
</script>

<style scoped>
.kpi-card {
  border: 1px solid var(--color-line);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
  background: var(--color-surface);
}
.row { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.head .title { font-weight: 700; color: var(--color-muted); font-size: .92rem; display: flex; align-items: center; }
.badge { margin-left: auto; }
.main .value { font-weight: 800; font-size: 1.75rem; letter-spacing: .2px; color: var(--color-text); display: flex; align-items: baseline; gap: 4px; }
.main .value .prefix, .main .value .suffix { font-size: 1rem; color: var(--color-muted); font-weight: 600; }
.delta { display: inline-flex; align-items: center; font-weight: 700; }
.delta.good { color: var(--color-success); }
.delta.bad { color: var(--color-error); }
.muted { color: var(--color-muted); font-weight: 500; }
</style>
