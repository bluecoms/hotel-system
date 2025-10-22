<!-- ============================================================================
  File    : src/ui/components/board/BoardList.vue
  Version : 2025.11 Final (Title 기본값 · RowClickable · 주석 정리)
  Purpose : Hotel Admin — 공용 보드 리스트 셸(테이블/필터/액션/페이지네이션)
  ------------------------------------------------------------------------------
  변경 요약
    • title 기본값 '' 부여 → 페이지에서 title 누락 시 Vue 경고 제거
    • rowClickable(boolean, default true) 도큐먼트/주석 정리
    • 코드 전반 주석 깔끔화(각 섹션 목적/이벤트/동작 명시)

  사용 예시
    <BoardList
      title="사용자 목록"
      :headers="headers"
      :items="items"
      :total="total"
      :page="page"
      :per-page="20"
      :loading="loading"
      @update:page="v => page = v"
      @update:items-per-page="v => perPage = v"
      @update:sort-by="sort = v"
      @row-click="onRowClick"
    >
      <template #filters> ... </template>
      <template #actions> ... </template>
      <template #cell.email="{ item }"> {{ item.email }} </template>
    </BoardList>
============================================================================ -->

<template>
  <v-card class="board-list" flat>
    <!-- ───────────────────────── 헤더(타이틀/배지/액션) ───────────────────────── -->
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

    <!-- ──────────────────────────────── 필터 영역 ─────────────────────────────── -->
    <div v-if="$slots.filters" class="board-filters">
      <slot name="filters" />
    </div>

    <!-- ───────────────────────────── 데이터 테이블 ────────────────────────────── -->
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
      <!-- 각 컬럼 key에 대응하는 커스텀 셀 슬롯을 그대로 전달 -->
      <template v-for="h in headers" v-slot:[`item.${h.key}`]="scope">
        <slot :name="`cell.${h.key}`" v-bind="scope" />
      </template>

      <!-- 페이지네이션(테이블 하단) -->
      <template #bottom>
        <v-pagination
          v-model="pageProxy"
          :length="pages"
          :total-visible="7"
          class="board-pagination"
          active-color="primary"
        />
      </template>

      <!-- 데이터 없음 UI(슬롯 미지정 시 공통 StateBlock 사용) -->
      <template #no-data>
        <slot name="no-data">
          <StateBlock :loading="loadingProxy" />
        </slot>
      </template>
    </v-data-table>

    <!-- 로딩 오버레이(테이블 위) -->
    <LoadingOverlay :show="loadingProxy" />
  </v-card>
</template>

<script setup lang="ts">
/* =============================================================================
   Hotel Admin — Unified Board List (공용 리스트 셸)
   목적
     • 일관된 목록 화면 레이아웃(헤더/필터/테이블/페이징)을 제공
     • 슬롯 기반으로 유연한 확장(필터/액션/셀 커스텀)

   특징/주의
     • title prop에 기본값 ''을 부여 → 페이지에서 누락해도 경고 없음(UX/로그 청결)
     • rowClickable=false 시 행 클릭 이벤트 차단(셀 내부 버튼과 충돌 방지)
     • perPage ↔ size 모두 지원(후방 호환), 내부 itemsPerPage로 통합
============================================================================= */

import { ref, computed, watch, withDefaults } from 'vue'
import { useI18n } from 'vue-i18n'
import StateBlock from '@/ui/components/common/StateBlock.vue'
import LoadingOverlay from '@/ui/components/common/LoadingOverlay.vue'

/** Vuetify 데이터테이블 헤더 타입(필수: title, key) */
export interface BoardHeader {
  title: string
  key: string
  align?: 'start' | 'center' | 'end'
  sortable?: boolean
  width?: string | number
}

/**
 * props 정의
 *  - title       : 상단 제목(기본값 '' → 경고 제거)
 *  - icon/badge  : 타이틀 좌측 아이콘/우측 배지
 *  - headers     : 테이블 헤더(필수)
 *  - items       : 테이블 데이터
 *  - total       : 총 개수(없으면 items.length 사용)
 *  - perPage/size: 페이지당 개수 입력(둘 중 하나 사용; perPage 권장)
 *  - page        : 외부 제어 페이지(양방향)
 *  - sortBy      : 정렬 상태(양방향; [{key,order}])
 *  - loading     : 로딩 플래그
 *  - rowClickable: 행 클릭 허용 여부(기본 true)
 */
const props = withDefaults(defineProps<{
  title?: string
  icon?: string
  badge?: string
  headers: BoardHeader[]
  items: any[]
  total?: number
  perPage?: number
  size?: number
  page?: number
  sortBy?: Array<{ key: string; order: 'asc' | 'desc' }>
  loading?: boolean
  rowClickable?: boolean
}>(), {
  title: '',          // ✅ 기본값: 경고 제거
  rowClickable: true, // ✅ 기본값: 행 클릭 허용
})

/**
 * 이벤트
 *  - update:page           : 페이지 변경(양방향)
 *  - update:items-per-page : 페이지당 개수 변경
 *  - update:sort-by        : 정렬 변경(양방향)
 *  - row-click             : 행 클릭(행 전체 객체 전달)
 */
const emit = defineEmits<{
  (e: 'update:page', v: number): void
  (e: 'update:items-per-page', v: number): void
  (e: 'update:sort-by', v: Array<{ key: string; order: 'asc' | 'desc' }>): void
  (e: 'row-click', row: any): void
}>()

const { t } = useI18n()

// ───────────────────────── 내부 상태 프록시(양방향 동기화) ─────────────────────────

// 페이지 프록시 (외부 page ↔ 내부 pageProxy)
const pageProxy = ref<number>(props.page ?? 1)
watch(() => props.page, (v) => {
  if (typeof v === 'number' && v !== pageProxy.value) pageProxy.value = v
})
watch(pageProxy, (v) => emit('update:page', v))

// 페이지당 개수 프록시 (perPage 우선, 없으면 size, 기본 10)
const itemsPerPage = ref<number>(props.perPage ?? props.size ?? 10)
watch(() => props.perPage ?? props.size, (v) => {
  const next = typeof v === 'number' ? v : 10
  if (next !== itemsPerPage.value) itemsPerPage.value = next
})

// 정렬 프록시 (외부 sortBy ↔ 내부 sortProxy)
const sortProxy = ref<Array<{ key: string; order: 'asc' | 'desc' }>>(props.sortBy ?? [])
watch(() => props.sortBy, (v) => { if (Array.isArray(v)) sortProxy.value = v })
function onUpdateSort(v: Array<{ key: string; order: 'asc' | 'desc' }>) {
  emit('update:sort-by', v)
}

// 로딩/총 페이지 계산
const loadingProxy = computed(() => props.loading ?? false)
const pages = computed(() => {
  const total = props.total ?? props.items.length
  return Math.max(1, Math.ceil(total / itemsPerPage.value))
})

// ─────────────────────────────── 이벤트 핸들러 ────────────────────────────────

/** 행 클릭 — rowClickable=false면 무시(슬롯 버튼/메뉴와 충돌 방지) */
function onRowClick(row: any) {
  if (props.rowClickable === false) return
  const payload = (row && row.item) ? row.item : row
  emit('row-click', payload)
}

/** 페이지당 개수 변경(테이블 하단 셀렉터/페이징과 연동) */
function onUpdateItemsPerPage(v: number) {
  if (typeof v === 'number') {
    itemsPerPage.value = v
    emit('update:items-per-page', v)
  }
}
</script>

<style scoped>
/* ============================================================================
   Hotel Admin — Unified Board List Style (Light-only)
   - 브랜드 토큰 사용: --color-*, --radius-*, --space-*, --shadow-*
============================================================================ */
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
