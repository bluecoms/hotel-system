// src/services/health.ts
import http from '@/services/http'

/** 백엔드 헬스체크 응답 타입 */
export type Healthz = {
  ok: boolean
  service: string
  env: 'dev' | 'prod' | 'staging' | string
  commit?: string
  ts?: string
}

/** 헬스 상태 조회 */
export async function getHealth(): Promise<Healthz> {
  try {
    const res = await http.get<Healthz>('/api/healthz')
    if (!res?.ok) throw new Error('서버 응답 실패')
    return res
  } catch (err) {
    return { ok: false, service: 'backend', env: 'unknown' }
  }
}
