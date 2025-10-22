<template>
  <v-card class="board-list" flat>
    <div class="d-flex align-center justify-space-between mb-3">
      <slot name="title">
        <h3 v-if="title" class="text-h6 font-weight-medium">{{ title }}</h3>
      </slot>
      <slot name="actions" />
    </div>

    <v-data-table
      :headers="headers"
      :items="items"
      :loading="loading"
      :items-per-page="perPage"
      v-model:page="page"
      density="comfortable"
      hover
      class="rounded-xl elevation-1"
      :no-data-text="t('state.empty')"
      :loading-text="t('state.loading')"
      @click:row="onRowClick"
    >
      <template #top>
        <slot name="filters" />
      </template>

      <template v-for="h in headers" v-slot:[`item.${h.key}`]="scope">
        <slot :name="`item.${h.key}`" v-bind="scope" />
      </template>

      <template #bottom>
        <v-pagination
          v-model="page"
          :length="pages"
          :total-visible="7"
          class="py-3"
        />
      </template>

      <template #no-data>
        <slot name="no-data">
          <NoDataBox :message="t('state.empty')" />
        </slot>
      </template>
    </v-data-table>
  </v-card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import NoDataBox from '@/ui/components/NoDataBox.vue'

export interface BoardHeader {
  title: string
  key: string
  align?: 'start' | 'center' | 'end'
  sortable?: boolean
  width?: string | number
}

const props = defineProps<{
  title?: string
  headers: BoardHeader[]
  items: any[]
  total?: number
  perPage?: number
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:page', v: number): void
  (e: 'row-click', row: any): void
}>()

const { t } = useI18n()

const page = ref(1)
const perPage = computed(() => props.perPage ?? 10)
const loading = computed(() => props.loading ?? false)
const pages = computed(() => {
  const total = props.total ?? props.items.length
  return Math.max(1, Math.ceil(total / perPage.value))
})

function onRowClick(e: MouseEvent, ctx: any) {
  const raw = ctx?.item?.raw ?? ctx?.item ?? ctx
  emit('row-click', raw)
}

watch(page, v => emit('update:page', v))

// 선택: 필터로 total이 줄어들 때 페이지 보정
watch([() => props.total, perPage], () => {
  const total = props.total ?? props.items.length
  const max = Math.max(1, Math.ceil(total / perPage.value))
  if (page.value > max) page.value = max
})
</script>

<style scoped>
.board-list {
  border-radius: var(--radius);
  border: 1px solid var(--color-line);
  background: rgb(var(--v-theme-surface));
  box-shadow: var(--shadow-sm);
  padding: 1rem;
}
.v-data-table {
  font-size: 0.9rem;
}
</style>
