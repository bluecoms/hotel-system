<template>
  <div class="chart-wrapper" ref="wrapper">
    <canvas ref="canvas"></canvas>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, onBeforeUnmount, ref, watch, nextTick } from 'vue'
import { Chart, ChartConfiguration, registerables } from 'chart.js'

// Chart.js 기본 플러그인 등록
Chart.register(...registerables)

interface Props {
  type: string
  data: any
  options?: any
  autoResize?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  type: 'bar',
  options: () => ({}),
  autoResize: true,
})

const wrapper = ref<HTMLElement | null>(null)
const canvas = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null
let resizeObserver: ResizeObserver | null = null
let resizeTimer: number | null = null

function renderChart() {
  if (!canvas.value) return
  if (chart) chart.destroy()

  chart = new Chart(canvas.value, {
    type: props.type,
    data: props.data,
    options: {
      maintainAspectRatio: false,
      responsive: props.autoResize,
      plugins: {
        legend: {
          labels: {
            font: { family: 'var(--font-base)' },
            color: 'var(--color-text)',
          },
        },
        tooltip: {
          titleFont: { family: 'var(--font-base)' },
          bodyFont: { family: 'var(--font-base)' },
        },
      },
      scales: {
        x: {
          ticks: { color: 'var(--color-muted)' },
          grid: { color: 'var(--color-line)' },
        },
        y: {
          ticks: { color: 'var(--color-muted)' },
          grid: { color: 'var(--color-line)' },
        },
      },
      ...props.options,
    },
  } as ChartConfiguration)
}

onMounted(async () => {
  await nextTick()
  renderChart()

  if (props.autoResize && wrapper.value) {
    resizeObserver = new ResizeObserver(() => {
      if (resizeTimer) clearTimeout(resizeTimer)
      resizeTimer = window.setTimeout(() => renderChart(), 150)
    })
    resizeObserver.observe(wrapper.value)
  }
})

onBeforeUnmount(() => {
  if (chart) {
    chart.destroy()
    chart = null
  }
  if (resizeObserver && wrapper.value) {
    resizeObserver.unobserve(wrapper.value)
    resizeObserver = null
  }
})

watch(() => props.data, () => renderChart(), { deep: true })
watch(() => props.type, () => renderChart())
watch(() => props.options, () => renderChart(), { deep: true })
</script>

<style scoped>
.chart-wrapper {
  position: relative;
  width: 100%;
  min-height: 280px;
}
canvas {
  width: 100% !important;
  height: 100% !important;
  font-family: var(--font-base);
}
</style>
