<template>
  <v-card class="pa-2">
    <v-card-title class="d-flex align-center justify-space-between">
      <div class="d-flex align-center gap8">
        <v-icon icon="mdi-food-fork-drink" size="18" class="text-medium-emphasis mr-1" />
        <span class="font-weight-bold">F&B 상품별 매출</span>
      </div>
      <v-chip size="small" variant="tonal" color="primary">
        {{ propertyCode }}
      </v-chip>
    </v-card-title>

    <v-divider class="mb-2" />

    <StateBlock :loading="loading" :error="err" :empty="!rows.length">
      <v-table density="comfortable">
        <thead>
          <tr>
            <th>카테고리</th>
            <th class="text-right">건수</th>
            <th class="text-right">금액</th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="r in rows" :key="r.category">
            <td>{{ r.category }}</td>
            <td class="text-right">{{ n(r.count) }}</td>
            <td class="text-right">{{ k(r.amount) }}</td>
          </tr>
        </tbody>

        <tfoot v-if="rows.length">
          <tr class="font-weight-bold">
            <td>Total</td>
            <td class="text-right">{{ n(tot.count) }}</td>
            <td class="text-right">{{ k(tot.amount) }}</td>
          </tr>
        </tfoot>
      </v-table>
    </StateBlock>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { getFnbSummary, type FnbSummaryResp } from '@/services/reports'
import { useToast } from '@/ui/composables/useToast'
import StateBlock from '@/ui/components/common/StateBlock.vue'

const props = defineProps<{
  dateFrom: string
  dateTo: string
  propertyCode?: string
}>()

const emit = defineEmits<{
  (e: 'totals', p: { amount: number; count: number }): void
}>()

const { error: toastError } = useToast()
const propertyCode = computed(() => props.propertyCode || 'MOP')

const loading = ref(false)
const rows = ref<{ category: string; amount: number; count: number }[]>([])
const err = ref<string | null>(null)

const tot = computed(() =>
  rows.value.reduce(
    (a, r) => ({
      amount: a.amount + (r.amount || 0),
      count: a.count + (r.count || 0),
    }),
    { amount: 0, count: 0 }
  )
)

const k = (n: number) => Number(n || 0).toLocaleString('ko-KR')
const n = (n: number) => Number(n || 0).toLocaleString('ko-KR')

async function load() {
  err.value = null
  loading.value = true
  try {
    const r: FnbSummaryResp = await getFnbSummary({
      date_from: props.dateFrom,
      date_to: props.dateTo,
      property_code: propertyCode.value,
    })

    rows.value = Array.isArray(r?.fnb)
      ? r.fnb.map((x) => ({
          category: String(x.category || ''),
          amount: Number(x.amount || 0),
          count: Number(x.count || 0),
        }))
      : []

    emit('totals', { amount: tot.value.amount, count: tot.value.count })
  } catch (e: any) {
    rows.value = []
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



