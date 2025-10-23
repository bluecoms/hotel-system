<!-- ============================================================================
  File      : src/ui/components/hr/EmployeePicker.vue
  Version   : 2.0 Final (2025-10-23 · HR 간소화 8차 · Property AutoSync + ActiveFilter)
  Purpose   : Hotel Admin — 직원 선택 컴포넌트 (검색형 콤보박스)
  ------------------------------------------------------------------------------
  변경 요약 (v2.0)
    ✅ property_code 자동 반영 (MOP 기본값 + localStorage + store 연동)
    ✅ onlyActive 옵션 → status 필터(active) 자동 적용
    ✅ 한글화 출력 (사번 / 이름 / 부서 / 직책 / 상태)
    ✅ 검색(q) 입력 시 즉시 fetch (EmployeesApi.list 기반)
    ✅ 선택 시 @selected(row) emit 구조 통일
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
            <span v-if="item.raw.contract_status" class="ml-1">
              · {{ statusLabel(item.raw.contract_status) }}
            </span>
          </div>
        </template>
      </v-list-item>
    </template>
  </v-autocomplete>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from 'vue'
import * as EmployeesApi from '@/services/employees'

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
  placeholder: '이름 / 사번 / 부서 / 직책 검색',
})

const emit = defineEmits<{
  (e: 'update:modelValue', v: number | null): void
  (e: 'selected', row: any | null): void
}>()

/* ===========================================================================
   상태
=========================================================================== */
const innerValue = ref<number | null>(props.modelValue)
const items = ref<any[]>([])
const loading = ref(false)
const q = ref('')
const propertyCode =
  localStorage.getItem('property_code') ||
  import.meta.env.VITE_DEFAULT_PROPERTY_CODE ||
  'MOP'

/* ===========================================================================
   데이터 로드
=========================================================================== */
async function fetch(query = '') {
  loading.value = true
  try {
    const res = await EmployeesApi.list({
      page: 1,
      size: 20,
      q: query || undefined,
      status: props.onlyActive ? 'active' : undefined,
      property_code: propertyCode,
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
   검색 핸들러
=========================================================================== */
function onSearch(v: string) {
  q.value = v || ''
  fetch(q.value)
}

/* ===========================================================================
   선택 시 부모 emit
=========================================================================== */
watch(innerValue, v => {
  emit('update:modelValue', v)
  const sel = items.value.find(r => Number(r?.id) === Number(v)) || null
  emit('selected', sel)
})

/* ===========================================================================
   상태 라벨 (한글화)
=========================================================================== */
function statusLabel(s?: string) {
  const v = (s || '').toLowerCase()
  if (v === 'active') return '계약중'
  if (v === 'terminated') return '만료'
  if (v === 'none') return '미계약'
  return ''
}

/* ===========================================================================
   Mount 시 초기 로드
=========================================================================== */
onMounted(async () => {
  await nextTick()
  await fetch()
})

/* ===========================================================================
   표시 포맷
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
