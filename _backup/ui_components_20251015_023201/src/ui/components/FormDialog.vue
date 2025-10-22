<template>
  <v-dialog v-model="openLocal" max-width="640">
    <v-card>
      <v-card-title class="d-flex align-center justify-space-between">
        <div class="d-flex align-center gap-2">
          <v-icon v-if="icon" :icon="icon" />
          <span>{{ title }}</span>
        </div>
        <v-btn icon="mdi-close" variant="text" @click="close" />
      </v-card-title>

      <v-divider />

      <v-card-text>
        <slot />
      </v-card-text>

      <v-divider />

      <v-card-actions class="justify-end">
        <v-btn variant="text" @click="close">{{ cancelText }}</v-btn>
        <v-btn color="primary" :loading="loading" @click="onSubmit">
          {{ okText }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  open: boolean
  title: string
  icon?: string
  okText?: string
  cancelText?: string
  loading?: boolean
}>()
const emit = defineEmits<{ (e: 'update:open', v: boolean): void; (e: 'submit'): void }>()

const openLocal = ref(props.open)
watch(() => props.open, v => openLocal.value = v)

function close() {
  openLocal.value = false
  emit('update:open', false)
}

function onSubmit() {
  emit('submit')
}
</script>

