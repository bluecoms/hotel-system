<template>
  <ReportsShell
    title="매출 리포트"
    icon="mdi-chart-box-outline"
    property-code="MOP"
    @filter="onFilter"
  >
    <v-tabs v-model="tab" class="mb-3">
      <v-tab value="rooms">객실 매출</v-tab>
      <v-tab value="fnb">F&B 매출</v-tab>
    </v-tabs>

    <v-window v-model="tab">
      <v-window-item value="rooms">
        <StateBlock v-if="loadingRooms" :loading="true" />
        <RoomsSplit
          v-else
          :date-from="dateFrom"
          :date-to="dateTo"
          :property-code="propertyCode"
          @totals="onRoomsTotals"
        />
      </v-window-item>

      <v-window-item value="fnb">
        <StateBlock v-if="loadingFnb" :loading="true" />
        <FnbSummary
          v-else
          :date-from="dateFrom"
          :date-to="dateTo"
          :property-code="propertyCode"
          @totals="onFnbTotals"
        />
      </v-window-item>
    </v-window>
  </ReportsShell>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ReportsShell from './ReportsShell.vue'
import StateBlock from '@/ui/components/common/StateBlock.vue'
import RoomsSplit from './RoomsSplit.vue'
import FnbSummary from './FnbSummary.vue'
import { useKpiStore } from '@/stores/kpi'

const tab = ref<'rooms' | 'fnb'>('rooms')
const { pushTotals } = useKpiStore()
const loadingRooms = ref(false)
const loadingFnb = ref(false)
const dateFrom = ref('')
const dateTo = ref('')
const propertyCode = ref('MOP')

function onFilter(p: { date_from: string; date_to: string; property_code: string }) {
  dateFrom.value = p.date_from
  dateTo.value = p.date_to
  propertyCode.value = p.property_code
  loadingRooms.value = true
  loadingFnb.value = true
  window.dispatchEvent(new CustomEvent('refresh-reports', { detail: p }))
  setTimeout(() => { loadingRooms.value = false; loadingFnb.value = false }, 600)
}

function onRoomsTotals(t: any) {
  const ro = Number(t?.room_only ?? t?.roomOnly ?? 0)
  const pkg = Number(t?.package ?? t?.pkg ?? 0)
  const etc = Number(t?.other ?? t?.etc ?? 0)
  pushTotals({ rooms: { roomOnly: ro, pkg, etc } })
}
function onFnbTotals(t: { amount: number; count: number }) {
  pushTotals({ fnb: t })
}
</script>

<style scoped>
.v-tabs { border-bottom: 1px solid var(--color-line); }
</style>
