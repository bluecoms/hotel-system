// ============================================================================
// File      : src/stores/property.ts
// Version   : 2025.11-01 · v3.6 (Auth Integration + Header Sync Final)
// Purpose   : Hotel Admin — Property(지점) 전역 상태 스토어
// ----------------------------------------------------------------------------
// 목적:
//   • 로그인 시 선택된 지점(property_code)을 전역으로 관리 및 주입
//   • 모든 API 요청 헤더(X-Property-Code)에 자동 반영(http.ts 내부)
//   • Auth 로그인/로그아웃 루틴과 완전 연동
// ----------------------------------------------------------------------------
// 주요 개선(v3.6):
//   ✅ AuthStore 로그인/로그아웃 시 자동 동기화 (set / clear)
//   ✅ http 및 httpEx 양쪽 호환 (헤더 자동 반영)
//   ✅ 앱 부팅 시(localStorage → state) 복원 로직 안정화
// ----------------------------------------------------------------------------
// 사용 예시:
//   import { usePropertyStore } from '@/stores/property'
//   const property = usePropertyStore()
//   property.init()             // 앱 부팅 시 복원
//   property.set('MOP')         // 지점 선택/변경
//   property.clear()            // 로그아웃 시 초기화
// ----------------------------------------------------------------------------
// 주의:
//   • 지점코드는 항상 대문자(예: MOP, BUS, SEO)로 관리
//   • localStorage 키: 'property_code'
//   • 지점 값 변경 시 fetch 요청은 다음 요청부터 자동 헤더 적용
// ============================================================================

import { defineStore } from 'pinia'

export const usePropertyStore = defineStore('property', {
  // ─────────────────────────────────────────────
  // 상태 정의
  // ─────────────────────────────────────────────
  state: () => ({
    /** 현재 선택된 지점코드 (기본값 'MOP') */
    current: localStorage.getItem('property_code') || 'MOP',
  }),

  // ─────────────────────────────────────────────
  // Getter (읽기 전용)
  // ─────────────────────────────────────────────
  getters: {
    /** 현재 지점코드 읽기 */
    get: (state) => () => state.current,
  },

  // ─────────────────────────────────────────────
  // Actions (설정 / 복원 / 초기화)
  // ─────────────────────────────────────────────
  actions: {
    /**
     * ✅ 지점코드 설정 및 스토리지 / 헤더 동기화
     * @param code 예: 'MOP' / 'BUS' / 'SEO'
     */
    set(code: string) {
      const val = (code || 'MOP').trim().toUpperCase()
      this.current = val
      try {
        localStorage.setItem('property_code', val)
      } catch (e) {
        console.warn('[PropertyStore] localStorage set failed:', e)
      }
    },

    /**
     * ✅ 앱 부팅 시 localStorage → state 복원
     *  - AuthStore.bootstrap() 또는 main.ts 초기화 단계에서 호출
     */
    init() {
      try {
        const saved = localStorage.getItem('property_code')
        if (saved) this.current = saved
        else {
          this.current = 'MOP'
          localStorage.setItem('property_code', 'MOP')
        }
      } catch (e) {
        console.warn('[PropertyStore] init failed:', e)
      }
    },

    /**
     * ✅ 로그아웃 또는 세션 만료 시 초기화
     *  - AuthStore.handle401() 또는 logout() 호출 시 사용
     */
    clear() {
      this.current = 'MOP'
      try {
        localStorage.removeItem('property_code')
      } catch (e) {
        console.warn('[PropertyStore] clear failed:', e)
      }
    },
  },
})

// ============================================================================
// End of File — src/stores/property.ts
// ============================================================================
