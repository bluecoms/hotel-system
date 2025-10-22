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
        <v-btn color="primary" :loading="loading" class="btn-action" @click="load(1)">
          검색
        </v-btn>

        <v-btn
          v-if="auth._effectiveLoaded && canManage"
          color="primary"
          variant="elevated"
          prepend-icon="mdi-account-plus"
          class="btn-action"
          @click="openCreate"
        >
          신규 사용자
        </v-btn>

        <v-btn
          v-if="auth._effectiveLoaded && canManage"
          color="primary"
          variant="elevated"
          prepend-icon="mdi-file-upload"
          class="btn-action"
          @click="openImport"
        >
          사원 임포트
        </v-btn>
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
      <template #cell.name="{ item }">
        <div class="font-weight-medium">{{ item.name }}</div>
        <div class="text-caption text-grey-darken-1">{{ item.email }}</div>
      </template>

      <template #cell.is_active="{ item }">
        <v-chip
          size="small"
          :color="item.is_active ? 'green' : 'grey-lighten-1'"
          :text-color="item.is_active ? 'white' : 'grey-darken-1'"
          label
        >
          {{ item.is_active ? '활성' : '비활성' }}
        </v-chip>
      </template>

      <template #cell.actions="{ item }">
        <div class="d-flex align-center" style="gap:6px">
          <v-btn size="small" variant="text" color="primary" @click="goDetail(item)">
            상세보기
          </v-btn>
          <v-btn size="small" variant="text" color="teal" @click="openMap(item)">
            사원 매핑
          </v-btn>
          <v-btn
            v-if="canManage && item.is_active"
            size="small"
            color="red"
            variant="tonal"
            @click="deactivate(item)"
          >
            비활성
          </v-btn>
          <v-btn
            v-if="canManage && !item.is_active"
            size="small"
            color="green"
            variant="tonal"
            @click="activate(item)"
          >
            활성
          </v-btn>
        </div>
      </template>

      <template #no-data>
        <NoDataBox
          icon="mdi-account-search-outline"
          title="사용자 없음"
          subtitle="검색 조건을 변경하거나 새로고침 해보세요."
          @reset="load(1)"
        />
      </template>
    </BoardList>

    <!-- ───────── 다이얼로그 영역 ───────── -->

    <!-- ✅ DialogUpload: 필수 props 보강 -->
    <DialogUpload
      v-model:open="dlgImport"
      dataset="employees"
      biz-date=""
      property-code="MOP"
      title="사원 데이터 임포트"
      endpoint="/api/employees/import"
      accept=".csv,.xlsx"
      sample-url="/api/templates/employees.csv"
      :auto-refresh="true"
      @uploaded="load(1)"
    />

    <!-- ✅ DialogMapUser: propertyCode 명시 -->
    <DialogMapUser
      v-model:open="dlgMap"
      :user="selUser"
      property-code="MOP"
      @mapped="load(1)"
    />

    <!-- ✅ DialogUserCreate: 최신 v-model:open 구조 -->
    <DialogUserCreate
      v-model:open="dlgCreate"
      @created="load(1)"
    />
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import * as UsersApi from '@/services/users'

// UI 컴포넌트
import BoardList from '@/ui/components/BoardList.vue'
import NoDataBox from '@/ui/components/NoDataBox.vue'
import DialogUpload from '@/ui/components/DialogUpload.vue'
import DialogMapUser from '@/ui/components/DialogLinkAccount.vue'
import DialogUserCreate from '@/ui/components/DialogUserCreate.vue'

const auth = useAuthStore()
const router = useRouter()

// ✅ 권한 계산
const canManage = computed(() => {
  if (!auth.user) return false
  return (
    auth.hasRole('SUPERADMIN') ||
    auth.can('users', 'edit') ||
    auth.can('*', 'admin')
  )
})

// ✅ 리스트 관련 상태
const rows = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(20)
const q = ref('')
const loading = ref(false)

const headers = [
  { title: '이름 / 이메일', key: 'name', sortable: true },
  { title: '활성 상태', key: 'is_active', sortable: false },
  { title: '관리', key: 'actions', sortable: false },
]

// ✅ 데이터 로딩
async function load(p = 1) {
  loading.value = true
  try {
    const res: any = await UsersApi.list({ q: q.value, page: p, size: size.value })
    rows.value = res.items || []
    total.value = res.total || 0
  } catch {
    rows.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}
onMounted(() => load(1))

// ✅ 활성/비활성
async function deactivate(u: any) {
  if (!confirm(`'${u.name}' 사용자를 비활성화하시겠습니까?`)) return
  await UsersApi.deactivate(u.id)
  await load(page.value)
}
async function activate(u: any) {
  await UsersApi.activate(u.id)
  await load(page.value)
}

// ✅ 다이얼로그 상태
const dlgCreate = ref(false)
const dlgImport = ref(false)
const dlgMap = ref(false)
const selUser = ref<any>(null)

// ✅ 오픈 핸들러
function openCreate() { dlgCreate.value = true }
function openImport() { dlgImport.value = true }
function openMap(u: any) {
  selUser.value = u
  dlgMap.value = true
}
function goDetail(item: any) {
  router.push(`/admin/hr/users/${item.id}`)
}
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
.search-input :deep(.v-field) { height: var(--ctl-h); }
.search-input :deep(input) { text-align: center; }
.btn-action { height: 40px; min-width: 90px; font-weight: 600; }
</style>
