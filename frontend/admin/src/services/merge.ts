// src/services/merge.ts
// ===============================================================
// Hotel Admin — Merge Engine API (2025 Unified Fetch Version)
// ---------------------------------------------------------------
//  • 공통 인증: X-Internal-Token 헤더 (http.ts 내부에서 자동 추가)
//  • axios / session / cookie 사용 금지
//  • fetch 기반 http.ts 클라이언트 사용
//  • dataset / property_code / order / limit 표준 파라미터 지원
// ===============================================================

import http from '@/services/http'

/**
 * 병합 배치 목록 조회
 * @param params { dataset?, property_code?, order?, limit? }
 * @returns Promise<any[]>
 */
export async function getMergeBatches(params?: Record<string, any>) {
  // ✅ RequestInit에 'params' 속성이 없으므로 URLSearchParams로 직접 처리
  const query = params
    ? '?' + new URLSearchParams(
        Object.entries(params).filter(([_, v]) => v != null)
      ).toString()
    : ''
  return await http.get(`/merge/batches${query}`)
}

/**
 * 특정 배치의 로그 조회
 * @param batchId 배치 ID
 * @returns Promise<{ changes: any[] }>
 */
export async function getMergeLogs(batchId: number) {
  return await http.get(`/merge/logs/${batchId}`)
}
