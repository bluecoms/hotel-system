import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'

// 대상 컴포넌트
import SalesTags from '../SalesTags.vue'

// http 모듈 default(mock)
vi.mock('@/services/http', () => {
  return {
    default: {
      get: vi.fn(),
    },
  }
})

import http from '@/services/http' // <-- 위 mock의 타입 사용

describe('SalesTags.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('성공: 표에 데이터 렌더링', async () => {
    ;(http.get as any).mockResolvedValueOnce([
      { tag: 'RoomOnly', sales_amount: 12345.67, count: 12 },
      { tag: 'Breakfast', sales_amount: 9876.5, count: 7 },
    ])

    const wrapper = mount(SalesTags)
    await flushPromises()

    // 에러 알림은 없어야 함
    expect(wrapper.find('[role="alert"]').exists()).toBe(false)

    // 데이터 테이블 본문 텍스트 확인(간단 체크)
    const text = wrapper.text()
    expect(text).toContain('RoomOnly')
    expect(text).toContain('Breakfast')
    expect(text).toContain('12345.67')
    expect(text).toContain('7')
  })

  it('실패: 에러 알림 표시', async () => {
    ;(http.get as any).mockRejectedValueOnce(new Error('boom'))

    const wrapper = mount(SalesTags)
    await flushPromises()

    // Vuetify v-alert가 role="alert"를 가짐(테마에 따라 다르면 텍스트로 체크)
    const alert = wrapper.find('[role="alert"]')
    // role 탐지 안되면 아래로 대체:
    // const alert = wrapper.find('.v-alert') 
    expect(alert.exists()).toBe(true)
    expect(wrapper.text()).toContain('Failed to load sales tags')
  })
})
