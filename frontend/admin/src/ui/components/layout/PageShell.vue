<!-- ============================================================
  Hotel Admin — src/ui/layout/page-shell.vue
  Version: 2025-10-21 Fullwidth Stable (Dashboard 대응)
---------------------------------------------------------------
  목적:
    • Glass Toolbar는 유지하되 본문 영역은 전체 폭(좌우 끝까지) 사용
    • 대시보드 같은 와이드 뷰를 위한 Fullwidth Layout
=========================================================== -->
<template>
  <section class="page-shell" :class="{ fluid }">
    <!-- 헤더 -->
    <header v-if="$slots.header" class="page-header">
      <slot name="header" />
    </header>

    <!-- 툴바 (Glass SmartFilterBar 등) -->
    <div v-if="$slots.toolbar" class="page-toolbar">
      <slot name="toolbar" />
    </div>

    <!-- 본문 -->
    <main class="page-body">
      <slot />
    </main>
  </section>
</template>

<script setup lang="ts">
/**
 * Props:
 *  - fluid?: boolean → true면 전체 폭(Full Width) 모드
 *
 * Slots:
 *  - header  : 상단 헤더(PageHeader)
 *  - toolbar : SmartFilterBar 등 Glass Toolbar
 *  - default : 본문 콘텐츠
 */
defineProps<{ fluid?: boolean }>()
</script>

<style scoped>
/* ============================================================
   1. 기본 레이아웃
=========================================================== */
.page-shell {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: var(--content-max, 1280px); /* 기본 중앙 정렬 */
  margin: 0 auto;
  padding: 24px 20px;
  box-sizing: border-box;
  gap: 20px;
}

/* ============================================================
   2. 툴바 (Glass Toolbar)
   ------------------------------------------------------------
   - SmartFilterBar 전용 (Glass 스타일)
=========================================================== */
.page-toolbar {
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  box-shadow: none;
  margin: 0;
  padding: 0;
}

/* SmartFilterBar 폭 고정 — 본문 패딩(20*2) 제외 */
.page-toolbar > * {
  width: 100%;
  max-width: calc(1280px - 40px);
  margin: 0 auto;
}

/* ============================================================
   3. 본문 영역
=========================================================== */
.page-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 60vh;
}

/* ============================================================
   4. Fullwidth 모드 (fluid)
   ------------------------------------------------------------
   - 좌우 여백 최소화
   - 본문/Glass Toolbar 모두 화면 끝까지 확장
=========================================================== */
.page-shell.fluid {
  max-width: 100%;
  padding: 16px 10px; /* 상하 16, 좌우 10 여백만 남김 */
}

.page-shell.fluid .page-toolbar > * {
  max-width: 100%;
}

.page-shell.fluid .page-body {
  padding: 0; /* 본문 카드 좌우 여백 제거 */
}

@media (max-width: 1024px) {
  .page-shell.fluid {
    padding: 12px 8px;
  }
}
</style>
