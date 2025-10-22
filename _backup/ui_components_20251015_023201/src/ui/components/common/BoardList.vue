<template>
  <v-card class="board-list" flat>
    <div class="d-flex align-center justify-space-between mb-2">
      <div class="d-flex align-center gap8">
        <v-icon v-if="icon" :icon="icon" size="18" class="mr-1 text-medium-emphasis" />
        <h3 class="text-h6 font-weight-bold">{{ title }}</h3>
        <v-chip v-if="badge" size="x-small" variant="tonal">{{ badge }}</v-chip>
      </div>
      <div>
        <slot name="actions" />
      </div>
    </div>

    <div v-if="$slots.filters" class="mb-2">
      <slot name="filters" />
    </div>

    <v-data-table
      :headers="headers"
      :items="items"
      :loading="loading"
      :items-per-page="perPage"
      v-model:page="page"
      density="comfortable"
      hover
      fixed-header
      class="rounded-xl elevation-1"
      :no-data-text="t('state.empty')"
      :loading-text="t('state.loading')"
      @click:row="onRowClick"
    >
      <template v-for="h in headers" v-slot:[`item.${h.key}`]="scope">
        <slot :name="`cell.${h.key}`" v-bind="scope" />
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
        <EmptyState :title="t('state.empty')" />
      </template>
    </v-data-table>

    <LoadingOverlay :show="loading" />
  </v-card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import EmptyState from '@/ui/components/common/EmptyState.vue'
import LoadingOverlay from '@/ui/components/common/LoadingOverlay.vue'

export interface BoardHeader {
  title: string
  key: string
  align?: 'start' | 'center' | 'end'
  sortable?: boolean
  width?: string | number
}

const props = defineProps<{
  title: string
  icon?: string
  badge?: string
  headers: BoardHeader[]
  items: any[]
  total?: number
  perPage?: number
  loading?: boolean
}>()

const emit = defineEmits<{
  (e:'update:page', v:number): void
  (e:'row-click', row:any): void
}>()

const { t } = useI18n()
const page = ref(1)
const perPage = computed(() => props.perPage ?? 10)
const loading = computed(() => props.loading ?? false)
const pages = computed(() => {
  const total = props.total ?? props.items.length
  return Math.max(1, Math.ceil(total / perPage.value))
})

function onRowClick(row: any) {
  emit('row-click', row)
}

watch(page, v => emit('update:page', v))
</script>

<style scoped>
.board-list{
  border-radius: var(--radius);
  border: 1px solid var(--color-line);
  background: rgb(var(--v-theme-surface));
  box-shadow: var(--shadow-sm);
  padding: 1rem;
  position: relative;
}
.v-data-table{ font-size:.9rem }
.gap8{ gap:8px }
</style>
vue
코드 복사
<template>
  <div class="pa-6 text-center" role="status" :aria-live="loading ? 'polite' : 'off'">
    <v-progress-linear v-if="loading" indeterminate class="mb-3" />
    <div v-else-if="error" class="text-error">{{ error }}</div>
    <div v-else-if="empty">{{ $t('state.empty') }}</div>
    <slot v-else />
  </div>
</template>

<script setup lang="ts">
defineProps<{ loading?: boolean; error?: string | null; empty?: boolean }>()
</script>
