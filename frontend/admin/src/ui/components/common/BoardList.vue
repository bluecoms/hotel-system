<template>
  <v-card class="board-list" flat>
    <!-- Header -->
    <div class="board-head">
      <div class="board-head-lhs">
        <v-icon v-if="icon" :icon="icon" size="18" class="mr-1 text-medium-emphasis" />
        <h3 class="board-title">{{ title }}</h3>
        <v-chip v-if="badge" size="x-small" variant="tonal">{{ badge }}</v-chip>
      </div>
      <div class="board-head-rhs">
        <slot name="actions" />
      </div>
    </div>

    <!-- Filters -->
    <div v-if="$slots.filters" class="board-filters">
      <slot name="filters" />
    </div>

    <!-- Data Table -->
    <v-data-table
      :headers="headers"
      :items="items"
      :loading="loadingProxy"
      :items-per-page="itemsPerPage"
      v-model:page="pageProxy"
      v-model:sort-by="sortProxy"
      density="comfortable"
      hover
      fixed-header
      class="board-table"
      :no-data-text="t('state.empty')"
      :loading-text="t('state.loading')"
      @click:row="onRowClick"
      @update:items-per-page="onUpdateItemsPerPage"
      @update:sort-by="onUpdateSort"
    >
      <!-- Custom cell slots (각 컬럼 key별로 그대로 전달) -->
      <template v-for="h in headers" v-slot:[`item.${h.key}`]="scope">
        <slot :name="`cell.${h.key}`" v-bind="scope" />
      </template>

      <!-- Pagination -->
      <template #bottom>
        <v-pagination
          v-model="pageProxy"
          :length="pages"
          :total-visible="7"
          class="board-pagination"
          active-color="primary"
        />
      </template>

      <!-- No Data -->
      <template #no-data>
        <slot name="no-data">
          <StateBlock :loading="loadingProxy" />
        </slot>
      </template>
    </v-data-table>

    <!-- Loading overlay -->
    <LoadingOverlay :show="loadingProxy" />
  </v-card>
</template>

<script setup lang="ts">
/* =============================================================================
   Hotel Admin — Unified Board List (공용 리스트 셸)
   변경 내역(안전 보강):
     • prop: rowClickable(boolean, default true) 추가
       - 행 클릭을 막고 싶을 때(셀 내부에서 버튼/메뉴 사용 시) 유용
       - 기존 화면 영향 없음: 내부 onRowClick에서 early-return 처리
   나머지 기능/슬롯/동작은 기존 유지 (정렬, 페이지, 로딩 등)
============================================================================= */

import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import StateBlock from '@/ui/components/common/StateBlock.vue'
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
  /** 권장: perPage, 호환: size */
  perPage?: number
  size?: number
  /** 외부 제어용 현재 페이지(선택) */
  page?: number
  /** 외부 제어용 정렬(선택) — Vuetify 표준 형태 [{ key, order }] */
  sortBy?: Array<{ key: string; order: 'asc' | 'desc' }>
  /** 로딩 플래그 */
  loading?: boolean
  /** 행 클릭 이벤트 허용 여부 (기본 true) — 버튼 클릭시 행클릭을 막고 싶을 때 false */
  rowClickable?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:page', v: number): void
  (e: 'update:items-per-page', v: number): void
  (e: 'update:sort-by', v: Array<{ key: string; order: 'asc' | 'desc' }>): void
  (e: 'row-click', row: any): void
}>()

const { t } = useI18n()

// 페이지 프록시
const pageProxy = ref<number>(props.page ?? 1)
watch(() => props.page, (v) => {
  if (typeof v === 'number' && v !== pageProxy.value) pageProxy.value = v
})
watch(pageProxy, (v) => emit('update:page', v))

// 페이지당 개수 프록시
const itemsPerPage = ref<number>(props.perPage ?? props.size ?? 10)
watch(() => props.perPage ?? props.size, (v) => {
  const next = typeof v === 'number' ? v : 10
  if (next !== itemsPerPage.value) itemsPerPage.value = next
})

// 정렬 프록시(양방향)
const sortProxy = ref<Array<{ key: string; order: 'asc' | 'desc' }>>(props.sortBy ?? [])
watch(() => props.sortBy, (v) => {
  if (Array.isArray(v)) sortProxy.value = v
})
function onUpdateSort(v: Array<{ key: string; order: 'asc' | 'desc' }>) {
  emit('update:sort-by', v)
}

const loadingProxy = computed(() => props.loading ?? false)
const pages = computed(() => {
  const total = props.total ?? props.items.length
  return Math.max(1, Math.ceil(total / itemsPerPage.value))
})

/** 행 클릭 — rowClickable=false면 무시(슬롯 내 버튼 클릭 시 동작 충돌 방지) */
function onRowClick(row: any) {
  if (props.rowClickable === false) return
  const payload = (row && row.item) ? row.item : row
  emit('row-click', payload)
}

function onUpdateItemsPerPage(v: number) {
  if (typeof v === 'number') {
    itemsPerPage.value = v
    emit('update:items-per-page', v)
  }
}
</script>

<style scoped>
/* ============================================================
   Hotel Admin — Unified Board List Style (Light Only)
============================================================ */
.board-list {
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-line);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
  padding: var(--space-4);
  position: relative;
}
.board-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--space-3); }
.board-head-lhs { display: flex; align-items: center; gap: var(--space-2); }
.board-head-rhs { display: flex; align-items: center; gap: var(--space-2); }
.board-title { font-size: 1.05rem; font-weight: 700; color: var(--color-text); }
.board-filters { margin-bottom: var(--space-3); }
.board-table { border-radius: var(--radius-xs); font-size: 0.9rem; background: var(--color-surface); }
.board-pagination { padding: var(--space-3) 0; justify-content: center; }
@media (max-width: 768px) {
  .board-list { padding: var(--space-3); }
  .board-title { font-size: 1rem; }
}
</style>
