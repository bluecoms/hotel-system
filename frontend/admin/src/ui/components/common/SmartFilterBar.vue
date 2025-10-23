<!-- ============================================================================
  File    : src/ui/components/common/SmartFilterBar.vue
  Version : 2025.10.30 Final Stable (HR 간소화 10차 · Glass Harmony · 중복버튼 제거)
  Purpose : Hotel Admin — Smart Filter Bar (Glass Harmony · HR/운영 공통)
  ------------------------------------------------------------------------------
  목적:
    • HR / 운영 공통으로 사용하는 상단 검색 필터 바(Glass 톤)
    • Property 코드 동기화(localStorage + emit)
    • 검색/조회/초기화 이벤트를 통합(search / reset)
    • Glass Harmony 톤 통일(Brand Theme 기반)
  ------------------------------------------------------------------------------
  변경 요약 (v2025.10.30)
    ✅ showProperty=false 시 Property 선택 숨김 (HR 화면용)
    ✅ 검색/조회/초기화 버튼 중복 제거 (조회/초기화 1세트만)
    ✅ keyword + property 상태 emit 통합
    ✅ 스타일 유지 + 주석 보강
============================================================================ -->
<template>
  <div class="smart-filter-bar">
    <!-- ▣ 좌측 필터 그룹 -->
    <div class="filter-group">
      <!-- Property 선택 (전역 동기화) -->
      <div v-if="showProperty" class="ctl property-wrap">
        <v-select
          v-model="internalProperty"
          :items="propertyOptions"
          density="comfortable"
          variant="solo-filled"
          hide-details
          class="property-select"
          @update:model-value="onPropertyChange"
        >
          <template #prepend-inner>
            <v-icon size="18" color="primary" class="mr-1">mdi-domain</v-icon>
          </template>
        </v-select>
      </div>

      <!-- slot 확장 (부서/상태 필터 등 추가 가능) -->
      <slot name="filters">
        <!-- 기본 검색 필드 -->
        <v-text-field
          v-model="keyword"
          label="검색"
          placeholder="검색어를 입력하세요"
          variant="solo-filled"
          hide-details
          density="comfortable"
          class="input"
          @keyup.enter="emitSearch"
        />
      </slot>

      <!-- 조회 버튼 (검색 이벤트 발생) -->
      <v-btn color="primary" class="btn" rounded="md" @click="emitSearch">
        조회
      </v-btn>

      <!-- 초기화 버튼 -->
      <v-btn variant="outlined" color="grey" class="btn" @click="emitReset">
        초기화
      </v-btn>
    </div>

    <!-- ▣ 우측 확장 영역 (예: 상태칩, 기간필터 등) -->
    <div class="extra-group">
      <slot name="extra" />
    </div>
  </div>
</template>

<script setup lang="ts">
/* ===========================================================================
   Script — SmartFilterBar
   ---------------------------------------------------------------------------
   • property_code 자동 동기화(localStorage + emit)
   • 검색(search) / 초기화(reset) 이벤트 일원화
   • HR/운영 화면의 상단 필터바 표준화
=========================================================================== */
import { ref, watch, withDefaults, onMounted } from 'vue'

/** Props 정의 */
const props = withDefaults(defineProps<{
  property?: string
  propertyOptions?: string[]
  showProperty?: boolean
}>(), {
  showProperty: true,
})

/** Emits 정의 */
const emit = defineEmits(['search', 'reset', 'update:property'])

/* 내부 상태 */
const internalProperty = ref(props.property || '')
const keyword = ref('')

/* Property prop 외부 변경 감시 */
watch(() => props.property, v => (internalProperty.value = v || ''))

/* 초기 로드 시 전역 property 동기화(localStorage) */
onMounted(() => {
  if (!internalProperty.value) {
    internalProperty.value =
      localStorage.getItem('property_code') ||
      import.meta.env.VITE_DEFAULT_PROPERTY_CODE ||
      'MOP'
  }
})

/** Property 변경 시 localStorage와 emit 모두 업데이트 */
function onPropertyChange(v: string) {
  localStorage.setItem('property_code', v)
  emit('update:property', v)
}

/** 검색/조회 이벤트 (엔터키 또는 버튼 클릭 시) */
function emitSearch() {
  emit('search', {
    property: internalProperty.value,
    keyword: keyword.value,
  })
}

/** 초기화 이벤트 */
function emitReset() {
  keyword.value = ''
  emit('reset')
}
</script>

<style scoped>
/* ===========================================================================
   Style — SmartFilterBar (Glass Harmony Ver.)
   ---------------------------------------------------------------------------
   • 브랜드 톤 기반 반투명 Glass 효과
   • 필터/버튼/추가영역 정렬 및 반응형 대응
=========================================================================== */
.smart-filter-bar {
  display: grid;
  grid-template-columns: 1fr auto; /* 좌측 유동, 우측 고정 */
  align-items: center;
  gap: 14px;

  /* Glass 톤 플로팅 */
  background: rgba(255, 255, 255, 0.85);
  border-radius: 20px;
  backdrop-filter: blur(10px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);

  padding: 16px 22px;
  transition: all 0.3s ease;
}
.smart-filter-bar:hover {
  box-shadow: 0 10px 28px rgba(37, 99, 235, 0.15);
  transform: translateY(-2px);
}

/* 좌측 그룹 */
.filter-group {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px 12px;
}

/* 우측 그룹 */
.extra-group {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px 12px;
}

/* Property Select Glass 톤 */
.property-wrap {
  display: flex;
  align-items: center;
}
.property-select :deep(.v-field) {
  background: rgba(255, 255, 255, 0.55);
  border-radius: 12px;
  box-shadow: inset 0 0 0 1px rgba(59, 130, 246, 0.15);
  transition: all 0.25s ease;
}
.property-select :deep(.v-field:hover) {
  background: rgba(255, 255, 255, 0.75);
  box-shadow: inset 0 0 0 1px rgba(59, 130, 246, 0.3);
}
.property-select :deep(.v-field__input) {
  font-weight: 600;
  color: var(--v-theme-primary);
}

/* 버튼 */
.btn {
  height: 40px;
  min-width: 88px;
  font-weight: 600;
  font-size: 0.9rem;
  border-radius: 10px;
  transition: all 0.2s ease;
}
.btn:hover {
  box-shadow: 0 3px 8px rgba(37, 99, 235, 0.18);
  transform: translateY(-1px);
}

/* 반응형 대응 */
@media (max-width: 1024px) {
  .smart-filter-bar {
    grid-template-columns: 1fr;
    padding: 14px 16px;
  }
  .extra-group {
    justify-content: center;
  }
}
@media (max-width: 640px) {
  .filter-group {
    justify-content: center;
  }
  .property-select,
  .input {
    width: 100%;
  }
  .btn {
    width: 100%;
  }
}
</style>
