<template>
  <div class="kpi-card">
    <div class="kpi-head">
      <span class="kpi-title">{{ title }}</span>
      <slot name="right"></slot>
    </div>
    <div class="kpi-body">
      <div class="kpi-value">
        <span v-if="prefix" class="muted">{{ prefix }}</span>{{ valueText }}
      </div>
      <div v-if="sub" class="kpi-sub">{{ sub }}</div>
      <slot></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  title: string
  value: string | number | null | undefined
  sub?: string
  prefix?: string
}>()

const valueText = computed(() => {
  if (props.value === null || props.value === undefined || props.value === 'N/A') return '—'
  if (typeof props.value === 'number') return new Intl.NumberFormat('ko-KR').format(props.value)
  return props.value
})
</script>

<style scoped>
.kpi-card{display:flex;flex-direction:column;gap:.5rem;padding:1rem;border:1px solid #e5e7eb;border-radius:14px;background:#fff}
.kpi-head{display:flex;align-items:center;justify-content:space-between}
.kpi-title{font-size:.95rem;color:#6b7280}
.kpi-body{display:flex;flex-direction:column;gap:.35rem}
.kpi-value{font-size:1.8rem;font-weight:700;letter-spacing:-.01em}
.kpi-value .muted{font-size:1rem;margin-right:.1rem;color:#6b7280}
.kpi-sub{font-size:.85rem;color:#6b7280}
</style>
