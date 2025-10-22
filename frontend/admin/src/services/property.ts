// ============================================================================
// File    : src/services/property.ts
// Version : 2025.10-22 v1.0 (Stable / Property Master Service)
// Purpose : Hotel Admin — Property(지점) 관리 API
// ----------------------------------------------------------------------------
// 목적
//   • 전체 Property(호텔/지점) 목록 및 활성 지점 조회
//   • 상단바 드롭다운, 보고서, 마감, HR 등 전역 모듈에서 사용
//
// 백엔드 경로
//   • GET    /api/master/property           → 목록 조회
//   • POST   /api/master/property           → 신규 생성
//   • PUT    /api/master/property/{code}    → 수정
//   • DELETE /api/master/property/{code}    → 삭제
// ============================================================================

import http from '@/services/http'

/** Property(지점) 기본 구조 */
export interface Property {
  code: string
  name: string
  is_active: boolean
}

/** 전체 지점 목록 조회 */
export async function list(): Promise<Property[]> {
  return await http.get('master/property')
}

/** 활성 지점만 조회 (is_active=true) */
export async function listActive(): Promise<Property[]> {
  const all = await list()
  return all.filter(p => p.is_active)
}

/** 지점 생성 */
export async function create(data: Property) {
  return await http.post('master/property', data)
}

/** 지점 수정 */
export async function update(code: string, data: Partial<Property>) {
  return await http.put(`master/property/${code}`, data)
}

/** 지점 삭제 */
export async function remove(code: string) {
  return await http.delete(`master/property/${code}`)
}

// ============================================================================
// ✅ EOF — Property Master Service (v2025.10-22)
// ============================================================================
