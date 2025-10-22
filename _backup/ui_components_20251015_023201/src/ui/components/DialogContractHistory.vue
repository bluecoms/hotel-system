<template>
  <v-dialog
    :model-value="open"
    max-width="760"
    scrollable
    :persistent="false"
    @update:model-value="v => emit('update:open', v)"
  >
    <v-card>
      <v-card-title class="d-flex align-center justify-space-between py-3">
        <div class="d-flex align-center gap-2">
          <v-icon icon="mdi-history" class="mr-1" />
          <div>
            <div class="text-subtitle-1 font-weight-bold">계약 이력</div>
            <div class="text-caption text-grey-darken-1">변경/만료 이력 확인</div>
          </div>
        </div>
        <v-btn icon="mdi-close" variant="text" @click="emit('update:open', false)" />
      </v-card-title>

      <v-divider />

      <v-card-text>
        <v-skeleton-loader v-if="loading" type="table" class="my-4" />
        <template v-else>
          <v-table density="comfortable" fixed-header>
            <thead>
              <tr>
                <th class="text-left">버전</th>
                <th class="text-left">유형</th>
                <th class="text-left">성명</th>
                <th class="text-left">시작</th>
                <th class="text-left">종료</th>
                <th class="text-right">월급</th>
                <th class="text-left">상태</th>
                <th class="text-left">생성일</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="ver in versions"
                :key="ver.version_no"
                :class="{ 'text-muted': ver.status === 'ENDED' }"
              >
                <td class="text-left">v{{ ver.version_no }}</td>
                <td class="text-left">{{ ver.contract_type }}</td>
                <td class="text-left">{{ ver.employee_name }}</td>
                <td class="text-left">{{ ver.start_date }}</td>
                <td class="text-left">{{ ver.end_date || '-' }}</td>
                <td class="text-right">{{ fmtCurrency(ver.salary_monthly) }}</td>
                <td class="text-left">{{ ver.status || '-' }}</td>
                <td class="text-left">{{ ver.created_at || '-' }}</td>
              </tr>
              <tr v-if="!versions.length">
                <td colspan="8">
                  <NoDataBox message="이력이 없습니다." />
                </td>
              </tr>
            </tbody>
          </v-table>
        </template>
      </v-card-text>

      <v-divider />

      <v-card-actions class="justify-end">
        <v-btn variant="text" @click="emit('update:open', false)">닫기</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { watch, ref } from 'vue'
import http from '@/services/http'
import { useToast } from '@/ui/composables/useToast'
import NoDataBox from '@/ui/components/NoDataBox.vue'

type VersionRow = {
  version_no: number
  contract_type: string
  employee_name: string
  start_date: string
  end_date?: string
  salary_monthly?: number
  status?: string
  created_at?: string
}

const props = defineProps<{
  open: boolean
  contractId: string | number
}>()

const emit = defineEmits<{ (e: 'update:open', v: boolean): void }>()
const { error } = useToast()

const loading = ref(false)
const versions = ref<VersionRow[]>([])

async function load() {
  try {
    loading.value = true
    const res: any = await http.get(`/contracts/${props.contractId}/versions`)
    versions.value = Array.isArray(res) ? res : []
  } catch (e: any) {
    error('이력을 불러오지 못했습니다.')
  } finally {
    loading.value = false
  }
}

function fmtCurrency(n?: number) {
  if (n === null || n === undefined) return '-'
  try { return (n || 0).toLocaleString() + '₩' } catch { return String(n) + '₩' }
}

/** 대화상자 열릴 때마다 새로 로드 */
watch(() => props.open, (v) => { if (v) load() })
</script>

<style scoped>
.text-muted {
  color: var(--color-muted);
}
</style>
