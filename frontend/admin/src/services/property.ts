// ============================================================================
// File      : src/services/property.ts
// Version   : 2025.11-01 · v3.7 (SSOT Final Stable · Property API 통합판)
// Purpose   : Hotel Admin — Property(지점) 관리 서비스 (백엔드 /api/properties 호환)
// ----------------------------------------------------------------------------
// 목적
//   • 활성 지점 목록 및 전체 Property 목록 조회
//   • 로그인 페이지 지점 선택, 마감·리포트·HR 등 전역 모듈에서 재사용
// ----------------------------------------------------------------------------
// 백엔드 경로
//   • GET    /api/properties                → 전체 지점 목록 (MasterProperty 테이블)
//   • GET    /api/properties?active=1       → 활성 지점만 필터링 (optional)
//   • POST   /api/properties                → 신규 등록
//   • PUT    /api/properties/{code}         → 수정
//   • DELETE /api/properties/{code}         → 삭제
// ----------------------------------------------------------------------------
// 연동 구조
//   • http.ts  → X-Property-Code 헤더 자동 첨부
//   • Login.vue → listActive() 로 활성 지점 목록 불러오기
//   • usePropertyStore() → localStorage 동기화
// ----------------------------------------------------------------------------
// 개선사항 (v3.7)
//   ✅ /api/master/property → /api/properties 로 정식 경로 변경
//   ✅ httpEx/http 모두 호환 가능 (fetch 기반 단일 구조)
//   ✅ 타입·필드 정규화 (code, name, is_active)
//   ✅ 오류 시 fallback 로직 단순화
// ============================================================================

import http from '@/services/http'

// ─────────────────────────────────────────────
// 타입 정의
// ─────────────────────────────────────────────
export interface Property {
  code: string
  name: string
  address?: string
  is_active: boolean
  created_at?: string
}

// ─────────────────────────────────────────────
// 유틸: 빈값 제외한 쿼리스트링 빌더
// ─────────────────────────────────────────────
function buildQS(params?: Record<string, string | number | undefined>): string {
  if (!params) return ''
  const q = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && String(v) !== '') q.append(k, String(v))
  }
  const s = q.toString()
  return s ? `?${s}` : ''
}

// ─────────────────────────────────────────────
// API: 전체 지점 목록 조회
// ─────────────────────────────────────────────
export async function list(params?: { active?: number }): Promise<Property[]> {
  return await http.get(`/properties${buildQS(params)}`)
}

// ─────────────────────────────────────────────
// API: 활성 지점만 조회 (is_active=true)
// ─────────────────────────────────────────────
export async function listActive(): Promise<Property[]> {
  try {
    const all = await list()
    return all.filter(p => p.is_active)
  } catch {
    // 실패 시 Mokpo Ocean Hotel 기본값 반환 (fallback)
    return [{ code: 'MOP', name: 'Mokpo Ocean Hotel', is_active: true }]
  }
}

// ─────────────────────────────────────────────
// API: 신규 등록
// ─────────────────────────────────────────────
export async function create(data: Property) {
  return await http.post('/properties', data)
}

// ─────────────────────────────────────────────
// API: 수정 (code 기준)
// ─────────────────────────────────────────────
export async function update(code: string, data: Partial<Property>) {
  return await http.put(`/properties/${code}`, data)
}

// ─────────────────────────────────────────────
// API: 삭제
// ─────────────────────────────────────────────
export async function remove(code: string) {
  return await http.delete(`/properties/${code}`)
}

// ============================================================================
// ✅ End of File — src/services/property.ts (v2025.11-01 · SSOT Final Stable)
// ============================================================================
