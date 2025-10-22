// src/utils/toastError.ts
import { useToast } from '@/ui/composables/useToast'

export function toastError(e: any, fallback = '오류가 발생했습니다') {
  const { error } = useToast()
  const detail =
    e?.response?.data?.detail ??
    e?.detail ??
    e?.message ??
    (Array.isArray(e?.response?.data) && e.response.data[0]?.msg) ??
    fallback
  error(String(detail))
}
