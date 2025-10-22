# /ui/components/common/BoardFormDialog.vue
<template>
  <v-dialog v-model="open" max-width="600" persistent>
    <v-card>
      <v-card-title>
        <v-icon :icon="icon" size="18" class="mr-2" />
        <span>{{ title }}</span>
      </v-card-title>

      <v-card-text>
        <v-form ref="form" v-model="valid" lazy-validation>
          <slot name="form" :model="model" :errors="errors" />
        </v-form>
      </v-card-text>

      <v-divider />

      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="cancel">취소</v-btn>
        <v-btn color="primary" :loading="saving" @click="submit">저장</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'

const props = defineProps<{
  modelValue: boolean
  title: string
  icon?: string
  initial?: Record<string, any>
}>()
const emit = defineEmits(['update:modelValue', 'submit', 'cancel'])

const open = ref(props.modelValue)
const valid = ref(false)
const form = ref()
const saving = ref(false)
const model = reactive({ ...(props.initial ?? {}) })
const errors = reactive<Record<string, string>>({})

function cancel() {
  emit('cancel')
  emit('update:modelValue', false)
}

async function submit() {
  saving.value = true
  try {
    emit('submit', model)
    emit('update:modelValue', false)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.v-card-title {
  display: flex;
  align-items: center;
  font-weight: 700;
}
</style>
