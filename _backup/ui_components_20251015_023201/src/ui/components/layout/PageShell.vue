<template>
  <section class="page-shell">
    <!-- 헤더 -->
    <header class="page-header">
      <div class="page-title">
        <!-- 아이콘 슬롯 (있을 경우만) -->
        <slot name="icon">
          <v-icon
            v-if="icon"
            :icon="icon"
            size="20"
            class="mr-1 text-medium-emphasis"
          />
        </slot>
        <h1>{{ title }}</h1>
      </div>

      <!-- 우측 액션 영역 -->
      <div class="page-actions">
        <slot name="actions" />
      </div>
    </header>

    <!-- 선택적 툴바 -->
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
defineProps<{ title: string; icon?: string }>()
</script>

<style scoped>
/* 전체 래퍼: 중앙 정렬 + 여백 */
.page-shell {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  max-width: var(--content-max, 1280px);
  margin: 0 auto;
  padding: 24px 20px;
  box-sizing: border-box;
}

/* 헤더 */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* 타이틀 */
.page-title {
  display: flex;
  align-items: center;
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--color-text, var(--text));
  gap: 6px;
  position: relative;
  padding-bottom: 0.3rem;
}

/* 밑줄 (옛 버전 호환) */
.page-title::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: 0;
  width: 72px;
  height: 3px;
  background: linear-gradient(
    90deg,
    var(--brand-accent),
    var(--brand-secondary)
  );
  border-radius: 3px;
}

/* 툴바 영역 */
.page-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  padding: 8px 0;
  border-bottom: 1px solid var(--color-line);
}

/* 본문 */
.page-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 60vh;
}
</style>
