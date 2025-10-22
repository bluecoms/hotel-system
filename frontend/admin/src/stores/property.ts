// ============================================================================
// File      : src/stores/property.ts
// Version   : 2025.10 Final Stable
// Purpose   : Hotel Admin — Property(지점) 전역 상태 스토어
// ----------------------------------------------------------------------------
// 목적:
//   • 로그인 시 선택된 지점(property_code)을 전역으로 관리
//   • 모든 API 요청(http.ts)과 화면 표시(대시보드/HR/리포트 등)에 통일 반영
// ----------------------------------------------------------------------------
// 설계 원칙:
//   • Pinia 기반 상태관리 (Vue 3 Composition API 호환)
//   • localStorage 연동 (브라우저 새로고침 후에도 유지)
//   • 읽기 전용 getter + 명시적 setter(set) 패턴
// ----------------------------------------------------------------------------
// 사용 예시:
//   import { usePropertyStore } from '@/stores/property'
//   const property = usePropertyStore()
//   console.log(property.current)         // 현재 지점 코드
//   property.set('MOP')                   // 지점 변경
//   property.get()                        // getter (동일 기능)
// ----------------------------------------------------------------------------
// 주의사항:
//   • 로그인 시 1회 선택된 값을 저장하며, 이후 모든 fetch 요청의 헤더에
//     X-Property-Code 로 자동 포함됨(http.ts 내부에서 처리).
//   • 선택형 드롭다운은 사용하지 않으며, 상단 바에서 표시만 함.
// ============================================================================

import { defineStore } from 'pinia'

export const usePropertyStore = defineStore('property', {
  // ─────────────────────────────────────────────
  // 상태 정의
  // ─────────────────────────────────────────────
  state: () => ({
    current: localStorage.getItem('property_code') || 'MOP', // 기본값: Mokpo Ocean Hotel
  }),

  // ─────────────────────────────────────────────
  // Getter (읽기 전용 접근)
  // ─────────────────────────────────────────────
  getters: {
    get: (state) => () => state.current,
  },

  // ─────────────────────────────────────────────
  // Actions (갱신 / 초기화)
  // ─────────────────────────────────────────────
  actions: {
    /** 지점코드 설정 및 localStorage 동기화 */
    set(code: string) {
      this.current = code.trim().toUpperCase()
      localStorage.setItem('property_code', this.current)
    },

    /** localStorage → state 초기화 (앱 부팅 시) */
    init() {
      const saved = localStorage.getItem('property_code')
      if (saved) this.current = saved
    },

    /** 상태 초기화 (로그아웃 시 호출) */
    clear() {
      this.current = 'MOP'
      localStorage.removeItem('property_code')
    },
  },
})
