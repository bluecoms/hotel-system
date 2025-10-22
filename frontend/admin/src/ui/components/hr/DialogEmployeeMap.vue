<!-- ============================================================================
  File    : src/ui/components/hr/DialogEmployeeMap.vue
  Version : 2025.10 Final Stable
  Purpose : Hotel Admin — 사원 ↔ 사용자 계정 매핑 다이얼로그
  ------------------------------------------------------------------------------
  연결 백엔드:
    • GET    /api/employees                       → 사원 목록(검색/페이징)
    • PUT    /api/users/{uid}/employee/{eid}      → 사용자-사원 매핑
  관련 파일:
    • src/views/Users/Users.vue                   → 호출 측(사원 매핑 버튼)
    • src/services/employees.ts                   → EmpApi.list()
    • src/services/users.ts                       → UsersApi.mapEmployee()
  주요 개선사항:
    ✅ 드롭다운 → 리스트형 선택(사번·이름·부서·직책 병기, 직관성↑)
    ✅ 이미 매핑된 항목 표기/선택 방지(※ 동일 사용자 매핑은 허용)
    ✅ 선택 요약 카드 표시(사번/부서/직책)
    ✅ 백엔드 엔드포인트 정합(users.py 기반)
============================================================================ -->

<template>
  <v-dialog v-model="open" max-width="820" transition="dialog-bottom-transition">
    <v-card class="rounded-2xl">
      <!-- 헤더 -->
      <v-card-title class="d-flex align-center justify-space-between py-3 px-5">
        <div class="d-flex align-center gap-2">
          <v-icon icon="mdi-account-link-outline" size="20" class="text-primary" />
          <span class="text-h6 font-weight-medium">사원 매핑</span>
        </div>
        <v-btn icon="mdi-close" variant="text" @click="open=false" />
      </v-card-title>

      <v-divider />

      <!-- 본문 -->
      <v-card-text class="px-5 py-4">
        <!-- 선택 대상 사용자 요약 -->
        <v-alert
          v-if="user"
          type="info"
          variant="tonal"
          border="start"
          density="compact"
          class="mb-4"
        >
          <v-icon icon="mdi-account-circle-outline" start />
          대상 계정:
          <strong>{{ user.name || user.email }}</strong>
          <span class="text-grey-darken-1">({{ user.email }})</span>
          <template #append>
            <v-chip
              v-if="user.employee_id"
              size="x-small"
              color="teal"
              class="ml-2"
              label
            >
              현재 연결: #{{ user.employee_id }}
            </v-chip>
            <v-chip
              v-else
              size="x-small"
              color="grey"
              variant="tonal"
              class="ml-2"
              label
            >
              미매핑
            </v-chip>
          </template>
        </v-alert>

        <!-- 검색 입력 -->
        <div class="d-flex align-center gap-2 mb-3">
          <v-text-field
            v-model="q"
            label="검색 (사번 / 이름 / 부서 / 직책)"
            prepend-inner-icon="mdi-magnify"
            variant="outlined"
            density="comfortable"
            hide-details
            clearable
            @keyup.enter="reload()"
            class="flex-1"
          />
          <v-btn variant="tonal" :loading="loadingList" @click="reload">
            새로고침
          </v-btn>
        </div>

        <!-- 리스트형 선택 (v-autocomplete + 커스텀 아이템) -->
        <v-autocomplete
          v-model="selectedEmpId"
          :items="displayItems"
          item-title="__label"
          item-value="id"
          label="사원 선택 (사번·이름·부서·직책)"
          variant="outlined"
          density="comfortable"
          prepend-inner-icon="mdi-account-search"
          :loading="loadingList"
          hide-details
          class="mb-3"
        >
          <!-- 아이템 렌더링: 사번/이름/부서/직책 + 상태칩 -->
          <template #item="{ item, props }">
            <v-list-item v-bind="props" :disabled="isDisabled(item.raw)">
              <div class="row-line">
                <div class="left">
                  <span class="mono">{{ item.raw.emp_no || '-' }}</span>
                  <span class="name">{{ item.raw.name }}</span>
                  <span class="hint">{{ item.raw.dept || '-' }}</span>
                  <span class="hint">{{ item.raw.title_name || item.raw.title || '-' }}</span>
                </div>
                <div class="right">
                  <v-chip
                    v-if="isDisabled(item.raw)"
                    size="x-small"
                    color="grey"
                    variant="flat"
                    label
                  >
                    매핑됨
                  </v-chip>
                </div>
              </div>
            </v-list-item>
          </template>

          <!-- 선택 렌더링(입력 상자 내부) -->
          <template #selection="{ item }">
            <span class="mono">{{ item.raw.emp_no }}</span>
            <span class="ml-1">{{ item.raw.name }}</span>
            <span class="sel-hint">/ {{ item.raw.dept }} · {{ item.raw.title_name || item.raw.title }}</span>
          </template>

          <template #no-data>
            <div class="pa-4 text-grey">검색 결과가 없습니다.</div>
          </template>
        </v-autocomplete>

        <!-- 선택 요약 카드 -->
        <v-expand-transition>
          <div v-if="selected" class="selected-card">
            <v-icon size="18" class="mr-1" color="primary">mdi-badge-account</v-icon>
            <strong>{{ selected.name }}</strong>
            <span class="mono ml-2">{{ selected.emp_no }}</span>
            <span class="hint ml-2">{{ selected.dept }}</span>
            <span class="hint ml-2">{{ selected.title_name || selected.title }}</span>
          </div>
        </v-expand-transition>
      </v-card-text>

      <v-divider />

      <!-- 액션 -->
      <v-card-actions class="px-5 py-3">
        <v-spacer />
        <v-btn variant="text" color="grey" @click="open=false">취소</v-btn>
        <v-btn
          color="primary"
          prepend-icon="mdi-link-variant"
          :loading="loading"
          :disabled="!selectedEmpId"
          @click="mapNow"
        >
          매핑 저장
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
/* ============================================================================
  Script  : DialogEmployeeMap.vue (Composition API)
  Notes   :
    • 열리는 순간 사원 목록 로드(EmpApi.list)
    • 이미 타 사용자와 매핑된 사원은 선택 비활성 (단, 현재 사용자와의 기존 연결은 허용)
    • 저장 시 UsersApi.mapEmployee(user.id, selectedEmpId)
============================================================================ */
import { computed, ref, watch } from 'vue'
import * as EmpApi from '@/services/employees'
import * as UsersApi from '@/services/users'
import { useToast } from '@/ui/composables/useToast'

type EmpRow = {
  id: number
  emp_no?: string
  name: string
  dept?: string
  title?: string
  title_name?: string
  // 있으면 다른 사용자에 이미 매핑된 것으로 간주(백엔드 스펙에 맞춰 자유 필드)
  mapped_user_id?: number | null
}

const props = defineProps<{
  modelValue: boolean
  user?: { id: number; email: string; name?: string; employee_id?: number | null }
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'mapped'): void
}>()

const toast = useToast()
const open = ref(props.modelValue)
const user = ref(props.user || null)

const employees = ref<EmpRow[]>([])
const loadingList = ref(false)

const q = ref('')
const selectedEmpId = ref<number | null>(null)
const loading = ref(false)

watch(() => props.modelValue, (v) => {
  open.value = v
  if (v) {
    q.value = ''
    selectedEmpId.value = null
    reload()
  }
})
watch(() => props.user, (v) => (user.value = v || null))
watch(open, (v) => emit('update:modelValue', v))

async function reload() {
  loadingList.value = true
  try {
    // EmpApi.list: { q, page, size } 계약 가정
    const resp: any = await EmpApi.list({ q: q.value, page: 1, size: 50 })
    // 백엔드 항목 표준화(title_name fallback 포함)
    const items: EmpRow[] = (resp?.items || []).map((r: any) => ({
      id: r.id,
      emp_no: r.emp_no || '',
      name: r.name || '',
      dept: r.dept || '',
      title: r.title || '',
      title_name: r.title_name || r.title || '',
      mapped_user_id: r.mapped_user_id ?? null,
    }))
    employees.value = items
  } catch (e: any) {
    employees.value = []
  } finally {
    loadingList.value = false
  }
}

const displayItems = computed(() =>
  employees.value
    .filter((r) => {
      if (!q.value) return true
      const s = `${r.emp_no} ${r.name} ${r.dept} ${r.title_name || r.title}`.toLowerCase()
      return s.includes(q.value.trim().toLowerCase())
    })
    .map((r) => ({
      ...r,
      __label: `${r.emp_no || '-'} · ${r.name} · ${r.dept || '-'} · ${r.title_name || r.title || '-'}${
        isDisabled(r) ? ' (매핑됨)' : ''
      }`,
    }))
)

const selected = computed(() => {
  const id = selectedEmpId.value
  if (!id) return null
  return employees.value.find((x) => x.id === id) || null
})

function isDisabled(row: EmpRow): boolean {
  // 다른 사용자에 이미 매핑되어 있으면 비활성
  if (row.mapped_user_id && user.value && row.mapped_user_id !== user.value.id) return true
  return false
}

async function mapNow() {
  if (!selectedEmpId.value || !user.value) return
  loading.value = true
  try {
    const empId = Number(selectedEmpId.value)  // ✅ 문자열 → 숫자 변환 (핵심)
    await UsersApi.mapEmployee(user.value.id, empId)
    toast.success('사원 매핑이 저장되었습니다.')
    emit('mapped')
    open.value = false
  } catch (e: any) {
    toast.error(e?.response?.detail || e?.message || '매핑에 실패했습니다.')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.flex-1 { flex: 1; }

.row-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.name {
  font-weight: 600;
}

.hint {
  color: #6b7280; /* grey-500 */
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  letter-spacing: 0.1px;
}

.sel-hint {
  color: #6b7280;
  margin-left: 6px;
}

.selected-card {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgb(var(--v-theme-surface));
  border: 1px solid var(--color-line, #e5e7eb);
  border-radius: 10px;
  padding: 10px 12px;
  box-shadow: 0 2px 8px rgba(16, 24, 40, 0.06);
}
</style>
