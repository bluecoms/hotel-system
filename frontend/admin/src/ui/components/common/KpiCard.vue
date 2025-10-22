<!-- ============================================================
 Hotel Admin — KpiCard Component (v2025.10 Stable / Final FIX)
---------------------------------------------------------------
 위치: src/ui/components/common/KpiCard.vue

 목적:
   • KPI(지표) 카드 단위 컴포넌트
   • Dashboard 등에서 Room Only, Package, Other, Total 등을 표시할 때 사용
   • 단일 숫자 + 제목 + 통화기호(₩ 등) 표시

 props:
   - title: string          → 카드 제목
   - value: number | null   → KPI 값
   - prefix?: string        → 접두 기호 (예: '₩')
   - suffix?: string        → 접미 기호 (예: '%')
   - color?: string         → Vuetify 색상 (기본 'primary')
   - loading?: boolean      → 로딩 상태일 경우 skeleton 표시

 사용 예시:
   <KpiCard title="Room Only" :value="12345678" prefix="₩" />
--------------------------------------------------------------- -->
<template>
  <v-card class="kpi-card" elevation="1">
    <v-card-text class="kpi-content">
      <!-- 제목 -->
      <div class="kpi-title text-caption text-grey-darken-1">
        {{ props.title }}
      </div>

      <!-- 로딩 중일 때 Skeleton -->
      <div v-if="props.loading" class="skeleton-line"></div>

      <!-- 실제 값 -->
      <div
        v-else
        class="kpi-value font-weight-medium"
        :class="{ 'text-grey': props.value === null || props.value === 0 }"
      >
        <span v-if="props.prefix" class="prefix">{{ props.prefix }}</span>
        {{ formatted }}
        <span v-if="props.suffix" class="suffix">{{ props.suffix }}</span>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'

/**
 * ✅ Props 정의 — defineProps()는 단 한 번만 선언
 * 타입 정의와 props 변수 선언을 동시에 처리
 */
const props = defineProps<{
  title: string
  value?: number | null
  prefix?: string
  suffix?: string
  color?: string
  loading?: boolean
}>()

/**
 * ✅ 통화 형식 변환 (세 자리마다 콤마)
 * - 값이 null, undefined, NaN이면 대시(—) 표시
 * - 숫자일 경우 toLocaleString()으로 포맷
 */
const formatted = computed(() => {
  if (props.value === null || props.value === undefined || isNaN(props.value))
    return '—'
  return Number(props.value).toLocaleString()
})
</script>

<style scoped>
/* ===========================================================
   KpiCard 스타일 — Hotel Admin v2025.10 Blue Neutral Theme
=========================================================== */

/* 카드 기본 레이아웃 */
.kpi-card {
  border-radius: 12px;
  border: 1px solid var(--surface-3, #e5e7eb);
  background: var(--surface-1, #fff);
  min-height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

/* hover 효과 */
.kpi-card:hover {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

/* 카드 내용 정렬 */
.kpi-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 16px;
}

/* 제목 스타일 */
.kpi-title {
  font-size: 0.85rem;
  font-weight: 500;
  margin-bottom: 4px;
}

/* 값 스타일 */
.kpi-value {
  font-size: 1.25rem;
  color: var(--color-text, #111);
}

/* 접두/접미 기호 */
.prefix,
.suffix {
  opacity: 0.8;
  font-size: 0.9em;
}

/* Skeleton (로딩 상태 시 표시) */
.skeleton-line {
  width: 60%;
  height: 18px;
  border-radius: 6px;
  background: linear-gradient(90deg, #e5e7eb 25%, #f3f4f6 50%, #e5e7eb 75%);
  background-size: 200% 100%;
  animation: shimmer 1.2s infinite;
}

/* Skeleton 애니메이션 */
@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}
</style>
