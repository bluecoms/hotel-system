<template>
  <div class="smart-filter-bar">
    <slot name="filters">
      <v-text-field
        v-model="search"
        :label="t('cta.search')"
        prepend-inner-icon="mdi-magnify"
        hide-details
        clearable
        density="comfortable"
        class="ctl min-w-220"
        @keyup.enter="emitSearch"
      />
      <v-btn color="primary" class="btn-action" @click="emitSearch">{{ t('cta.search') }}</v-btn>
      <v-btn variant="outlined" color="grey" class="btn-action" @click="emitReset">{{ t('cta.refresh') }}</v-btn>
    </slot>

    <slot />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const search = ref('')
const emit = defineEmits(['search', 'reset'])

function emitSearch() {
  emit('search', search.value)
}
function emitReset() {
  search.value = ''
  emit('reset')
}
</script>

<style scoped>
.smart-filter-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  background: rgb(var(--v-theme-surface));
  border: 1px solid var(--color-line, rgba(0,0,0,0.08));
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(16, 24, 40, 0.06);
  padding: 10px 12px;
  min-height: 60px; /* 통일 높이 */
}

/* 입력 필드와 버튼 높이 정렬 */
.ctl :deep(.v-field),
.btn-action {
  height: 40px !important;
}
.ctl :deep(.v-field__input) {
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  height: 40px !important;
  line-height: 40px !important;
}
.btn-action {
  font-weight: 600;
  min-width: 90px;
  height: 40px;
}

/* 반응형 */
@media (max-width: 960px) {
  .smart-filter-bar {
    gap: 8px;
    padding: 8px 10px;
  }
}
</style>
