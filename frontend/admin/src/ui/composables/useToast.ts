import { ref } from 'vue'
export type Toast = { text:string; timeout?:number }
const queue = ref<Toast[]>([])
export function useToast() {
  function show(text:string, timeout=2500) { queue.value.push({ text, timeout }) }
  function shift(){ queue.value.shift() }
  return { queue, show, shift }
}
