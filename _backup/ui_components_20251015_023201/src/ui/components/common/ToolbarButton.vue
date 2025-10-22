<template>
  <v-btn
    :color="color"
    :variant="variant"
    :prepend-icon="icon"
    size="small"
    class="font-weight-600"
    v-bind="$attrs"
  >
    <slot />
  </v-btn>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  icon?: string
  color?: string
  variant?: 'flat' | 'tonal' | 'text' | 'outlined'
}>(), {
  color: 'primary',
  variant: 'flat',
})
</script>
