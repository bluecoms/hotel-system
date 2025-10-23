<!-- ============================================================================
# VIEW: HR-USER-DETAIL
# File    : src/views/Admin/HR/UserDetail.vue
# Version : 2025.10-28 · v2.0.1 (Hotfix · Master API 인자 제거 · 주석정리)
# Purpose : 사용자 상세/편집 화면 (프로필 단일 뷰, 계약은 별도 화면으로 이동)
# ----------------------------------------------------------------------------
# 변경 요약 (v2.0.1)
#   ✅ TS2554 해결: MasterApi.departmentOptions({}) → MasterApi.departmentOptions()
#   ✅ Master API 호출 주석 정리 (departmentOptions / positionOptions)
#   ✅ 전체 주석/가독성 정리 및 정책(axios금지) 강조
# ----------------------------------------------------------------------------
# 연계
#   • GET  /api/users/{id}              → 사용자 로드 (users.py)
#   • PUT  /api/users/{id}              → 사용자 수정 (허용 필드만 보냄)
#   • GET  /api/master/departments/...  → 부서 옵션 (departmentOptions)
#   • GET  /api/master/positions/...    → 직위 옵션 (positionOptions)
#   • 계약 관리 이동: /admin/hr/contracts (employee_id 있을 때 필터를 쿼리로 전달)
# ----------------------------------------------------------------------------
# 주의
#   • fetch 기반 http.ts 사용(axios 금지)
#   • 역할(Role) 코드는 항상 대문자 (SUPERADMIN, ADMIN 등)
# ============================================================================ -->
<template>
  <v-container fluid class="page-shell py-6">
    <!-- ───────────── 상단 바 ───────────── -->
    <div class="bar brand-panel d-flex align-center justify-space-between flex-wrap mb-4">
      <div class="bar-left d-flex align-center flex-wrap gap8">
        <v-icon color="primary" icon="mdi-account-circle-outline" size="22" />
        <div class="d-flex flex-column">
          <h2 class="text-h6 font-weight-bold mb-0">{{ user?.name || '사용자 상세' }}</h2>
          <span class="text-muted text-body-2">{{ user?.email || '-' }}</span>
        </div>
      </div>

      <!-- 우측 상태/버튼 영역 -->
      <div class="bar-right d-flex align-center gap8 mt-2 mt-sm-0">
        <v-chip
          size="small"
          :color="user?.is_active ? 'green' : 'grey-lighten-1'"
          :text-color="user?.is_active ? 'white' : 'grey-darken-1'"
          label
        >
          {{ user?.is_active ? '활성' : '비활성' }}
        </v-chip>

        <v-btn variant="outlined" color="primary" prepend-icon="mdi-arrow-left" @click="router.push('/admin/users')">
          목록으로
        </v-btn>

        <v-btn
          v-if="user?.employee_id"
          color="primary"
          prepend-icon="mdi-file-sign"
          variant="flat"
          @click="goContracts"
        >
          계약 관리로
        </v-btn>
      </div>
    </div>

    <!-- ───────────── 프로필 카드 ───────────── -->
    <v-card class="rounded-xl elevation-1">
      <v-card-text class="pa-6">
        <!-- 상단 요약 -->
        <v-alert v-if="user" type="info" variant="tonal" border="start" class="mb-4">
          <div class="d-flex align-center flex-wrap gap8">
            <v-icon icon="mdi-badge-account" start />
            <div class="text-body-2">
              <strong>{{ user.name }}</strong>
              <span class="text-grey-darken-1 ml-2">{{ user.email }}</span>
              <v-chip
                v-for="r in (user.roles || [])"
                :key="r"
                size="x-small"
                class="ml-2"
                color="blue-grey"
                label
              >
                {{ r }}
              </v-chip>
              <v-chip
                v-if="user.employee_id"
                size="x-small"
                class="ml-2"
                color="teal"
                label
              >
                직원ID: {{ user.employee_id }}
              </v-chip>
            </div>
          </div>
        </v-alert>

        <!-- 프로필 폼 -->
        <v-form ref="formRef" @submit.prevent="saveProfile" class="py-3">
          <v-row dense>
            <v-col cols="12" md="4">
              <v-text-field v-model.trim="form.name" label="이름" :rules="[req]" hide-details="auto" />
            </v-col>

            <v-col cols="12" md="4">
              <v-text-field
                v-model.trim="form.email"
                label="이메일"
                type="email"
                :rules="[emailRule]"
                hide-details="auto"
              />
            </v-col>

            <!-- 역할: 다중 선택 -->
            <v-col cols="12" md="4">
              <v-select v-model="form.roles" :items="roleItems" label="역할(Role)" multiple chips hide-details="auto" />
            </v-col>

            <!-- 부서 선택 -->
            <v-col cols="12" md="6">
              <v-select
                v-model="form.department"
                :items="deptOptions"
                item-title="title"
                item-value="value"
                label="부서"
                clearable
                hide-details="auto"
              />
            </v-col>

            <!-- 직위 선택 -->
            <v-col cols="12" md="6">
              <v-select
                v-model="form.position"
                :items="positionOptions"
                item-title="title"
                item-value="value"
                label="직위"
                clearable
                hide-details="auto"
              />
            </v-col>

            <v-col cols="12">
              <v-textarea v-model.trim="form.memo" label="메모" rows="3" hide-details="auto" />
            </v-col>
          </v-row>

          <div class="d-flex justify-end mt-4 gap8">
            <v-btn variant="text" @click="router.push('/admin/users')">취소</v-btn>
            <v-btn color="primary" :loading="saving" @click="saveProfile">저장</v-btn>
          </div>
        </v-form>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
/* ===========================================================================
# Script — HR User Detail (프로필 단일 뷰)
# 흐름:
#   1) route.params.id 로 사용자 로드 (/api/users/{id})
#   2) Master 부서/직위 옵션 로드 → v-select에 바인딩
#   3) 저장 시 허용 필드만 PUT (name, email, roles, department, position, memo)
#   4) 직원 매핑이 있을 경우 '계약 관리' 화면으로 이동 버튼 제공
# ---------------------------------------------------------------------------
# 정책:
#   • axios 금지, fetch 기반 http.ts만 사용
#   • roles는 항상 대문자 코드 (SUPERADMIN, ADMIN 등)
=========================================================================== */
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import http from '@/services/http'
import { useToast } from '@/ui/composables/useToast'
import * as MasterApi from '@/services/master'

const route = useRoute()
const router = useRouter()
const { success, error } = useToast()

/** 파라미터/상태 */
const userId = Number(route.params.id)
const user = ref<any>(null)
const formRef = ref()
const saving = ref(false)

/** 폼 상태 */
const form = ref<any>({
  name: '',
  email: '',
  roles: [] as string[],
  department: '',
  position: '',
  memo: '',
})

/** 역할 코드 (대문자) */
const roleItems = ['SUPERADMIN', 'ADMIN', 'FRONT', 'HK', 'FNB']

/** Master 옵션 (부서/직위) */
const deptOptions = ref<Array<{ title: string; value: string }>>([])
const positionOptions = ref<Array<{ title: string; value: string }>>([])

/** 검증 규칙 */
const req = (v: any) => !!String(v ?? '').trim() || '필수 항목입니다.'
const emailRule = (v: any) => {
  const s = String(v ?? '').trim()
  if (!s) return true
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s) || '이메일 형식이 올바르지 않습니다.'
}

/** 사용자 로드 */
async function loadUser() {
  try {
    const r = await http.get<any>(`/users/${userId}`)
    user.value = r
    const rolesArray = Array.isArray(r?.roles) ? r.roles : (r?.roles ? [r.roles] : [])
    Object.assign(form.value, {
      name: r?.name ?? '',
      email: r?.email ?? '',
      roles: rolesArray.map((x: any) => String(x).toUpperCase()),
      department: r?.department ?? '',
      position: r?.position ?? '',
      memo: r?.memo ?? '',
    })
  } catch {
    error('사용자 정보를 불러오지 못했습니다.')
  }
}

/** Master 옵션 로드
 * Hotfix: departmentOptions() 인자 제거 (TS2554 해결)
 */
async function loadMasters() {
  try {
    const deptRes = await MasterApi.departmentOptions() // ✅ 인자 제거
    deptOptions.value = Array.isArray(deptRes) ? deptRes : (deptRes?.items ?? [])
  } catch {
    deptOptions.value = []
  }

  try {
    const pos = (await (MasterApi as any).positionOptions?.()) || []
    positionOptions.value = Array.isArray(pos) ? pos : (pos?.items ?? [])
  } catch {
    positionOptions.value = []
  }
}

/** 저장 */
async function saveProfile() {
  const ok =
    (formRef.value as any)?.validate
      ? await (formRef.value as any).validate()
      : { valid: true }
  if (ok?.valid === false) return

  if (form.value.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.value.email)) {
    error('이메일 형식이 올바르지 않습니다.')
    return
  }

  try {
    saving.value = true
    const payload = {
      name: form.value.name,
      email: form.value.email,
      roles: (form.value.roles || []).map((x: any) => String(x).toUpperCase()),
      department: form.value.department || null,
      position: form.value.position || null,
      memo: form.value.memo || '',
    }
    await http.put(`/users/${userId}`, payload)
    success('저장되었습니다.')
    await loadUser()
  } catch {
    error('저장 실패')
  } finally {
    saving.value = false
  }
}

/** 계약 관리 화면으로 이동 */
function goContracts() {
  const eid = user.value?.employee_id
  if (!eid) return
  router.push({ name: 'admin-hr-contracts', query: { employee_id: String(eid) } })
}

/** 초기 로드 */
onMounted(async () => {
  await Promise.all([loadUser(), loadMasters()])
})
</script>

<style scoped src="@/styles/toolbar.scss"></style>

<style scoped>
.page-shell {
  max-width: 1280px;
  margin: 0 auto;
}
</style>
