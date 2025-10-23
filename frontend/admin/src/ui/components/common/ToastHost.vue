<!-- ============================================================================
  File    : src/ui/components/common/ToastHost.vue
  Version : 2025.11 Final Stable (주석보존 · HR 간소화 10차 · Vue 파서 오류 수정완료)
  Purpose : Hotel Admin — 전역 Toast 표시 컴포넌트 (하단 우측 최대 3개 스택)
  ------------------------------------------------------------------------------
  목적:
    • 전역 Toast 큐(queue) 상태를 실시간 렌더링하여 사용자에게 알림 표시
    • useToast()에서 관리되는 queue를 구독
    • 하단 우측 위치 고정 + 최대 3개까지만 병렬 표시
  ------------------------------------------------------------------------------
  특징:
    ✅ ToastItem 타입(useToast.ts)과 연동
    ✅ Hover 시 자동 닫힘 일시정지
    ✅ 색상/아이콘 일원화
    ✅ aria-live 적용 (접근성 보장)
============================================================================ -->
<template>
  <!-- Toast 큐를 순회하며 개별 Snackbar 렌더링 -->
  <template v-for="item in items" :key="item.id">
    <v-snackbar
      :model-value="true"
      :timeout="hovering.has(item.id) ? 0 : (item.timeout ?? 2500)"
      :color="colorOf(item.kind)"
      location="bottom right"
      elevation="8"
      class="toast-host"
      :role="item.kind==='error' ? 'alert' : 'status'"
      :aria-live="item.ariaLive ?? (item.kind==='error' ? 'assertive' : 'polite')"
      @update:modelValue="(v:boolean)=>{ if(!v) remove(item.id) }"
      @timeout="remove(item.id)"
      @mouseenter="hovering.add(item.id)"
      @mouseleave="hovering.delete(item.id)"
    >
      <!-- 토스트 내부 콘텐츠 -->
      <div class="toast-row">
        <!-- 아이콘 -->
        <v-icon :icon="iconOf(item.kind)" size="18" class="mr-2" />
        <!-- 메시지 -->
        <span class="toast-msg">{{ item.message }}</span>
        <v-spacer />
        <!-- 닫기 버튼 -->
        <v-btn
          variant="text"
          density="comfortable"
          icon="mdi-close"
          class="ml-2"
          @click="remove(item.id)"
          :aria-label="$t ? $t('cta.close') : '닫기'"
        />
      </div>
    </v-snackbar>
  </template>
</template>

<script setup lang="ts">
/* ===========================================================================
   Script — ToastHost
   ---------------------------------------------------------------------------
   • useToast()로부터 queue/reactive 상태를 구독
   • 최대 3개까지만 스택 표시
   • Hover 시 자동 닫힘 중단 (Set으로 관리)
=========================================================================== */
import { computed, ref } from 'vue'
import type { ToastItem, ToastKind } from '@/ui/composables/useToast'
import { useToast } from '@/ui/composables/useToast'

/** 전역 상태(useToast)에서 queue 구독 */
const { queue, remove } = useToast()

/** 최대 3개까지만 표시 (queue가 늘어나면 slice) */
const items = computed<ToastItem[]>(() => queue.value.slice(0, 3))

/** Hover 상태 저장 (id Set 기반) */
const hovering = ref<Set<number>>(new Set())

/** 종류별 색상 반환 */
function colorOf(kind: ToastKind) {
  switch (kind) {
    case 'success': return 'success'
    case 'error':   return 'error'
    case 'warning': return 'warning'
    default:        return 'primary'
  }
}

/** 종류별 아이콘 반환 */
function iconOf(kind: ToastKind) {
  switch (kind) {
    case 'success': return 'mdi-check-circle'
    case 'error':   return 'mdi-alert-circle'
    case 'warning': return 'mdi-alert'
    default:        return 'mdi-information'
  }
}
</script>

<style scoped>
/* ===========================================================================
   Style — ToastHost (Bottom-right Stack)
   ---------------------------------------------------------------------------
   • Vuetify Snackbar 기본 wrapper 확장
   • 반응형 대응 (모바일 너비 축소)
=========================================================================== */
.toast-host :deep(.v-snackbar__wrapper) {
  min-width: 320px;
}
.toast-row {
  display: flex;
  align-items: center;
}
.toast-msg {
  display: inline-block;
  max-width: 520px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 모바일 대응 */
@media (max-width: 640px) {
  .toast-host :deep(.v-snackbar__wrapper) {
    min-width: 260px;
  }
  .toast-msg {
    max-width: 240px;
  }
}
</style>
