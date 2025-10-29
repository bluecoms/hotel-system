<!-- ============================================================================
# File      : src/ui/components/hr/EmployeePicker.vue
# Version   : 2.1 (2025-11-10 · SSOT Final · UX Polish)
# Purpose   : 직원 선택 콤보박스 (검색형 + Property 자동 동기화)
# ----------------------------------------------------------------------------
# 기능 요약:
#   • 검색어 입력 시 실시간 조회 (/api/employees)
#   • onlyActive=true → status=active 자동 필터링
#   • property_code 자동 주입 (localStorage / VITE_DEFAULT)
#   • 한글 라벨: 계약상태(계약중/만료/미계약)
#   • 선택 시 @selected(row) / v-model 동기화
# ----------------------------------------------------------------------------
# 연계 파일:
#   • src/services/employees.ts
#   • src/ui/components/hr/DialogContractForm.vue
#   • src/views/Admin/HR/Contracts.vue
# ============================================================================ -->
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
/* ============================================================================
   Script — EmployeePicker (v2.1)
   ---------------------------------------------------------------------------
   Props:
     • modelValue: 선택된 직원 ID
     • onlyActive: 활성 상태 직원만 표시
     • label, placeholder: UI 라벨
   Emits:
     • update:modelValue(v:number|null)
     • selected(row:any|null)
============================================================================ */
import { ref, watch, onMounted, nextTick } from 'vue'
import * as EmployeesApi from '@/services/employees'

/* ▣ Props / Defaults */
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

/* ▣ 상태 */
const innerValue = ref<number | null>(props.modelValue)
const items = ref<any[]>([])
const loading = ref(false)
const q = ref('')
const propertyCode =
  localStorage.getItem('property_code') ||
  import.meta.env.VITE_DEFAULT_PROPERTY_CODE ||
  'MOP'

/* ============================================================================
   데이터 로드
   - EmployeesApi.list({ q, property_code, status, page, size })
   - onlyActive=true → status='active'
============================================================================ */
let fetchTimer: any = null
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
    items.value = res?.items || []
    const sel = items.value.find(r => Number(r?.id) === Number(innerValue.value)) || null
    emit('selected', sel)
  } catch (err) {
    console.error('[EmployeePicker.fetch]', err)
  } finally {
    loading.value = false
  }
}

/* ============================================================================
   검색 입력 이벤트 (Debounce 200ms)
============================================================================ */
function onSearch(v: string) {
  q.value = v || ''
  clearTimeout(fetchTimer)
  fetchTimer = setTimeout(() => fetch(q.value), 200)
}

/* ============================================================================
   선택 변경 → 부모로 전달
============================================================================ */
watch(innerValue, v => {
  emit('update:modelValue', v)
  const sel = items.value.find(r => Number(r?.id) === Number(v)) || null
  emit('selected', sel)
})

/* ============================================================================
   상태 라벨 (한글화)
============================================================================ */
function statusLabel(s?: string) {
  const v = (s || '').toLowerCase()
  if (v === 'active') return '계약중'
  if (v === 'terminated') return '만료'
  if (v === 'none') return '미계약'
  return ''
}

/* ============================================================================
   Mount 시 초기 로드
============================================================================ */
onMounted(async () => {
  await nextTick()
  await fetch()
})

/* ============================================================================
   표시 포맷터
============================================================================ */
const itemTitle = (r: any) =>
  `${r?.name || ''} (${r?.emp_no || ''}) — ${(r?.dept_name || r?.dept || '-')}/${(r?.title_name || r?.title || '-')}`
const itemValue = (r: any) => Number(r?.id ?? 0)
</script>

<style scoped>
.v-autocomplete {
  width: 100%;
}
</style>
