<!-- ============================================================================
# File      : src/ui/components/users/master/MasterTable.vue
# Version   : 2025.10-25 · v2.1 (Add Bank Support · SSOT Stable)
# Purpose   : Hotel Admin — 공통 기준정보 테이블 (MasterTable)
# ----------------------------------------------------------------------------
# 목적:
#   • 인사관리 및 운영 전반의 기준정보를 하나의 공통 컴포넌트로 관리.
#   • CRUD / 검색 / 사용여부 토글 / 순서 정렬 기능을 통합 제공.
# ----------------------------------------------------------------------------
# 구성:
#   • 공통 컬럼: 코드 / 이름 / 사용 / 식별자 / 작업
#   • 급여등급(master_salary_grades): 연봉(₩) 표시 추가
#   • 지점(properties): 코드(PK) 기반 PUT/DELETE 처리 대응
#   • 은행(master_banks): alias(약칭) 필드 및 id 기반 CRUD
# ----------------------------------------------------------------------------
# 연계:
#   • backend: /api/master/* , /api/properties
#   • frontend: src/views/Users/master/*Table.vue
#   • 활용: 부서 / 직책 / 직급 / 급여 / 사번 / 지점(Property) / 은행(Bank)
# ----------------------------------------------------------------------------
# 변경이력:
#   v2.0 (2025-10-24) : Property 지원 추가
#   v2.1 (2025-10-25) : Bank(alias 필드) 입력/표시 로직 통합
# ============================================================================ -->
<template>
  <v-card flat class="rounded-xl elevation-1">
    <!-- ▣ 헤더 -->
    <v-card-title class="d-flex flex-wrap gap-2 align-center justify-space-between">
      <div class="d-flex align-center gap-2">
        <v-icon :color="color" size="22">{{ icon }}</v-icon>
        <span class="font-weight-bold text-subtitle-1">{{ title }}</span>
      </div>
      <div class="d-flex align-center gap-2">
        <v-text-field
          v-model="q"
          density="compact"
          clearable
          hide-details
          prepend-inner-icon="mdi-magnify"
          placeholder="검색 (코드/이름)"
          style="max-width:260px"
          @keyup.enter="load"
        />
        <v-btn color="primary" prepend-icon="mdi-plus" @click="openAddDialog">추가</v-btn>
      </div>
    </v-card-title>

    <v-divider />

    <!-- ▣ 목록 테이블 -->
    <v-table class="px-3 pb-2">
      <thead>
        <tr>
          <th style="width:120px;">#</th>
          <th style="min-width:140px;">코드</th>
          <th style="min-width:180px;">이름</th>
          <th v-if="isBank" style="min-width:160px;">약칭(Alias)</th>
          <th v-if="isSalaryGrades" style="width:140px;" class="text-end">연봉(₩)</th>
          <th style="width:100px;" class="text-center">사용</th>
          <th style="width:110px;">식별자</th>
          <th style="width:120px;" class="text-center">작업</th>
        </tr>
      </thead>

      <draggable
        v-model="rows"
        item-key="_id"
        tag="tbody"
        handle=".drag-handle"
        @end="onReorder"
      >
        <template #item="{ element, index }">
          <tr v-show="matchFilter(element, q)">
            <!-- 순번칩 -->
            <td class="text-center">
              <v-chip size="small" color="grey" variant="tonal" class="mr-2">{{ index + 1 }}</v-chip>
              <v-icon size="18" color="grey" class="drag-handle">mdi-drag</v-icon>
            </td>

            <!-- 코드 / 이름 -->
            <td>{{ element.code }}</td>
            <td>{{ element.name }}</td>

            <!-- 은행 전용: Alias 표시 -->
            <td v-if="isBank">{{ element.alias || '-' }}</td>

            <!-- 급여 등급 전용: 연봉 표시 -->
            <td v-if="isSalaryGrades" class="text-end">
              ₩{{ Number(element.annual_salary || 0).toLocaleString() }}
            </td>

            <!-- 사용 여부 -->
            <td class="text-center">
              <v-chip
                size="small"
                :color="toBool(element.is_active) ? 'success' : 'grey-lighten-1'"
                :text-color="toBool(element.is_active) ? 'white' : 'grey-darken-1'"
                label
              >
                {{ toBool(element.is_active) ? '사용' : '중지' }}
              </v-chip>
            </td>

            <!-- 식별자 -->
            <td>
              <v-chip size="small" variant="tonal" color="grey">{{ element[_idKey] }}</v-chip>
            </td>

            <!-- 작업 버튼 -->
            <td class="text-center">
              <v-btn icon="mdi-pencil" color="primary" variant="text" size="small"
                     @click="openEditDialog(element)" />
              <v-btn icon="mdi-delete" color="error" variant="text" size="small"
                     @click="remove(element)" />
            </td>
          </tr>
        </template>
      </draggable>

      <tfoot v-if="!loading && rows.length === 0">
        <tr>
          <td :colspan="tableColspan" class="text-center py-8 text-medium-emphasis">
            데이터가 없습니다.
          </td>
        </tr>
      </tfoot>
    </v-table>

    <!-- 로딩 인디케이터 -->
    <v-progress-linear v-if="loading" indeterminate class="mt-2" />

    <!-- ▣ 추가/수정 다이얼로그 -->
    <v-dialog v-model="dlg.open" max-width="460px">
      <v-card class="rounded-xl">
        <v-card-title class="text-h6">
          {{ dlg.mode === 'edit' ? '항목 수정' : '항목 추가' }}
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-form ref="formRef" v-model="formValid" lazy-validation>
            <v-row dense>
              <!-- 코드 -->
              <v-col cols="12" md="6" v-if="dlg.mode === 'add'">
                <v-text-field
                  v-model="dlg.code"
                  label="코드 (영문 대문자)"
                  placeholder="예: NH / KB / WR"
                  clearable
                  :rules="[ruleRequired, ruleCode]"
                  @blur="dlg.code = (dlg.code || '').toUpperCase()"
                />
              </v-col>

              <!-- 이름 -->
              <v-col :cols="dlg.mode === 'add' ? 12 : 12" :md="dlg.mode === 'add' ? 6 : 12">
                <v-text-field
                  v-model="dlg.name"
                  label="이름"
                  placeholder="예: 농협은행 / 국민은행"
                  clearable
                  :rules="[ruleRequired]"
                />
              </v-col>

              <!-- 은행 전용: 약칭 입력 -->
              <v-col v-if="isBank" cols="12">
                <v-text-field
                  v-model="dlg.alias"
                  label="약칭 (Alias)"
                  placeholder="예: NH Bank / KB Bank"
                  clearable
                />
              </v-col>

              <!-- 급여 등급 전용: 연봉 -->
              <v-col v-if="isSalaryGrades" cols="12">
                <v-text-field
                  v-model.number="dlg.base_salary"
                  label="연봉(세전)"
                  type="number"
                  prefix="₩"
                  clearable
                />
              </v-col>

              <!-- 사용 여부 -->
              <v-col cols="12">
                <v-switch
                  v-model="dlg.is_active"
                  inset
                  color="primary"
                  hide-details
                  label="사용"
                />
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="dlg.open = false">취소</v-btn>
          <v-btn color="primary" @click="confirmDialog">확인</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<script setup lang="ts">
/* ============================================================================
# Script Logic
# ----------------------------------------------------------------------------
#   • CRUD + 필터링 + 순서 재정렬
#   • Property(지점) 및 Bank(은행) 전용 로직 포함
# ============================================================================ */
import { ref, onMounted, watch, computed } from 'vue'
import draggable from 'vuedraggable'
import http from '@/services/http'
import { useToast } from '@/ui/composables/useToast'
const { success, error } = useToast()

/* ▣ Props 정의 */
const props = withDefaults(defineProps<{
  title: string
  apiBase: string
  icon?: string
  color?: string
  idKey?: string
  codeKey?: string[]
  nameKey?: string[]
}>(), {
  icon: 'mdi-view-list-outline',
  color: 'primary',
  idKey: 'id',
  codeKey: () => ['code', 'dept_code', 'title_code', 'rank_code'],
  nameKey: () => ['name', 'dept_name', 'title_name', 'rank_name'],
})

/* ▣ Emits 정의 */
const emit = defineEmits<{
  (e: 'reloaded', rows: any[]): void
  (e: 'saved', item: any): void
  (e: 'deleted', id: string | number): void
}>()

/* 내부 상태 */
const _idKey = props.idKey
const isSalaryGrades = computed(() => props.apiBase?.includes('salary-grades'))
const isProperty = computed(() => props.apiBase?.includes('properties'))
const isBank = computed(() => props.apiBase?.includes('banks')) // ✅ 추가
const rows = ref<any[]>([])
const loading = ref(false)
const q = ref('')

/* 다이얼로그 */
const dlg = ref({
  open: false,
  mode: 'add' as 'add' | 'edit',
  target: null as any,
  code: '',
  name: '',
  alias: '',
  base_salary: 0,
  is_active: true,
})
const formRef = ref()
const formValid = ref(false)

/* ─────────────── 유틸/검증 ─────────────── */
const ruleRequired = (v: any) => (!!v && String(v).trim().length > 0) || '필수 입력입니다.'
const ruleCode = (v: string) => /^[A-Z0-9_]+$/.test(v || '') || '영문 대문자/숫자/밑줄(_)만 허용'
const toBool = (v: any) => (v === true || v === 1 || v === '1' || v === 'true' || v === 'TRUE')

function pick(r: any, keys: string[], fallback = '') {
  for (const k of keys) if (r?.[k] !== undefined && r?.[k] !== null) return r[k]
  return fallback
}
function normalizeRow(r: any) {
  const idVal = r?.[_idKey] ?? r?.id ?? r?.code
  return {
    ...r,
    _id: idVal,
    [_idKey]: idVal,
    code: pick(r, props.codeKey, r?.code || ''),
    name: pick(r, props.nameKey, r?.name || ''),
    alias: r?.alias || '',
    base_salary: r?.base_salary ?? 0,
    is_active: toBool(r?.is_active ?? true),
    order_no: r?.order_no ?? null,
  }
}
function matchFilter(row: any, keyword: string) {
  const s = (keyword || '').trim().toLowerCase()
  if (!s) return true
  return (
    String(row.code || '').toLowerCase().includes(s) ||
    String(row.name || '').toLowerCase().includes(s) ||
    String(row.alias || '').toLowerCase().includes(s)
  )
}

/* ─────────────── CRUD ─────────────── */
async function load() {
  loading.value = true
  try {
    const base = props.apiBase.replace(/^\/?api\//, '')
    const res: any = await http.get(base)
    const list = Array.isArray(res) ? res : (res?.items ?? [])
    rows.value = list.map(normalizeRow)
    emit('reloaded', rows.value)
  } catch {
    error('불러오기 실패')
  } finally {
    loading.value = false
  }
}

function openAddDialog() {
  dlg.value = { open: true, mode: 'add', target: null, code: '', name: '', alias: '', base_salary: 0, is_active: true }
}
function openEditDialog(item: any) {
  dlg.value = {
    open: true, mode: 'edit', target: item,
    code: item.code, name: item.name, alias: item.alias || '',
    base_salary: item.base_salary || 0,
    is_active: toBool(item.is_active),
  }
}

async function confirmDialog() {
  const ok = await (formRef.value as any)?.validate?.()
  if (!ok?.valid) return
  dlg.value.base_salary = Number(dlg.value.base_salary) || 0

  try {
    const base = props.apiBase.replace(/^\/?api\//, '')
    const isAdd = dlg.value.mode === 'add'
    let payload: any = { code: dlg.value.code, name: dlg.value.name, is_active: dlg.value.is_active }

    if (isBank.value) payload.alias = dlg.value.alias
    if (isSalaryGrades.value) payload.base_salary = dlg.value.base_salary
    if (base.includes('departments')) {
      payload.dept_code = dlg.value.code
      payload.dept_name = dlg.value.name
    }

    if (isAdd) {
      const created = await http.post(base, payload)
      success('등록 완료'); emit('saved', created ?? payload)
    } else {
      const id = dlg.value.target?.[_idKey]
      const urlId = isProperty.value ? dlg.value.code : id
      const updated = await http.put(`${base}/${urlId}`, payload)
      success('수정 완료'); emit('saved', updated ?? { id: urlId, ...payload })
    }

    dlg.value.open = false
    await load()
  } catch {
    error('저장 실패')
  }
}

async function remove(item: any) {
  const id = item?.[_idKey] ?? item?.code
  if (!confirm(`'${item?.name}' 항목을 삭제하시겠습니까?`)) return
  try {
    const base = props.apiBase.replace(/^\/?api\//, '')
    const urlId = isProperty.value ? item.code : id
    await http.delete(`${base}/${urlId}`)
    success('삭제 완료'); emit('deleted', urlId)
    await load()
  } catch {
    error('삭제 실패')
  }
}

/* 순서 정렬 저장 */
async function onReorder() {
  try {
    const base = props.apiBase.replace(/^\/?api\//, '')
    const items = rows.value.map((r: any, idx: number) => ({ id: r[_idKey], order_no: idx + 1 }))
    await http.put(`${base}/reorder`, { items })
    success('순서가 저장되었습니다.')
  } catch {
    error('순서 저장 실패')
  }
}

/* ▣ 테이블 colspan 계산 */
const tableColspan = computed(() => (isBank.value ? 8 : isSalaryGrades.value ? 7 : 6))

/* 초기 로드 */
onMounted(load)
watch(() => props.apiBase, () => load(), { flush: 'post' })
</script>

<style scoped>
.drag-handle { cursor: move; }
.gap-2 { gap: .5rem; }
.text-end { text-align: right; }
</style>
