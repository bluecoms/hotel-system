import { ref } from 'vue'

// Confirm 상태 타입 확장
interface ConfirmState {
  msg: string
  title?: string
  okText?: string
  cancelText?: string
  resolve?: (ok: boolean) => void
}

const state = ref<ConfirmState | null>(null)

export function useConfirm() {
  function ask(
    msg: string,
    opts?: { title?: string; okText?: string; cancelText?: string }
  ): Promise<boolean> {
    return new Promise((resolve) => {
      state.value = { msg, ...opts, resolve }
    })
  }

  function decide(ok: boolean) {
    state.value?.resolve?.(ok)
    state.value = null
  }

  return { state, ask, decide }
}
