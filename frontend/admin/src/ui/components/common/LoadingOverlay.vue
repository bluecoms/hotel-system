<!-- ============================================================================
  File    : src/ui/components/common/LoadingOverlay.vue
  Version : 2.0 Final (2025-10-23 · HR 간소화 12차 · Glass Overlay)
  Purpose : Hotel Admin — 공용 로딩 오버레이 (Glass 톤 반투명 + 중앙 인디케이터)
  ------------------------------------------------------------------------------
  목적:
    • 테이블/폼/다이얼로그 등 로딩 중 상태를 Glass 톤 반투명 오버레이로 표시
    • HR, Closing, Upload 등 전역에서 공용 사용
    • show(boolean) prop 하나로 표시/비표시 제어 (transition 포함)
  ------------------------------------------------------------------------------
  주요 특징:
    ✅ Glass 반투명 톤 + Blur 효과 적용
    ✅ ProgressCircular 중앙 정렬
    ✅ slot 지원 (예: “처리중…” 텍스트)
    ✅ radius 상속 + z-index 상단 고정
============================================================================ -->
<template>
  <transition name="fade">
    <div
      v-if="show"
      class="overlay d-flex flex-column align-center justify-center text-center"
      role="alert"
      aria-live="polite"
    >
      <v-progress-circular
        indeterminate
        color="primary"
        size="32"
        width="3"
      />
      <div v-if="$slots.default" class="mt-2 text-body-2 text-primary font-weight-medium">
        <slot />
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
/* ===========================================================================
   Props — show(boolean) : 표시 여부
=========================================================================== */
defineProps<{ show: boolean }>()
</script>

<style scoped>
/* ============================================================================
   Style — Glass Overlay / 중앙 정렬 / Fade Transition
============================================================================ */
.overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.55);
  backdrop-filter: blur(6px);
  border-radius: inherit;
  z-index: 10;
  transition: all 0.25s ease;
}

/* Fade 효과 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
