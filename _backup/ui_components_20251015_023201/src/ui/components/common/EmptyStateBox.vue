<template>
  <div class="empty-box" :class="{ border, compact }" role="status" :aria-live="ariaLive">
    <template v-if="loading">
      <v-progress-circular indeterminate size="28" color="primary" class="mb-3" />
      <div class="text">{{ loadingText }}</div>
    </template>

    <template v-else-if="error">
      <v-icon icon="mdi-alert-circle-outline" color="error" size="36" class="mb-2" />
      <div class="title">{{ errorText }}</div>
      <div class="sub">{{ errorSub }}</div>
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

    <template v-else>
      <v-icon :icon="icon" color="primary" size="40" class="mb-2" />
      <div class="title">{{ titleText }}</div>
      <div class="sub">{{ messageText }}</div>

      <div class="actions mt-3">
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
  retry?: (() => void) | null
  retryText?: string
  icon?: string
  border?: boolean
  compact?: boolean
}>()

const { t } = useI18n()

const ariaLive = computed(() => (props.loading ? 'polite' : props.error ? 'assertive' : 'off'))
const icon = computed(() => props.icon || 'mdi-database-off')

const titleText = computed(() => props.title || t('state.notFound'))
const messageText = computed(() => props.message || t('state.empty'))

const loadingText = computed(() => t('state.loading'))
const errorText = computed(() => t('state.error'))
const errorSub = computed(() => t('msg.errorTryAgain'))
const retryText = computed(() => props.retryText || t('cta.retry'))
</script>

<style scoped>
.empty-box {
  min-height: 160px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 24px;
  color: var(--color-muted);
  background: linear-gradient(180deg, #fff, #fafbfc);
  border-radius: var(--radius);
  transition: all .2s ease;
}
.empty-box.border { border: 1px dashed var(--color-line); }
.empty-box.compact { min-height: auto; padding: 16px; }

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
.text { color: var(--color-text); font-weight: 600; }
.actions { display: flex; align-items: center; justify-content: center; gap: 8px; }
</style>
