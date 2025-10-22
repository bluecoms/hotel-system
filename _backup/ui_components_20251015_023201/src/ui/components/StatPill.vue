<template>
  <v-chip :color="color" variant="tonal" size="small" class="font-weight-600">
    <slot />
  </v-chip>
</template>
<script setup lang="ts">
withDefaults(defineProps<{ color?: string }>(), { color: 'secondary' })
</script>


