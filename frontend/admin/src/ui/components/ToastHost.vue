<template>
  <v-snackbar v-model="open" :timeout="cur?.timeout ?? 2500" location="bottom right" @update:modelValue="onClose">
    {{ cur?.text }}
  </v-snackbar>
</template>
<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useToast } from '@/ui/composables/useToast'
const { queue, shift } = useToast()
const cur = computed(()=> queue.value[0])
const open = ref(false)
watch(cur, v => open.value = !!v)
function onClose(v:boolean){ if(!v) shift() }
</script>
