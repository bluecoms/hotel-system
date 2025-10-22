<template>
  <v-container fluid class="page-shell py-6">
    <div class="bar mb-6">
      <div class="bar-left">
        <v-icon color="primary" icon="mdi-account-link-outline" size="22" />
        <h2 class="text-h6 font-weight-bold">직원 ↔ 계정 매핑</h2>
        <span class="text-muted text-body-2">직원 정보와 사용자 계정 연결 관리</span>
      </div>
      <div class="bar-right">
        <v-btn
          color="primary"
          prepend-icon="mdi-sync"
          :loading="loading"
          variant="flat"
          class="btn-action"
          @click="reload"
        >
          새로고침
        </v-btn>
      </div>
    </div>

    <SmartFilterBar class="mb-4 brand-panel">
      <template #filters>
        <v-text-field
          v-model="filters.q"
          label="검색 (직원명, 계정 이메일)"
          prepend-inner-icon="mdi-magnify"
          clearable
          hide-details
          density="comfortable"
          class="min-w-240"
          @keyup.enter="reload"
        />

        <v-select
          v-model="filters.status"
          :items="statusItems"
          label="매핑 상태"
          clearable
          hide-details
          density="comfortable"
          style="max-width: 180px"
          @update:model-value="reload"
        />

        <v-btn
          color="primary"
          variant="flat"
          class="btn-action"
          :loading="loading"
          @click="reload"
        >
          검색
        </v-btn>

        <v-btn
          variant="outlined"
          color="grey"
          class="btn-action"
          :disabled="loading"
          @click="resetFilters"
        >
          초기화
        </v-btn>
      </template>
    </SmartFilterBar>

    <BoardList
      :headers="headers"
      :items="rows"
      :total="total"
      :loading="loading"
      :page="page"
      :size="size"
      @update:page="(p) => { page = p; reload() }"
      @update:items-per-page="(s) => { size = s; page = 1; reload() }"
    >
      <template #cell.employee_name="{ item }">
        <div>
          <div class="font-weight-medium">{{ item.employee_name }}</div>
          <div class="text-caption text-grey-darken-1">{{ item.dept }}</div>
        </div>
      </template>

      <template #cell.user_email="{ item }">
        <div v-if="item.user_email">
          <v-icon size="16" class="mr-1" color="primary">mdi-email</v-icon>
          {{ item.user_email }}
        </div>
        <div v-else class="text-grey text-caption">— 미매핑 —</div>
      </template>

      <template #cell.status="{ item }">
        <v-chip
          size="small"
          :color="item.user_email ? 'success' : 'grey-lighten-2'"
          :text-color="item.user_email ? 'white' : 'grey-darken-2'"
          label
        >
          {{ item.user_email ? '매핑됨' : '미매핑' }}
        </v-chip>
      </template>

      <template #cell.actions="{ item }">
        <v-btn
          v-if="!item.user_email"
          size="small"
          color="primary"
          variant="text"
          prepend-icon="mdi-link-variant"
          @click="openLinkDialog(item)"
        >
          매핑
        </v-btn>
        <v-btn
          v-else
          size="small"
          color="error"
          variant="text"
          prepend-icon="mdi-link-variant-off"
          @click="unlink(item)"
        >
          해제
        </v-btn>
      </template>

      <template #no-data>
        <NoDataBox
          icon="mdi-account-arrow-left-outline"
          title="직원 정보 없음"
          subtitle="검색 조건을 변경하거나 새로고침해 보세요."
          @reset="resetFilters"
        />
      </template>
    </BoardList>

    <!-- 필수 prop(open, propertyCode) 추가 -->
    <DialogLinkAccount
      v-model="dialogLink"
      :open="dialogLink"
      :employee="selectedEmployee"
      :propertyCode="propertyCode"
      @linked="reload"
    />
  </v-container>
</template>

<script setup lang="ts">
/**
 * AccountLink.vue — HR 직원-계정 매핑 (SmartFilterBar + BoardList 통합형 최신판)
 */
import { ref, reactive, onMounted, computed } from 'vue'
import { useToast } from '@/ui/composables/useToast'
import * as LinkApi from '@/services/account_link'

// 공통 UI 컴포넌트
import SmartFilterBar from '@/ui/components/SmartFilterBar.vue'
import BoardList from '@/ui/components/BoardList.vue'
import NoDataBox from '@/ui/components/NoDataBox.vue'
import DialogLinkAccount from '@/ui/components/DialogLinkAccount.vue'

const toast = useToast()

// 기본 propertyCode (호텔 코드)
const propertyCode = computed(() => 'MOP')

// 상태 관리
const rows = ref<any[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const size = ref(20)

const filters = reactive({
  q: '',
  status: '',
})

const statusItems = [
  { title: '전체', value: '' },
  { title: '매핑됨', value: 'linked' },
  { title: '미매핑', value: 'unlinked' },
]

const headers = [
  { title: '직원명', key: 'employee_name', sortable: true },
  { title: '부서', key: 'dept', sortable: true },
  { title: '계정 이메일', key: 'user_email', sortable: true },
  { title: '상태', key: 'status', sortable: false },
  { title: '관리', key: 'actions', sortable: false },
]

const dialogLink = ref(false)
const selectedEmployee = ref<any>(null)

// 계정 매핑 다이얼로그 열기
function openLinkDialog(item: any) {
  selectedEmployee.value = item
  dialogLink.value = true
}

// 매핑 해제
async function unlink(item: any) {
  if (!confirm(`'${item.employee_name}'의 계정 매핑을 해제하시겠습니까?`)) return
  try {
    await LinkApi.unlink(item.employee_id)
    toast.success('매핑이 해제되었습니다.')
    reload()
  } catch (e: any) {
    toast.error('해제 실패')
  }
}

// 목록 조회
async function reload() {
  loading.value = true
  try {
    // LinkApi.list 내부 URL 중복 방지: '/api/api' → '/api'
    const res: any = await LinkApi.list({
      page: page.value,
      size: size.value,
      q: filters.q,
      status: filters.status,
    })
    rows.value = res.items || []
    total.value = res.total || 0
  } catch (e: any) {
    toast.error('목록을 불러올 수 없습니다.')
  } finally {
    loading.value = false
  }
}

// 필터 초기화
function resetFilters() {
  filters.q = ''
  filters.status = ''
  page.value = 1
  reload()
}

onMounted(reload)
</script>

<style scoped src="@/styles/toolbar.scss"></style>

<style scoped>
.page-shell {
  max-width: 1280px;
  margin: 0 auto;
}

/* SmartFilterBar 톤 통일 */
.brand-panel {
  background: rgb(var(--v-theme-surface));
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(16, 24, 40, 0.06);
  padding: 12px 16px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

/* 버튼 통일 */
.btn-action {
  font-weight: 600;
  min-width: 90px;
  height: 40px;
}

/* 테이블 헤더 */
:deep(.v-data-table__th) {
  white-space: nowrap;
  color: var(--color-muted);
  font-weight: 600;
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-line);
}
</style>
