<template>
  <v-card class="pa-2">
    <v-card-title class="d-flex align-center justify-space-between">
      <div class="d-flex align-center gap8">
        <v-icon icon="mdi-bed-outline" size="18" class="text-medium-emphasis mr-1" />
        <span class="font-weight-bold">객실 매출 분리</span>
      </div>
      <v-chip size="small" variant="tonal" color="primary">
        {{ propertyCode }}
      </v-chip>
    </v-card-title>

    <v-divider class="mb-2" />

    <StateBlock :loading="loading" :error="err" :empty="!hasData">
      <v-table density="comfortable">
        <thead>
          <tr>
            <th>구분</th>
            <th class="text-right">금액</th>
          </tr>
        </thead>
        <tbody>
          <tr><td>룸온리</td><td class="text-right">{{ k(rooms.room_only) }}</td></tr>
          <tr><td>패키지</td><td class="text-right">{{ k(rooms.package) }}</td></tr>
          <tr><td>현금</td><td class="text-right">{{ k(rooms.cash) }}</td></tr>
          <tr><td>카드</td><td class="text-right">{{ k(rooms.card) }}</td></tr>
          <tr><td>기타</td><td class="text-right">{{ k(rooms.etc) }}</td></tr>
          <tr class="font-weight-bold">
            <td>Total</td>
            <td class="text-right">{{ k(total) }}</td>
          </tr>
        </tbody>
      </v-table>
    </StateBlock>
  </v-card>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { getRoomsSplit, type RoomsSplitResp } from '@/services/reports'
import { useToast } from '@/ui/composables/useToast'
import StateBlock from '@/ui/components/common/StateBlock.vue'

const props = defineProps<{
  dateFrom: string
  dateTo: string
  propertyCode?: string
}>()

const emit = defineEmits<{
  (e: 'totals', p: {
    roomOnly: number
    package: number
    etc: number
    cash: number
    card: number
  }): void
}>()

const { error: toastError } = useToast()
const propertyCode = computed(() => props.propertyCode || 'MOP')

const loading = ref(false)
const rooms = ref({ room_only: 0, package: 0, cash: 0, card: 0, etc: 0 })
const err = ref<string | null>(null)
const total = computed(() =>
  rooms.value.room_only +
  rooms.value.package +
  rooms.value.cash +
  rooms.value.card +
  rooms.value.etc
)
const hasData = computed(() => total.value > 0)
const k = (n: number) => Number(n || 0).toLocaleString('ko-KR')

async function load() {
  err.value = null
  loading.value = true
  try {
    const r: RoomsSplitResp = await getRoomsSplit({
      date_from: props.dateFrom,
      date_to: props.dateTo,
      property_code: propertyCode.value,
    })
    rooms.value = r?.rooms ?? { room_only: 0, package: 0, cash: 0, card: 0, etc: 0 }
    emit('totals', {
      roomOnly: rooms.value.room_only,
      package: rooms.value.package,
      etc: rooms.value.etc,
      cash: rooms.value.cash,
      card: rooms.value.card,
    })
  } catch (e: any) {
    rooms.value = { room_only: 0, package: 0, cash: 0, card: 0, etc: 0 }
    err.value = e?.message || '로드 실패'
    toastError(err.value)
  } finally {
    loading.value = false
  }
}

watch(() => [props.dateFrom, props.dateTo, propertyCode.value], load, { immediate: true })
</script>

<style scoped>
.v-card {
  border: 1px solid var(--color-line);
  border-radius: var(--radius);
  background: rgb(var(--v-theme-surface));
}
.gap8 {
  gap: 8px;
}
</style>
