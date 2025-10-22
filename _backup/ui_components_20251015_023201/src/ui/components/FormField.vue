<template>
  <div class="form-field">
    <label v-if="label" class="label">
      {{ label }}
      <span v-if="required" class="req">*</span>
    </label>

    <component
      :is="component"
      v-bind="inputProps"
      v-model="model"
      density="comfortable"
      variant="outlined"
      hide-details
      :error="!!error"
      :messages="error ? [error] : []"
    />

    <div v-if="hint && !error" class="hint">{{ hint }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  modelValue: any
  label?: string
  hint?: string
  required?: boolean
  error?: string
  type?: string
  component?: any
}>()
const emit = defineEmits<{ 'update:modelValue': [any] }>()

const model = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const inputProps = computed(() => ({
  type: props.type || 'text',
}))
</script>

<style scoped>
.form-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
}
.label {
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--color-text);
  margin-bottom: 2px;
}
.req { color: var(--color-error); margin-left: 4px; }
.hint {
  font-size: 0.8rem;
  color: var(--color-muted);
  margin-top: 2px;
}
</style>
