// src/ui/composables/useToast.ts
// =============================================================
// useState.ts — 화면 상태 관리 (로딩/에러/성공/빈 상태)
// =============================================================
import { ref } from 'vue'
import { useToast } from '@/ui/components/common/ToastHost.vue'

export function useStateFeedback() {
  const loading = ref(false)
  const error = ref<null | string>(null)
  const empty = ref(false)

  const { success, error: errToast } = useToast()

  async function wrap<T>(fn: () => Promise<T>, msg?: { ok?: string; fail?: string }) {
    loading.value = true
    error.value = null
    try {
      const res = await fn()
      empty.value = Array.isArray((res as any)?.items) && !(res as any)?.items.length
      if (msg?.ok) success(msg.ok)
      return res
    } catch (e: any) {
      const m = e?.message || msg?.fail || '오류 발생'
      error.value = m
      errToast(m)
      throw e
    } finally {
      loading.value = false
    }
  }

  return { loading, error, empty, wrap }
}
