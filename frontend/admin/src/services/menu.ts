// ============================================================================
// File      : src/services/menu.ts
// Version   : 1.2 Final (2025-11-05 · SSOT Stable · Safe Normalize)
// Purpose   : Hotel Admin — Sidebar/Menu API Service (권한 기반 메뉴 트리)
// ----------------------------------------------------------------------------
// 목적:
//   • /api/menu 호출로 메뉴 트리 구조 로드.
//   • roles 기반 접근제한 및 sidebar 렌더링 데이터 제공.
// ----------------------------------------------------------------------------
// 주요 개선 (v1.2):
//   ✅ { items: [...] } / [...] 응답 모두 자동 정규화
//   ✅ 요청 실패 시 [] 반환 (화면 안정성 보장)
//   ✅ 주석 및 타입 정의를 SSOT 규격(auth/master와 통일)
// ----------------------------------------------------------------------------
// 연동 백엔드:
//   • GET /api/menu → [{ id, label, path, roles, children }]
// ============================================================================

import http from '@/services/http'

// ----------------------------------------------------------------------------
//  타입 정의
// ----------------------------------------------------------------------------
export type MenuItem = {
  /** 고유 ID (또는 routeName) */
  id?: string
  /** 메뉴 표시명 */
  label: string
  /** 실제 경로 (/dashboard 등) */
  path?: string
  /** Vue Router 'to' (path 동일) */
  to?: string
  /** 하위 메뉴 */
  children?: MenuItem[]
  /** 접근 권한 (roles 배열, 예: ['ADMIN','SUPERADMIN']) */
  roles?: string[]
}

// ----------------------------------------------------------------------------
//  메뉴 로드 API
// ----------------------------------------------------------------------------
/**
 * /api/menu 호출 — 백엔드 응답 정규화
 * @returns MenuItem[] — 계층형 메뉴 목록
 */
export async function getMenu(): Promise<MenuItem[]> {
  try {
    const res = await http.get<MenuItem[] | { items: MenuItem[] }>('menu')
    // ✅ { items: [...] } 형태 → items 로 변환
    if (Array.isArray(res)) return res
    if (Array.isArray((res as any)?.items)) return (res as any).items
    return []
  } catch (err) {
    console.error('[menu.getMenu] failed:', err)
    return []
  }
}

// ============================================================================
// ✅ EOF — src/services/menu.ts (v1.2 Final · SSOT 안정판)
// ============================================================================
