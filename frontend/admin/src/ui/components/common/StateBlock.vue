# /ui/components/common/StateBlock.vue.vue
<template>
  <div
    class="state-block d-flex flex-column align-center justify-center text-center"
    role="status"
    :aria-live="loading ? 'polite' : (error ? 'assertive' : 'off')"
    :class="{ compact, border }"
  >
    <!-- ✅ 로딩 -->
    <template v-if="loading">
      <v-progress-circular indeterminate size="28" color="primary" class="mb-3" />
      <div class="text font-weight-medium">{{ t('state.loading') }}</div>
    </template>

    <!-- ✅ 에러 -->
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

    <!-- ✅ 빈 상태 -->
    <template v-else>
      <v-icon :icon="icon" color="primary" size="40" class="mb-2" />
      <div class="title">{{ titleText }}</div>
      <div class="sub">{{ messageText }}</div>

      <div v-if="$slots.actions" class="mt-3 d-flex align-center justify-center gap-2">
        <slot name="actions" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
  loading?: boolean
  error?: boolean
  title?: string
  message?: string
  icon?: string
  retry?: (() => void) | null
  retryText?: string
  compact?: boolean
  border?: boolean
}>()

const { t } = useI18n()

const icon = computed(() => props.icon || 'mdi-database-off')
const titleText = computed(() => props.title || t('state.notFound'))
const messageText = computed(() => props.message || t('state.empty'))
const errorTitle = computed(() => t('state.error'))
const errorMessage = computed(() => t('msg.errorTryAgain'))
const retryText = computed(() => props.retryText || t('cta.retry'))
</script>

<style scoped>
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
