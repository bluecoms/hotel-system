// =============================================================
// useForm.ts — 입력/검증/저장 통합 훅 (2025 통합 버전)
// =============================================================
import { ref } from 'vue'
import { useToast } from '@/ui/composables/useToast'
import { useConfirm } from '@/ui/composables/useConfirm'

export function useForm<T extends object>(initial: T) {
  const model = ref({ ...initial })
  const loading = ref(false)
  const errors = ref<Record<string, string>>({})

  const { success, error: errToast } = useToast()
  const { ask } = useConfirm()

  function reset() {
    model.value = { ...initial }
    errors.value = {}
  }

  function validate(rules: Record<keyof T, (v: any) => string | null>) {
    const errs: Record<string, string> = {}
    for (const k in rules) {
      const msg = rules[k](model.value[k])
      if (msg) errs[k] = msg
    }
    errors.value = errs
    return Object.keys(errs).length === 0
  }

  async function submit(
    fn: (payload: T) => Promise<any>,
    opts?: { confirmMsg?: string; okMsg?: string; failMsg?: string }
  ) {
    if (opts?.confirmMsg && !(await ask(opts.confirmMsg))) return
    loading.value = true
    try {
      await fn(model.value)
      success(opts?.okMsg || '저장 완료')
      return true
    } catch (e: any) {
      errToast(opts?.failMsg || e?.message || '저장 실패')
      return false
    } finally {
      loading.value = false
    }
  }

  return { model, loading, errors, reset, validate, submit }
}
