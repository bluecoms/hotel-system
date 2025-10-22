# /ui/components/common/BoardViewDialog.vue
<template>
  <v-dialog v-model="open" max-width="640">
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon v-if="icon" :icon="icon" size="18" class="mr-2" />
        <span class="text-h6">{{ title }}</span>
      </v-card-title>

      <v-divider />

      <v-card-text>
        <slot name="content" :item="item" />
      </v-card-text>

      <v-divider />

      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="close">닫기</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  modelValue: boolean
  title: string
  icon?: string
  item?: Record<string, any>
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const open = computed({
  get: () => props.modelValue,
  set: (v: boolean) => emit('update:modelValue', v),
})

function close() {
  emit('update:modelValue', false)
}
</script>

<style scoped>
.v-card-text {
  min-height: 120px;
}
</style>
