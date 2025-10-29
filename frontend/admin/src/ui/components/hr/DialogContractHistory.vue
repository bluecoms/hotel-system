<!-- ============================================================================
# File    : src/ui/components/hr/DialogContractHistory.vue
# Version : 4.2 (2025-11-10 · salary_monthly → salary · SSOT Final)
# Purpose : 근로계약 이력 다이얼로그 (계약별 버전 이력 조회)
# ----------------------------------------------------------------------------
# ✅ 변경 요약 (v4.2)
#   • 급여 필드명 수정: salary_monthly → salary (SSOT 스키마 통일)
#   • API 경로 확정 → /api/contracts/{id}/versions
#   • contractId null 가드 보강
#   • UI 및 주석 구조 일관화
# ----------------------------------------------------------------------------
# 목적:
#   • 근로계약의 변경·만료 이력을 직관적으로 표시
#   • 버전별 계약기간, 급여, 상태를 보기 좋게 정렬
#   • 목록 없을 때는 StateBlock 컴포넌트로 공백상태 안내
# ============================================================================
-->
<template>
  <v-dialog
    :model-value="open"
    max-width="840"
    scrollable
    @update:model-value="v => emit('update:open', v)"
  >
    <v-card class="rounded-xl">
      <!-- ─────────────── 헤더 ─────────────── -->
      <v-card-title class="d-flex align-center justify-space-between py-3 px-5">
        <div class="d-flex align-center gap-2">
          <v-icon icon="mdi-history" color="primary" size="22" />
          <div>
            <div class="text-subtitle-1 font-weight-bold">계약 이력</div>
            <div class="text-caption text-grey-darken-1">변경 · 만료 이력 확인</div>
          </div>
        </div>
        <v-btn icon="mdi-close" variant="text" @click="emit('update:open', false)" />
      </v-card-title>

      <v-divider />

      <!-- ─────────────── 본문 ─────────────── -->
      <v-card-text class="px-5 py-4">
        <!-- 로딩 상태 -->
        <v-skeleton-loader v-if="loading" type="table" class="my-4" />

        <!-- 계약 이력 테이블 -->
        <v-data-table
          v-else
          :headers="headers"
          :items="versions"
          class="elevation-1 rounded-lg"
          density="comfortable"
          hover
        >
          <!-- 버전 -->
          <template #item.version_no="{ item }">
            <span class="font-weight-medium text-primary">v{{ item.version_no }}</span>
          </template>

          <!-- 계약유형 -->
          <template #item.contract_type="{ item }">
            <v-chip size="small" color="primary" variant="flat" label>
              {{ typeLabel(item.contract_type) }}
            </v-chip>
          </template>

          <!-- 급여 -->
          <template #item.salary="{ item }">
            <div class="text-right font-weight-medium">
              {{ fmtCurrency(item.salary) }}
            </div>
          </template>

          <!-- 상태 -->
          <template #item.status="{ item }">
            <v-chip
              size="small"
              :color="item.status === 'active' ? 'success' : 'grey-lighten-1'"
              :text-color="item.status === 'active' ? 'white' : 'grey-darken-1'"
              label
            >
              {{ statusLabel(item.status) }}
            </v-chip>
          </template>

          <!-- 데이터 없음 -->
          <template #no-data>
            <StateBlock
              icon="mdi-file-document-outline"
              title="계약 이력이 없습니다."
              subtitle="신규 계약을 등록하거나 기존 이력을 다시 불러와 주세요."
            />
          </template>
        </v-data-table>
      </v-card-text>

      <v-divider />

      <!-- ─────────────── 푸터 ─────────────── -->
      <v-card-actions class="px-5 py-3 justify-end">
        <v-btn variant="text" @click="emit('update:open', false)">닫기</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
/* ============================================================================
# Script — DialogContractHistory (v4.2)
# ----------------------------------------------------------------------------
# 기능 요약:
#   • 계약별 버전 이력 조회
#   • props.contractId 로 /api/contracts/{id}/versions 호출
#   • contractId 유효성 검사 및 에러 핸들링 포함
# ============================================================================
*/
import { ref, watch } from 'vue'
import http from '@/services/http'
import { useToast } from '@/ui/composables/useToast'
import StateBlock from '@/ui/components/common/StateBlock.vue'

/* ─────────────── Props / Emits ─────────────── */
const props = defineProps<{ open: boolean; contractId: string | number | null }>()
const emit = defineEmits<{ (e: 'update:open', v: boolean): void }>()

const { error } = useToast()
const loading = ref(false)
const versions = ref<any[]>([])

/* ─────────────── 테이블 헤더 ─────────────── */
const headers = [
  { title: '버전', key: 'version_no', width: '70px' },
  { title: '유형', key: 'contract_type', width: '140px' },
  { title: '성명', key: 'employee_name', width: '120px' },
  { title: '시작일', key: 'start_date', width: '120px' },
  { title: '종료일', key: 'end_date', width: '120px' },
  { title: '월급(세전)', key: 'salary', align: 'end', width: '140px' },
  { title: '상태', key: 'status', width: '100px' },
  { title: '생성일', key: 'created_at', width: '160px' },
]

/* ─────────────── 데이터 로드 ─────────────── */
async function load() {
  if (!props.contractId) {
    error('계약 ID가 유효하지 않습니다.')
    return
  }
  try {
    loading.value = true
    const res: any = await http.get(`/contracts/${props.contractId}/versions`)
    versions.value = Array.isArray(res) ? res : []
  } catch (err) {
    console.error('[DialogContractHistory] Load fail:', err)
    error('계약 이력을 불러오지 못했습니다.')
  } finally {
    loading.value = false
  }
}

/* ─────────────── 헬퍼 ─────────────── */
function fmtCurrency(n?: number) {
  if (!n && n !== 0) return '-'
  try {
    return '₩' + Math.floor(n).toLocaleString('ko-KR')
  } catch {
    return String(n)
  }
}
function typeLabel(v: string) {
  switch (v) {
    case 'PARTTIME': return '아르바이트'
    case 'DAILY': return '일용직'
    case 'MONTHLY': return '정규직(월급제)'
    default: return v || '-'
  }
}
function statusLabel(v?: string) {
  const s = (v || '').toUpperCase()
  if (s === 'ACTIVE') return '진행중'
  if (s === 'TERMINATED') return '종료'
  if (s === 'DRAFT') return '작성중'
  return '-'
}

/* ─────────────── 다이얼로그 감시 ─────────────── */
watch(() => props.open, (v) => {
  if (v) load()
})
</script>

<style scoped>
.v-data-table { border-radius: 8px; }
</style>
