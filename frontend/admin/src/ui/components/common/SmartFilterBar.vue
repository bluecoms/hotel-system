<!-- ============================================================
 Hotel Admin — SmartFilterBar (v2025.10.22 Glass Harmony Ver.)
---------------------------------------------------------------
 목적:
   • Glass 톤 + 플로팅 입체감의 상단 툴바 (KPI 카드 톤 통일)
   • Property Select / BizDatePicker / Actions의 일관성 확보
   • 중복 기능 버튼(‘새로고침’ vs ‘Refresh’) 통합
=========================================================== -->
<template>
  <div class="smart-filter-bar">
    <!-- ▣ 좌측: Property + 날짜 + 조회 -->
    <div class="filter-group">
      <!-- Property -->
      <div v-if="showProperty" class="ctl property-wrap">
        <v-select
          v-model="internalProperty"
          :items="propertyOptions"
          density="comfortable"
          variant="solo-filled"
          hide-details
          class="property-select"
          @update:model-value="$emit('update:property', $event)"
        >
          <template #prepend-inner>
            <v-icon size="18" color="primary" class="mr-1">mdi-domain</v-icon>
          </template>
        </v-select>
      </div>

      <!-- 날짜 (slot로 교체 가능) -->
      <slot name="filters">
        <v-text-field
          v-model="search"
          type="date"
          label="Business Date"
          variant="solo-filled"
          hide-details
          density="comfortable"
          class="input"
          @keyup.enter="emitSearch"
        />
      </slot>

      <!-- 조회 버튼 -->
      <v-btn color="primary" class="btn" rounded="md" @click="emitSearch">
        조회
      </v-btn>
    </div>

    <!-- ▣ 우측: 확장 slot (예: 상태칩 / 진행률 / Refresh 등) -->
    <div class="extra-group">
      <slot name="extra" />
    </div>
  </div>
</template>

<script setup lang="ts">
/* ============================================================
   SmartFilterBar Script — Reactive State / Events
=========================================================== */
import { ref, watch, withDefaults } from 'vue'

const props = withDefaults(defineProps<{
  property?: string
  propertyOptions?: string[]
  from?: string
  to?: string
  showProperty?: boolean
}>(), {
  showProperty: true,
})

const emit = defineEmits(['search', 'reset', 'update:property'])

const search = ref('')
const internalProperty = ref(props.property || '')

watch(() => props.property, v => (internalProperty.value = v || ''))

function emitSearch() {
  emit('search', {
    property: internalProperty.value,
    keyword: search.value,
  })
}
</script>

<style scoped>
/* ============================================================
   SmartFilterBar — Glass Floating Unified Style
   ------------------------------------------------------------
   Glass 톤, 둥근 radius, soft shadow, 반응형 지원
=========================================================== */
.smart-filter-bar {
  display: grid;
  grid-template-columns: 1fr auto; /* 좌측 유동, 우측 내용 */
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

/* Responsive */
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
