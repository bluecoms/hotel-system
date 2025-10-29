<!-- ============================================================================
# File      : src/views/HousekeepingAssign.vue
# Version   : 2025.11-10 · v1.0 (SSOT Base · Assignment Plan Draft)
# Purpose   : Hotel Admin — 하우스키핑 정비 배정 화면
# ----------------------------------------------------------------------------
# 목적:
#   • 객실별 청소 담당자(직원) 배정 관리
#   • 배정표(Assignment Plan) 생성/저장/조회
#   • 기본 데이터: MasterRoomType + Employees(HK 부서)
# ----------------------------------------------------------------------------
# 기능 (v1.0):
#   ✅ 업무일자 선택
#   ✅ 객실목록(유형/상태) + 직원 목록 표시
#   ✅ 담당자 드롭다운 선택 → 로컬 상태에 반영
#   ✅ “배정 저장” 버튼 → (후속 단계: API 연결 예정)
# ----------------------------------------------------------------------------
# 향후 보강:
#   • /api/housekeeping/assignments CRUD 추가 예정
#   • Drag & Drop 또는 일괄 배정 기능 추가
# ============================================================================ -->
<template>
  <v-container fluid class="py-6">
    <!-- ▣ 헤더 -->
    <div class="d-flex align-center justify-space-between mb-4">
      <div class="d-flex align-center gap-2">
        <v-icon color="primary" icon="mdi-clipboard-account-outline" size="22" />
        <div>
          <div class="text-h6 font-weight-bold">하우스키핑 정비 배정</div>
          <div class="text-caption text-grey-darken-1">
            객실별 담당 직원을 지정하여 청소 계획을 관리합니다.
          </div>
        </div>
      </div>
      <v-text-field
        v-model="businessDate"
        type="date"
        label="업무일자"
        density="comfortable"
        hide-details
        style="max-width: 200px"
        @change="loadRooms"
      />
    </div>

    <!-- ▣ 메인 패널 -->
    <v-row>
      <!-- 좌측: 객실 목록 -->
      <v-col cols="12" md="8">
        <v-card class="pa-4 elevation-1">
          <div class="d-flex justify-space-between align-center mb-2">
            <h3 class="text-subtitle-1 font-weight-bold">객실 목록</h3>
            <v-btn color="primary" variant="flat" prepend-icon="mdi-content-save" @click="saveAssignments">
              배정 저장
            </v-btn>
          </div>

          <v-data-table
            :headers="headers"
            :items="assignments"
            density="comfortable"
            :loading="loading"
            class="elevation-1"
          >
            <!-- 직원 선택 -->
            <template #item.employee_id="{ item }">
              <v-select
                v-model="item.employee_id"
                :items="employees"
                item-title="name"
                item-value="id"
                label="담당자"
                variant="outlined"
                hide-details
                density="compact"
                clearable
              />
            </template>

            <template #no-data>
              <div class="pa-4 text-grey text-caption text-center">객실 데이터가 없습니다.</div>
            </template>
          </v-data-table>
        </v-card>
      </v-col>

      <!-- 우측: 직원 목록 -->
      <v-col cols="12" md="4">
        <v-card class="pa-4 elevation-1">
          <h3 class="text-subtitle-1 font-weight-bold mb-2">직원 목록</h3>
          <v-list density="compact">
            <v-list-item
              v-for="emp in employees"
              :key="emp.id"
            >
              <v-list-item-title>{{ emp.name }}</v-list-item-title>
              <v-list-item-subtitle>{{ emp.dept || '하우스키핑팀' }}</v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
/* ============================================================================
# Script — HousekeepingAssign
# ----------------------------------------------------------------------------
# • 마스터 객실 + 하우스키핑 직원 목록을 불러와서 화면상 배정 구성
# • 이후 “배정 저장”은 /api/housekeeping/assignments 로 확장 예정
# ============================================================================ */
import { ref, onMounted } from 'vue'
import { useToast } from '@/ui/composables/useToast'
import * as EmployeesApi from '@/services/employees'
import * as MasterApi from '@/services/master'

const toast = useToast()

/* ▣ 상태 */
const businessDate = ref<string>(new Date().toISOString().slice(0, 10))
const assignments = ref<any[]>([]) // 객실 목록 + 직원 배정 상태
const employees = ref<any[]>([])   // 하우스키핑 직원 목록
const loading = ref(false)

/* ▣ 테이블 헤더 */
const headers = [
  { title: '객실번호', key: 'room_no', width: 120 },
  { title: '객실타입', key: 'room_type', width: 140 },
  { title: '상태', key: 'status', width: 120 },
  { title: '담당자', key: 'employee_id', width: 200 },
]

/* ▣ 객실목록 로드 */
async function loadRooms() {
  loading.value = true
  try {
    // MasterRoomType 과의 관계는 추후 연결 (임시 Mock)
    const mockRooms = [
      { id: 1, room_no: '101', room_type: 'STD', status: 'DIRTY', employee_id: null },
      { id: 2, room_no: '102', room_type: 'DLX', status: 'CLEAN', employee_id: null },
      { id: 3, room_no: '103', room_type: 'STW', status: 'DIRTY', employee_id: null },
    ]
    assignments.value = mockRooms
  } catch (e: any) {
    toast.error('객실 목록을 불러올 수 없습니다.')
  } finally {
    loading.value = false
  }
}

/* ▣ 직원목록 로드 */
async function loadEmployees() {
  try {
    const res: any = await EmployeesApi.list({ dept: 'HK', size: 50 })
    employees.value = res.items || []
  } catch {
    employees.value = []
  }
}

/* ▣ 배정 저장 (현재는 로컬 확인용) */
async function saveAssignments() {
  const assigned = assignments.value.filter(r => r.employee_id)
  if (!assigned.length) {
    toast.info('배정된 항목이 없습니다.')
    return
  }
  // 후속: POST /api/housekeeping/assignments
  console.table(assigned)
  toast.success('임시 저장 완료 (API 연결 예정)')
}

/* ▣ 초기화 */
onMounted(() => {
  loadRooms()
  loadEmployees()
})
</script>

<style scoped>
.v-data-table {
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-line);
}
.v-list {
  border: 1px solid var(--color-line);
  border-radius: var(--radius-sm);
}
</style>
