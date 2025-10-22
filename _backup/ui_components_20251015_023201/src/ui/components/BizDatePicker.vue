<template>
  <div class="d-flex align-center" style="gap:8px">
    <v-text-field
      v-model="model"
      :label="mode === 'day' ? 'Business Date (YYYY-MM-DD)' : 'Month (YYYY-MM)'"
      density="comfortable" style="max-width:200px"
    />
    <v-btn variant="tonal" @click="pick">{{ mode === 'day' ? 'Pick Day' : 'Pick Month' }}</v-btn>
  </div>
</template>
<script setup lang="ts">
import { ref, watch } from 'vue'
const props = defineProps<{ modelValue:string, mode?: 'day'|'month' }>()
const emit = defineEmits<{ 'update:modelValue':[string] }>()
const mode = props.mode ?? 'day'
const model = ref(props.modelValue ?? '')
watch(()=>props.modelValue, v=> model.value = v)
watch(model, v => emit('update:modelValue', v || ''))
function pick(){
  const now = new Date()
  if (mode === 'day'){
    const v = prompt('YYYY-MM-DD', model.value || now.toISOString().slice(0,10))
    if (v) model.value = v
  } else {
    const v = prompt('YYYY-MM', model.value || now.toISOString().slice(0,7))
    if (v) model.value = v
  }
}
</script>
