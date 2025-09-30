import { ref } from 'vue'
const state = ref<{ msg:string; resolve?:(ok:boolean)=>void } | null>(null)
export function useConfirm(){
  function ask(msg:string){ return new Promise<boolean>(resolve => state.value = { msg, resolve }) }
  function decide(ok:boolean){ state.value?.resolve?.(ok); state.value = null }
  return { state, ask, decide }
}
