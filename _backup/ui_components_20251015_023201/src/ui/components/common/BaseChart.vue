<template>
  <div class="chart-wrap">
    <canvas ref="canvas" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { Chart, type ChartConfiguration } from 'chart.js/auto'

const props = defineProps<{
  config: ChartConfiguration
}>()

const canvas = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null

onMounted(() => {
  if (canvas.value) {
    chart = new Chart(canvas.value, props.config)
  }
})

watch(() => props.config, (cfg) => {
  if (chart) {
    chart.destroy()
    chart = new Chart(canvas.value!, cfg)
  }
}, { deep: true })

onBeforeUnmount(() => {
  if (chart) chart.destroy()
})
</script>

<style scoped>
.chart-wrap {
  width: 100%;
  height: 100%;
  position: relative;
}
canvas {
  width: 100% !important;
  height: 100% !important;
}
</style>
