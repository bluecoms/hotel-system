<template>
  <v-sheet
    class="no-data-box d-flex flex-column align-center justify-center text-center"
    color="transparent"
    :elevation="0"
  >
    <div class="icon-wrap">
      <v-icon :icon="icon" size="40" class="mb-2" />
    </div>
    <div class="title">{{ titleText }}</div>
    <div v-if="messageText" class="message">{{ messageText }}</div>

    <div class="mt-3 d-flex align-center gap-2">
      <slot name="actions">
        <v-btn
          v-if="retry"
          variant="tonal"
          color="primary"
          prepend-icon="mdi-refresh"
          @click="retry"
        >
          {{ retryText }}
        </v-btn>
      </slot>
    </div>
  </v-sheet>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
  title?: string
  message?: string
  icon?: string
  retry?: (() => void) | null
  retryText?: string
}>()

const { t } = useI18n()

const icon = computed(() => props.icon || 'mdi-database-off')
const titleText = computed(() => props.title || t('state.notFound'))
const messageText = computed(() => props.message || t('state.empty'))
const retryText = computed(() => props.retryText || t('cta.refresh'))
</script>

<style scoped>
.no-data-box {
  min-height: 180px;
  border: 1px dashed var(--color-line);
  border-radius: var(--radius-sm);
  background: linear-gradient(180deg, #ffffff, #fbfbfd);
  padding: 24px;
}
.icon-wrap {
  display: grid;
  place-items: center;
  width: 56px; height: 56px;
  border-radius: 14px;
  background: #f3f6fb;
  color: var(--brand-secondary);
  margin-bottom: 6px;
}
.title {
  font-weight: 700;
  font-size: 1.05rem;
  color: var(--color-text);
}
.message {
  margin-top: 4px;
  font-size: .92rem;
  color: var(--color-muted);
}
</style>
