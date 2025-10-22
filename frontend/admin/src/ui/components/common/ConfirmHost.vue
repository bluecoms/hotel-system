# /ui/components/common/ConfirmHost.vue
<template>
  <v-dialog v-model="open" max-width="420">
    <v-card>
      <v-card-title>Confirm</v-card-title>
      <v-card-text>{{ state?.msg }}</v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="decide(false)">Cancel</v-btn>
        <v-btn color="primary" @click="decide(true)">OK</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { useConfirm } from '@/ui/composables/useConfirm'
const { state, decide } = useConfirm()
const open = computed(()=> !!state.value)
</script>
