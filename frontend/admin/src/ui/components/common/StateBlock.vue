<!-- ============================================================================
  File    : src/ui/components/common/StateBlock.vue
  Version : 2025.10.23 Final (HR 간소화 11차 · Empty/Error/Loading 통합)
  Purpose : Hotel Admin — 공용 상태 블록 (데이터 없음 / 로딩 / 오류 / 액션)
  ------------------------------------------------------------------------------
  목적:
    • HR·운영·리포트 등 모든 화면에서 “데이터 없음”, “로딩 중”, “오류 발생” 공통 UI 제공
    • 브랜드 톤(Primary/Muted)과 일관된 아이콘, 메시지, 버튼 사용
    • 접근성(aria-live) 및 역할(role="status") 준수
  ------------------------------------------------------------------------------
  주요 특징:
    ✅ 로딩 / 오류 / 빈 상태 3단계 상태 표시
    ✅ i18n 기반 문구(localized) 자동 노출 (state.*, msg.*)
    ✅ retry 콜백 전달 시 “다시 시도” 버튼 자동 표시
    ✅ compact / border 옵션으로 크기·테두리 조절
    ✅ slot(actions) 으로 추가 액션 버튼 삽입 가능
============================================================================ -->
<template>
  <div
    class="state-block d-flex flex-column align-center justify-center text-center"
    role="status"
    :aria-live="loading ? 'polite' : (error ? 'assertive' : 'off')"
    :class="{ compact, border }"
  >
    <!-- ───────────────────────────── 로딩 상태 ───────────────────────────── -->
    <template v-if="loading">
      <v-progress-circular
        indeterminate
        size="28"
        color="primary"
        class="mb-3"
      />
      <div class="text font-weight-medium">{{ t('state.loading') }}</div>
    </template>

    <!-- ───────────────────────────── 오류 상태 ───────────────────────────── -->
    <template v-else-if="error">
      <v-icon icon="mdi-alert-circle-outline" color="error" size="36" class="mb-2" />
      <div class="title">{{ errorTitle }}</div>
      <div class="sub">{{ errorMessage }}</div>
      <v-btn
        v-if="retry"
        variant="tonal"
        color="primary"
        prepend-icon="mdi-refresh"
        size="small"
        class="mt-3"
        @click="retry"
      >
        {{ retryText }}
      </v-btn>
    </template>

    <!-- ───────────────────────────── 빈 상태 ────────────────────────────── -->
    <template v-else>
      <v-icon :icon="icon" color="primary" size="40" class="mb-2" />
      <div class="title">{{ titleText }}</div>
      <div class="sub">{{ messageText }}</div>

      <!-- ▣ 추가 액션 슬롯 (예: “새로 등록” 버튼 등) -->
      <div v-if="$slots.actions" class="mt-3 d-flex align-center justify-center gap-2">
        <slot name="actions" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
/* ===========================================================================
   Script Logic — 상태 블록 로직 (i18n·Props·Computed)
   ---------------------------------------------------------------------------
   구성:
     • props : loading / error / title / message / icon / retry / compact / border
     • computed : i18n 텍스트/기본값 자동 처리
     • i18n : vue-i18n t() 사용 (state.*, msg.*, cta.*)
=========================================================================== */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
  loading?: boolean          // 로딩 여부
  error?: boolean            // 오류 여부
  title?: string             // 빈 상태 타이틀 (기본: state.notFound)
  message?: string           // 빈 상태 메시지 (기본: state.empty)
  icon?: string              // 빈 상태 아이콘 (기본: mdi-database-off)
  retry?: (() => void) | null// 오류 시 재시도 콜백
  retryText?: string         // “다시 시도” 버튼 텍스트
  compact?: boolean          // compact 모드 (패딩 축소)
  border?: boolean           // border 표시 여부
}>()

const { t } = useI18n()

// 표시용 계산 필드
const icon = computed(() => props.icon || 'mdi-database-off')
const titleText = computed(() => props.title || t('state.notFound'))
const messageText = computed(() => props.message || t('state.empty'))
const errorTitle = computed(() => t('state.error'))
const errorMessage = computed(() => t('msg.errorTryAgain'))
const retryText = computed(() => props.retryText || t('cta.retry'))
</script>

<style scoped>
/* ============================================================================
   Style — StateBlock 공통 스타일
   ---------------------------------------------------------------------------
   Glass Light 톤 기반 · radius/muted 컬러/transition 적용
============================================================================ */
.state-block {
  min-height: 160px;
  border-radius: var(--radius-sm);
  border: 1px dashed transparent;
  padding: 24px;
  color: var(--color-muted);
  background: linear-gradient(180deg, #fff, #fafbfc);
  transition: all .2s ease;
}
.state-block.border {
  border-color: var(--color-line);
}
.state-block.compact {
  min-height: auto;
  padding: 16px;
}
.title {
  font-weight: 700;
  font-size: 1rem;
  color: var(--color-text);
}
.sub {
  font-size: .9rem;
  color: var(--color-muted);
  margin-top: 4px;
}
.text {
  color: var(--color-text);
  font-weight: 600;
}
</style>
