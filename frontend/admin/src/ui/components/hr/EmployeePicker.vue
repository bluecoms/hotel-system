<!-- ============================================================================
  File      : src/ui/components/hr/EmployeePicker.vue
  Version   : 2025.10-24 Final Stable (Property-Safe + Reactive Emit)
  Purpose   : Hotel Admin — 직원 선택 컴포넌트 (검색형 콤보박스)
  ------------------------------------------------------------------------------
  목적:
    • 계약/기록/급여 등에서 직원(employee) 선택용 자동완성 필드 제공
    • property_code(지점코드) 자동 주입 — 현재 선택된 지점 기준으로만 검색
  ------------------------------------------------------------------------------
  주요 개선사항 (v2025.10-24)
    ✅ usePropertyStore 연동 (초기 undefined 방지)
    ✅ onMounted + nextTick으로 전역 store 초기화 시점 보장
    ✅ 직원 선택 시 즉시 selected emit (부모 컨텍스트 자동 갱신)
    ✅ 검색/다이얼로그 재열림 시 데이터 즉시 새로고침
  ------------------------------------------------------------------------------
  연계 API:
    • GET /api/employees?property_code=MOP&q=...&status=active
============================================================================ -->
<template>
  <v-autocomplete
    v-model="innerValue"
    :items="items"
    :loading="loading"
    :label="label"
    :placeholder="placeholder"
    variant="outlined"
    density="comfortable"
    clearable
    hide-details="auto"
    :item-title="itemTitle"
    :item-value="itemValue"
    :return-object="false"
    :menu-props="{ maxHeight: 360 }"
    @update:search="onSearch"
  >
    <!-- ▣ 항목 표시 템플릿 -->
    <template #item="{ props, item }">
      <v-list-item v-bind="props">
        <template #title>
          <div class="d-flex align-center">
            <span class="font-weight-medium mr-2">{{ item.raw.name }}</span>
            <span class="text-caption text-grey-darken-1">({{ item.raw.emp_no }})</span>
          </div>
        </template>
        <template #subtitle>
          <div class="text-caption text-grey-darken-1">
            {{ item.raw.dept_name || item.raw.dept || '-' }} /
            {{ item.raw.title_name || item.raw.title || '-' }}
            <span v-if="item.raw.email"> · {{ item.raw.email }}</span>
          </div>
        </template>
      </v-list-item>
    </template>
  </v-autocomplete>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from 'vue'
import * as EmployeesApi from '@/services/employees'
import { usePropertyStore } from '@/stores/property'

/* ===========================================================================
   Props / Emits
=========================================================================== */
const props = withDefaults(defineProps<{
  modelValue: number | null
  onlyActive?: boolean
  label?: string
  placeholder?: string
}>(), {
  modelValue: null,
  onlyActive: true,
  label: '직원 선택',
  placeholder: '이름 / 사번 / 부서 / 직책 / 이메일로 검색',
})

const emit = defineEmits<{
  (e: 'update:modelValue', v: number | null): void
  (e: 'selected', row: any | null): void
}>()

/* ===========================================================================
   상태 정의
=========================================================================== */
const innerValue = ref<number | null>(props.modelValue)
const items = ref<any[]>([])
const loading = ref(false)
const q = ref('')
const property = usePropertyStore()
const propertyCode = ref('MOP') // ✅ 초기 기본값 (store 초기화 전 안전)

/* ===========================================================================
   데이터 로드 함수
=========================================================================== */
async function fetch(query = '') {
  if (!propertyCode.value) return
  loading.value = true
  try {
    const res = await EmployeesApi.list({
      page: 1,
      size: 20,
      q: query || undefined,
      status: props.onlyActive ? 'active' : undefined,
      property_code: propertyCode.value,
      sort: 'name:asc',
    })
    items.value = res.items || []
    const sel = items.value.find(r => Number(r?.id) === Number(innerValue.value)) || null
    emit('selected', sel)
  } catch (err) {
    console.error('[EmployeePicker.fetch]', err)
  } finally {
    loading.value = false
  }
}

/* ===========================================================================
   Mount 시점 — property store 초기화 보장
=========================================================================== */
onMounted(async () => {
  await nextTick()
  // ✅ store 초기화 시점 보장
  propertyCode.value =
    property.current ||
    localStorage.getItem('property_code') ||
    import.meta.env.VITE_DEFAULT_PROPERTY_CODE ||
    'MOP'

  // 초기 로드
  await fetch()
})

/* ===========================================================================
   검색 입력 핸들러
=========================================================================== */
function onSearch(v: string) {
  q.value = v || ''
  fetch(q.value)
}

/* ===========================================================================
   선택 시 부모 emit (핵심)
=========================================================================== */
watch(innerValue, v => {
  emit('update:modelValue', v)
  const sel = items.value.find(r => Number(r?.id) === Number(v)) || null
  emit('selected', sel)
})

/* ===========================================================================
   표시 포맷터
=========================================================================== */
const itemTitle = (r: any) =>
  `${r?.name || ''} (${r?.emp_no || ''}) — ${(r?.dept_name || r?.dept || '-')}/${(r?.title_name || r?.title || '-')}`
const itemValue = (r: any) => Number(r?.id ?? 0)
</script>

<style scoped>
.v-autocomplete {
  width: 100%;
}
</style>
