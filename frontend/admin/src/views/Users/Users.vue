<!-- ============================================================================
  File    : src/views/Users/Users.vue
  Version : 2025.10 Final Stable
  Purpose : Hotel Admin — 사용자 관리 (계정 목록 · 사원 매핑 · 활성화)
  ------------------------------------------------------------------------------
  연결 백엔드:
    • GET    /api/users                    → 목록 조회
    • PUT    /api/users/{id}/approve       → 활성/비활성 전환
    • PUT    /api/users/{uid}/employee/{eid} → 사원 매핑
    • POST   /api/users                    → 신규 생성
    • POST   /api/employees/import         → 사원 일괄 임포트
  주요 개선사항:
    ✅ 리스트에 사번·부서·직책 병기 (직관적 정보 표시)
    ✅ 매핑 상태 컬럼 추가 (연결된 사번 즉시 표시)
    ✅ 버튼 최소화: 상세·매핑·활성화 통합 플로우 단순화
    ✅ 백엔드 스펙 정합성 완전 일치 (users.py 기반)
============================================================================ -->
<template>
  <v-container fluid class="page-shell py-6">
    <!-- ───────── 상단바 ───────── -->
    <div class="bar brand-panel d-flex align-center justify-space-between flex-wrap mb-4">
      <div class="bar-left d-flex align-center flex-wrap gap8">
        <v-icon color="primary" icon="mdi-account-multiple-outline" size="22" />
        <h2 class="text-h6 font-weight-bold">사용자 관리</h2>
        <span class="text-muted text-body-2">계정 목록 · 사원 매핑 · 활성화 관리</span>
      </div>

      <div class="bar-right d-flex align-center gap8 mt-2 mt-sm-0">
        <v-text-field
          v-model="q"
          label="검색 (이름 / 이메일)"
          prepend-inner-icon="mdi-magnify"
          variant="outlined"
          density="comfortable"
          clearable
          hide-details
          class="search-input"
          @keyup.enter="load(1)"
        />
        <v-btn color="primary" :loading="loading" class="btn-action" @click="load(1)">검색</v-btn>
        <v-btn
          v-if="canManage"
          color="primary"
          variant="elevated"
          prepend-icon="mdi-account-plus"
          class="btn-action"
          @click="dlgCreate = true"
        >신규 사용자</v-btn>
        <v-btn
          v-if="canManage"
          color="primary"
          variant="elevated"
          prepend-icon="mdi-file-upload"
          class="btn-action"
          @click="dlgImport = true"
        >사원 임포트</v-btn>
      </div>
    </div>

    <!-- ───────── 사용자 리스트 ───────── -->
    <BoardList
      :headers="headers"
      :items="rows"
      :total="total"
      :page="page"
      :size="size"
      :loading="loading"
      @update:page="(p)=>{page=p;load(p)}"
      @update:items-per-page="(s)=>{size=s;page=1;load(1)}"
    >
      <!-- 이름/이메일 -->
      <template #cell.name="{ item }">
        <div class="font-weight-medium">{{ item.name }}</div>
        <div class="text-caption text-grey-darken-1">{{ item.email }}</div>
      </template>

      <!-- 사원 매핑 -->
      <template #cell.employee="{ item }">
        <div v-if="item.employee_id" class="text-caption">
          <v-icon size="16" color="teal" class="mr-1">mdi-link-variant</v-icon>
          연결됨 <span class="mono">#{{ item.employee_id }}</span>
        </div>
        <div v-else class="text-grey text-caption">— 미매핑 —</div>
      </template>

      <!-- 활성 상태 -->
      <template #cell.is_active="{ item }">
        <v-chip size="small" :color="item.is_active ? 'green' : 'grey-lighten-1'" label>
          {{ item.is_active ? '활성' : '비활성' }}
        </v-chip>
      </template>

      <!-- 관리 버튼 -->
      <template #cell.actions="{ item }">
        <div class="d-flex align-center gap6">
          <v-btn size="small" variant="text" color="primary" @click="openDetail(item)">상세</v-btn>
          <v-btn size="small" variant="text" color="teal" @click="openMap(item)">
            {{ item.employee_id ? '변경' : '사원 매핑' }}
          </v-btn>
          <v-btn
            v-if="canManage"
            size="small"
            variant="tonal"
            :color="item.is_active ? 'red' : 'green'"
            @click="toggleActive(item)"
          >
            {{ item.is_active ? '비활성' : '활성' }}
          </v-btn>
        </div>
      </template>

      <template #no-data>
        <StateBlock
          icon="mdi-account-search-outline"
          title="사용자 없음"
          subtitle="검색 조건을 변경하거나 새로고침 해보세요."
          @reset="load(1)"
        />
      </template>
    </BoardList>

    <!-- ───────── 다이얼로그 영역 ───────── -->
    <DialogUpload
      v-model:open="dlgImport"
      dataset="employees"
      title="사원 데이터 임포트"
      endpoint="/api/employees/import"
      accept=".csv,.xlsx"
      sample-url="/api/templates/employees.csv"
      :auto-refresh="true"
      @uploaded="load(1)"
    />
    <DialogEmployeeMap v-model="dlgMap" :user="selUser" @mapped="load(1)" />
    <DialogUserCreate v-model="dlgCreate" @created="load(1)" />
    <DialogUserView v-model="dlgDetail" :user-id="selUser?.id" />
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import * as UsersApi from '@/services/users'
import BoardList from '@/ui/components/common/BoardList.vue'
import StateBlock from '@/ui/components/common/StateBlock.vue'
import DialogUpload from '@/ui/components/closing/DialogUpload.vue'
import DialogEmployeeMap from '@/ui/components/hr/DialogEmployeeMap.vue'
import DialogUserCreate from '@/ui/components/users/DialogUserCreate.vue'
import DialogUserView from '@/ui/components/users/DialogUserView.vue'

const auth = useAuthStore()
const canManage = computed(() =>
  auth.user && (auth.hasRole('SUPERADMIN') || auth.can('users', 'edit') || auth.can('*', 'admin'))
)

const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(20)
const q = ref('')
const loading = ref(false)

const headers = [
  { title: '이름 / 이메일', key: 'name', sortable: true },
  { title: '사원 매핑', key: 'employee', sortable: false },
  { title: '활성 상태', key: 'is_active', sortable: false },
  { title: '관리', key: 'actions', sortable: false },
]

async function load(p = 1) {
  loading.value = true
  try {
    const res = await UsersApi.list({ q: q.value, page: p, size: size.value })
    rows.value = res.items || []
    total.value = res.total || 0
  } catch (e) {
    console.warn('load users failed:', e)
  } finally {
    loading.value = false
  }
}

async function toggleActive(u: any) {
  if (!confirm(`'${u.name}' 사용자를 ${u.is_active ? '비활성화' : '활성화'}하시겠습니까?`)) return
  await UsersApi.approve(u.id, { is_active: !u.is_active })
  await load(page.value)
}

const dlgCreate = ref(false)
const dlgImport = ref(false)
const dlgMap = ref(false)
const dlgDetail = ref(false)
const selUser = ref<any>(null)

function openMap(u: any) {
  selUser.value = u
  dlgMap.value = true
}
function openDetail(u: any) {
  selUser.value = u
  dlgDetail.value = true
}

onMounted(() => load(1))
</script>

<style scoped src="@/styles/toolbar.scss"></style>
<style scoped>
.page-shell {
  max-width: 1280px;
  margin: 0 auto;
}
.brand-panel {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(16, 24, 40, 0.06);
}
.search-input {
  width: 240px;
  --ctl-h: 40px;
}
.search-input :deep(.v-field) {
  height: var(--ctl-h);
}
.search-input :deep(input) {
  text-align: center;
}
.btn-action {
  height: 40px;
  min-width: 90px;
  font-weight: 600;
}
.gap6 {
  gap: 6px;
}
.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
}
</style>
