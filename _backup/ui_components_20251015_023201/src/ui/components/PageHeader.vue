<template>
  <header class="page-header mb-4">
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

        <slot name="sub" />
      </div>
    </div>

    <div class="rhs">
      <slot name="actions" />
    </div>
  </header>
</template>

<script setup lang="ts">
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

/* ✅ 제목 밑에 브랜드 블루 강조선 */
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

/* ✅ 액션 버튼 영역 */
.rhs {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-self: end;
}

/* 모바일에서 자동 줄바꿈 대응 */
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
