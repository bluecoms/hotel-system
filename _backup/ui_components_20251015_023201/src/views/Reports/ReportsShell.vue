<template>
  <section class="report-shell">
    <div class="shell-header">
      <div class="d-flex align-center gap8">
        <v-icon v-if="icon" :icon="icon" size="18" class="text-medium-emphasis" />
        <h2 class="text-h6 font-weight-bold">{{ title }}</h2>
        <v-chip size="small" variant="tonal" color="primary">
          {{ propertyCode }}
        </v-chip>
      </div>
      <div class="actions">
        <slot name="actions" />
      </div>
    </div>

    <div class="shell-toolbar">
      <v-text-field
        v-model="dateFrom"
        label="From (YYYY-MM-DD)"
        density="comfortable"
        class="minw-160"
        hide-details
      />
      <v-text-field
        v-model="dateTo"
        label="To (YYYY-MM-DD)"
        density="comfortable"
        class="minw-160"
        hide-details
      />
      <v-btn variant="text" @click="setThisMonth">이번 달</v-btn>
      <v-btn variant="text" @click="setToday">오늘</v-btn>
      <v-btn variant="flat" color="primary" @click="emitFilter">조회</v-btn>
    </div>

    <div class="shell-body">
      <slot
        :date-from="dateFrom"
        :date-to="dateTo"
        :property-code="propertyCode"
      />
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// props
const props = defineProps<{
  title: string
  icon?: string
  propertyCode?: string
}>()

const emit = defineEmits<{
  (e: 'filter', params: { date_from: string; date_to: string; property_code: string }): void
}>()

// propertyCode (기본값: MOP)
const propertyCode = props.propertyCode || 'MOP'

// 날짜 유틸
function pad2(n: number) { return String(n).padStart(2, '0') }
function ymd(d: Date)     { return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}` }
function firstDayOfMonth(d = new Date()) { return new Date(d.getFullYear(), d.getMonth(), 1) }
function lastDayOfMonth(d = new Date())  { return new Date(d.getFullYear(), d.getMonth() + 1, 0) }

const dateFrom = ref(ymd(firstDayOfMonth(new Date())))
const dateTo   = ref(ymd(lastDayOfMonth(new Date())))

function setThisMonth() {
  const t = new Date()
  dateFrom.value = ymd(firstDayOfMonth(t))
  dateTo.value   = ymd(lastDayOfMonth(t))
}
function setToday() {
  const t = ymd(new Date())
  dateFrom.value = t
  dateTo.value   = t
}

function emitFilter() {
  emit('filter', { date_from: dateFrom.value, date_to: dateTo.value, property_code: propertyCode })
}
</script>

<style scoped>
.report-shell {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 1100px;
  margin: 0 auto;
  padding: 12px;
}

/* 상단 헤더 */
.shell-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 툴바 */
.shell-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  padding: 4px 0 10px;
  border-bottom: 1px solid var(--color-line);
}
.minw-160 { min-width: 160px; }

/* 본문 */
.shell-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
