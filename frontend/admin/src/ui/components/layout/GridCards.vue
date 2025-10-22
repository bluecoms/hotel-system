<!-- ============================================================================
  File    : src/ui/components/layout/GridCards.vue
  Version : 2025.10 Final Stable (Phase3 SSOT UI)
  Purpose : DatasetCard 등의 카드들을 반응형 2열 그리드로 배치하는 래퍼
  ------------------------------------------------------------------------------
  특징:
    ✅ 반복되는 카드 레이아웃을 통일
    ✅ 최소 360px 단위로 auto-fit, 1~N열 반응형 배치
    ✅ 내부에 slot만 렌더링 (로직 없음)
  ------------------------------------------------------------------------------
  Slots:
    • default → 그리드 배치할 카드들(DatasetCard 등)
============================================================================ -->

<template>
  <div class="d-grid">
    <slot />
  </div>
</template>

<script setup lang="ts">
// slot-only wrapper
</script>

<style scoped>
.d-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: 16px;
}
</style>
