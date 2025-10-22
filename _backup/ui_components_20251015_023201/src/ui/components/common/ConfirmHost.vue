<template>
  <v-dialog v-model="open" max-width="420">
    <v-card>
      <v-card-title class="font-weight-bold text-h6">
        {{ state?.title || '확인' }}
      </v-card-title>
      <v-card-text>{{ state?.msg }}</v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="decide(false)">취소</v-btn>
        <v-btn color="primary" variant="flat" @click="decide(true)">확인</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useConfirm } from '@/ui/composables/useConfirm'
const { state, decide } = useConfirm()
const open = computed(() => !!state.value)
</script>

<style scoped>
.v-card-text {
  white-space: pre-line;
}
</style>
