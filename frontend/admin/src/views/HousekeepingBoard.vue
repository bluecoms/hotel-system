<!-- ============================================================================
 File      : src/views/HousekeepingBoard.vue
 Version   : 2025.11-05 · v1.2 (주석 안전화 · Vue 주석 제거 오류 대응)
 Purpose   : Hotel Admin — 하우스키핑 업무보드 (DeptAccess 기반)
 ----------------------------------------------------------------------------
 기능:
   ✅ 일자별 객실 목록 조회 (/api/housekeeping/tasks?business_date=YYYY-MM-DD)
   ✅ 작업 완료 처리 (/api/housekeeping/task/{id}/complete)
   ✅ 직원/부서 필터링 (department_code=HK) — 백엔드 연동 준비
   ✅ 통계(/api/housekeeping/stats/units) 표시
 변경사항(v1.2):
   • Vue 템플릿 주석(<!-- ... -->) 제거 → InvalidCharacterError 해결
   • staff_name 제거 정책 반영(직원ID 표시 우선)
   • 타입 안전 보강 및 fetch 기반 서비스와 완전 호환
============================================================================ -->
<template>
  <v-container fluid class="py-6">
    <v-row>
      <v-col cols="12" class="d-flex align-center justify-space-between">
        <div class="text-h6 font-weight-bold">하우스키핑 업무보드</div>
        <v-text-field
          v-model="businessDate"
          type="date"
          label="업무 일자"
          density="comfortable"
          style="max-width: 200px"
          @change="loadTasks"
        />
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="8">
        <v-data-table
          :headers="headers"
          :items="tasks"
          :loading="loading"
          item-key="id"
          class="elevation-1"
        >
          <template #item.status_after="{ item }">
            <v-chip :color="item.status_after === 'CLEAN' ? 'green' : 'grey'" label>
              {{ item.status_after || '—' }}
            </v-chip>
          </template>

          <template #item.completed_at="{ item }">
            {{ item.completed_at || '—' }}
          </template>

          <template #item.actions="{ item }">
            <v-btn
              v-if="!item.completed_at"
              size="small"
              color="primary"
              @click="completeTask(item.id)"
            >
              완료
            </v-btn>
          </template>
        </v-data-table>
      </v-col>

      <v-col cols="12" md="4">
        <v-card class="pa-4">
          <div class="text-subtitle-1 mb-2">통계 요약</div>
          <v-list>
            <v-list-item
              v-for="s in stats.by_staff"
              :key="s.employee_id ?? s.staff_name ?? String(Math.random())"
            >
              <v-list-item-title>
                {{ s.employee_id != null ? `직원ID #${s.employee_id}` : (s.staff_name || '—') }}
              </v-list-item-title>
              <v-list-item-subtitle>
                {{ s.units }} 유닛 / 완료 {{ s.completed }}/{{ s.count }}
              </v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  getHousekeepingTasks,
  completeHousekeepingTask,
  getHousekeepingStats
} from '@/services/housekeeping'

const businessDate = ref<string>(new Date().toISOString().slice(0, 10))
const tasks = ref<any[]>([])
const stats = ref<{ by_staff: any[] }>({ by_staff: [] })
const loading = ref(false)

const headers = [
  { title: '객실번호', key: 'room_no' },
  { title: '상태', key: 'status_after' },
  { title: '유닛', key: 'units' },
  { title: '완료시간', key: 'completed_at' },
  { title: 'Actions', key: 'actions', sortable: false }
]

async function loadTasks() {
  loading.value = true
  try {
    const res = (await getHousekeepingTasks({
      business_date: businessDate.value
    })) as unknown

    if (Array.isArray(res)) {
      tasks.value = res
    } else if (res && typeof res === 'object' && (res as any).items) {
      tasks.value = (res as any).items
    } else {
      tasks.value = []
    }

    const s = (await getHousekeepingStats({
      business_date: businessDate.value
    })) as unknown

    if (s && typeof s === 'object' && (s as any).by_staff && Array.isArray((s as any).by_staff)) {
      stats.value = s as { by_staff: any[] }
    } else {
      stats.value = { by_staff: [] }
    }
  } finally {
    loading.value = false
  }
}

async function completeTask(id: number) {
  await completeHousekeepingTask(id)
  await loadTasks()
}

onMounted(loadTasks)
</script>
