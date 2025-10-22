<!-- ===========================================================
  Hotel Admin — src/ui/components/layout/PageHeader.vue
  Version: 2025-10-17 Stable v3.1
  -------------------------------------------------------------
  목적:
    • 페이지별 상단 타이틀/아이콘/부제목/Breadcrumbs 표시
    • page-shell.vue의 <slot name="header"> 내부에서 사용
    • CSS Scoped → page-shell과 클래스명 중복되어도 안전

  구성:
    <header.page-header>
      <div.lhs>  → 아이콘 + 타이틀 + 부제 + Breadcrumbs
      <div.rhs>  → 액션 버튼 슬롯

  변경 내역 (2025-10-17)
    ✅ Breadcrumbs density="compact" 통일
    ✅ 모바일 대응 (1단 레이아웃 자동 전환)
    ✅ flex-wrap 추가로 액션 버튼 줄바꿈 허용

  주의:
    - 이 컴포넌트는 레이아웃이 아니라 “내용”용.
      page-shell.vue와 함께 써야 완성된 구조.
=========================================================== -->

<template>
  <header class="page-header mb-4">
    <!-- 좌측: 아이콘 + 타이틀 + 서브 -->
    <div class="lhs">
      <v-icon
        v-if="icon"
        :icon="icon"
        color="primary"
        size="24"
        class="mr-1"
      />
      <div class="titles">
        <h2 class="page-title">{{ title }}</h2>

        <p v-if="subtitle" class="page-subtitle">{{ subtitle }}</p>

        <v-breadcrumbs
          v-if="breadcrumbs?.length"
          :items="breadcrumbs"
          class="page-breadcrumbs"
          density="compact"
        />

        <!-- 커스텀 서브 슬롯 -->
        <slot name="sub" />
      </div>
    </div>

    <!-- 우측: 액션 버튼 슬롯 -->
    <div class="rhs">
      <slot name="actions" />
    </div>
  </header>
</template>

<script setup lang="ts">
/**
 * Props:
 *  - title: 메인 타이틀
 *  - subtitle?: 부제목
 *  - icon?: MDI 아이콘명 (예: mdi-calendar)
 *  - breadcrumbs?: Breadcrumb 아이템 배열
 * 
 * Slots:
 *  - sub      : 타이틀 아래 추가 요소 (ex. 필터 or 태그)
 *  - actions  : 우측 액션 버튼
 */
defineProps<{
  title: string
  subtitle?: string
  icon?: string
  breadcrumbs?: Array<{ text: string; href?: string; disabled?: boolean }>
}>()
</script>

<style scoped>
/* ────────────────────────────────
   Page Header — Unified Light Style
   (Hotel Admin 2025 Neutral Blue)
────────────────────────────────── */
.page-header {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: flex-start;
  gap: 16px;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--color-line);
}

.lhs {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  min-width: 0;
}

.titles {
  min-width: 0;
}

/* ✅ 제목 스타일 통일 */
.page-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text);
  line-height: 1.25;
  position: relative;
  padding-bottom: 4px;
}

/* ✅ 브랜드 블루 밑줄 */
.page-title::after {
  content: "";
  position: absolute;
  left: 0;
  bottom: 0;
  width: 64px;
  height: 3px;
  border-radius: 3px;
  background: linear-gradient(90deg, #60A5FA, #2563EB);
}

/* ✅ 부제목 */
.page-subtitle {
  margin: 0.25rem 0 0;
  font-size: 0.9rem;
  color: var(--color-muted);
}

/* ✅ Breadcrumbs */
.page-breadcrumbs {
  margin-top: 0.4rem;
  padding: 0;
  font-size: 0.85rem;
  opacity: 0.9;
}

/* ✅ 우측 액션 버튼 영역 */
.rhs {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-self: end;
}

/* ✅ 모바일 대응 */
@media (max-width: 768px) {
  .page-header {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  .rhs {
    justify-content: flex-start;
  }
}
</style>
