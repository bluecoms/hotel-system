<!-- =========================================================================
 File      : src/views/Users/MyInfo.vue
 Version   : 2025.10-22 Final Stable
 Purpose   : Hotel Admin — 내 정보 페이지 (계정정보 + 인사정보 + 비밀번호 변경 통합)
----------------------------------------------------------------------------
 변경사항 (v2025.10-22)
   ✅ 계정정보 + 인사정보(Employee) + 비밀번호 변경 3단 구조 통합
   ✅ /api/employees/me 연동 (부서·직급·전화·주소 등 표시)
   ✅ 강도 게이지, CapsLock 감지, 토스트/확인 UX 유지
----------------------------------------------------------------------------
 구성:
   • ① 계정 정보 (auth.user 기반)
   • ② 인사 정보 (employees/me API)
   • ③ 비밀번호 변경 폼
   • 단일 페이지 — /account/info
 ========================================================================= -->
<template>
  <v-container class="py-8" style="max-width: 820px;">
    <!-- ───────── 계정 정보 ───────── -->
    <h2 class="text-h6 font-weight-bold mb-4">내 정보</h2>

    <v-card class="pa-4 mb-8">
      <h3 class="text-subtitle-1 font-weight-bold mb-3">계정 정보</h3>
      <v-list density="comfortable">
        <v-list-item>
          <v-list-item-title>이름</v-list-item-title>
          <v-list-item-subtitle>{{ user?.name || '—' }}</v-list-item-subtitle>
        </v-list-item>
        <v-list-item>
          <v-list-item-title>이메일</v-list-item-title>
          <v-list-item-subtitle>{{ user?.email || '—' }}</v-list-item-subtitle>
        </v-list-item>
        <v-list-item>
          <v-list-item-title>역할(Role)</v-list-item-title>
          <v-list-item-subtitle>
            <v-chip
              v-for="r in (user?.roles || [])"
              :key="r"
              color="primary"
              variant="tonal"
              size="small"
              class="mr-1"
              label
            >
              {{ r }}
            </v-chip>
            <span v-if="!user?.roles?.length">—</span>
          </v-list-item-subtitle>
        </v-list-item>
        <v-list-item>
          <v-list-item-title>상태</v-list-item-title>
          <v-list-item-subtitle>
            <v-chip
              size="small"
              :color="user?.is_active ? 'green' : 'grey-lighten-1'"
              label
            >
              {{ user?.is_active ? '활성' : '비활성' }}
            </v-chip>
          </v-list-item-subtitle>
        </v-list-item>
      </v-list>
    </v-card>

    <!-- ───────── 인사 정보(Employee) ───────── -->
    <v-card v-if="employee" class="pa-4 mb-8">
      <h3 class="text-subtitle-1 font-weight-bold mb-3">인사 정보</h3>
      <v-list density="comfortable">
        <v-list-item>
          <v-list-item-title>사번</v-list-item-title>
          <v-list-item-subtitle>{{ employee.emp_no || '—' }}</v-list-item-subtitle>
        </v-list-item>
        <v-list-item>
          <v-list-item-title>부서</v-list-item-title>
          <v-list-item-subtitle>{{ employee.dept || '—' }}</v-list-item-subtitle>
        </v-list-item>
        <v-list-item>
          <v-list-item-title>직급 / 직책</v-list-item-title>
          <v-list-item-subtitle>{{ employee.title_name || employee.title || '—' }}</v-list-item-subtitle>
        </v-list-item>
        <v-list-item>
          <v-list-item-title>전화번호</v-list-item-title>
          <v-list-item-subtitle>{{ employee.phone || '—' }}</v-list-item-subtitle>
        </v-list-item>
        <v-list-item>
          <v-list-item-title>주소</v-list-item-title>
          <v-list-item-subtitle>{{ employee.address || '—' }}</v-list-item-subtitle>
        </v-list-item>
        <v-list-item>
          <v-list-item-title>은행 / 계좌</v-list-item-title>
          <v-list-item-subtitle>
            {{ employee.bank_name || '—' }}
            <span v-if="employee.account_mask">({{ employee.account_mask }})</span>
          </v-list-item-subtitle>
        </v-list-item>
        <v-list-item>
          <v-list-item-title>생년월일</v-list-item-title>
          <v-list-item-subtitle>{{ employee.birth_date || '—' }}</v-list-item-subtitle>
        </v-list-item>
      </v-list>
    </v-card>

    <v-alert
      v-else
      type="warning"
      variant="tonal"
      border="start"
      class="mb-8"
    >
      인사 정보(Employee) 데이터를 불러올 수 없습니다.
    </v-alert>

    <!-- ───────── 비밀번호 변경 ───────── -->
    <div class="d-flex align-center justify-space-between mb-4">
      <h3 class="text-subtitle-1 font-weight-bold">비밀번호 변경</h3>
      <v-btn color="secondary" variant="text" size="small" @click="clearForm">
        입력 초기화
      </v-btn>
    </div>

    <v-alert type="info" variant="tonal" class="mb-6">
      <div>현재 비밀번호를 입력하고 새 비밀번호를 설정하세요.</div>
      <div class="text-caption">
        비밀번호는 <strong>8자 이상</strong>이어야 하며 영문+숫자 조합을 권장합니다.
      </div>
    </v-alert>

    <v-text-field
      v-model="current"
      label="현재 비밀번호"
      :type="showCur ? 'text' : 'password'"
      variant="outlined"
      density="comfortable"
      hide-details="auto"
      color="primary"
      class="mb-3"
      :append-inner-icon="showCur ? 'mdi-eye-off' : 'mdi-eye'"
      @click:append-inner="showCur = !showCur"
      @keyup.enter="focusNext('next1')"
      ref="curInput"
      @keyup="checkCaps($event)"
    />

    <v-text-field
      v-model="next1"
      label="새 비밀번호"
      :type="showNew ? 'text' : 'password'"
      variant="outlined"
      density="comfortable"
      hide-details="auto"
      color="primary"
      class="mb-3"
      :append-inner-icon="showNew ? 'mdi-eye-off' : 'mdi-eye'"
      @click:append-inner="showNew = !showNew"
      ref="nextInput1"
      @keyup.enter="focusNext('next2')"
      @keyup="checkCaps($event)"
    />

    <v-text-field
      v-model="next2"
      label="새 비밀번호 확인"
      :type="showNew ? 'text' : 'password'"
      variant="outlined"
      density="comfortable"
      hide-details="auto"
      color="primary"
      ref="nextInput2"
      @keyup.enter="submit"
    />

    <v-alert
      v-if="capsOn"
      type="warning"
      variant="tonal"
      density="comfortable"
      class="mt-2 mb-3"
    >
      Caps Lock이 켜져 있습니다.
    </v-alert>

    <v-progress-linear
      v-if="next1"
      :model-value="strength"
      :color="strengthColor"
      height="6"
      rounded
      class="mt-2 mb-5"
    />

    <v-btn
      color="primary"
      size="large"
      :loading="loading"
      :disabled="disabled"
      block
      class="font-weight-bold"
      @click="submit"
    >
      비밀번호 변경
    </v-btn>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import http from '@/services/http'
import { useAuthStore } from '@/stores/auth'
import { changePassword } from '@/services/auth'
import { useToast } from '@/ui/composables/useToast'
import { useConfirm } from '@/ui/composables/useConfirm'

const auth = useAuthStore()
const toast = useToast()
const confirmApi = useConfirm()

const user = auth.user
const employee = ref<any>(null)

// ─────────────────────────────
// 인사정보 로드
// ─────────────────────────────
async function loadEmployee() {
  try {
    employee.value = await http.get('/employees/me')
  } catch (e) {
    employee.value = null
    console.warn('직원 정보 불러오기 실패:', e)
  }
}

onMounted(() => loadEmployee())

// ─────────────────────────────
// 비밀번호 변경 섹션
// ─────────────────────────────
const current = ref('')
const next1 = ref('')
const next2 = ref('')
const showCur = ref(false)
const showNew = ref(false)
const loading = ref(false)
const capsOn = ref(false)
const curInput = ref<HTMLInputElement>()
const nextInput1 = ref<HTMLInputElement>()
const nextInput2 = ref<HTMLInputElement>()

function checkCaps(e: KeyboardEvent) {
  const caps = e.getModifierState && e.getModifierState('CapsLock')
  capsOn.value = !!caps
}

function focusNext(refName: string) {
  if (refName === 'next1') nextTick(() => nextInput1.value?.focus())
  else if (refName === 'next2') nextTick(() => nextInput2.value?.focus())
}

const strength = computed(() => {
  if (!next1.value) return 0
  let s = 0
  if (next1.value.length >= 8) s += 30
  if (/[A-Z]/.test(next1.value)) s += 20
  if (/[0-9]/.test(next1.value)) s += 25
  if (/[^A-Za-z0-9]/.test(next1.value)) s += 25
  return Math.min(s, 100)
})
const strengthColor = computed(() => {
  if (strength.value < 40) return 'error'
  if (strength.value < 70) return 'warning'
  return 'success'
})

const disabled = computed(
  () =>
    !current.value ||
    !next1.value ||
    next1.value !== next2.value ||
    next1.value.length < 8
)

function clearForm() {
  current.value = ''
  next1.value = ''
  next2.value = ''
  capsOn.value = false
}

async function submit() {
  if (disabled.value) {
    toast.info('입력값을 확인하세요.')
    return
  }
  const ok = await confirmApi.ask('비밀번호를 변경하시겠습니까?', {
    title: '비밀번호 변경 확인',
    okText: '변경',
    cancelText: '취소',
  })
  if (!ok) return

  loading.value = true
  try {
    await changePassword(current.value, next1.value)
    toast.success('비밀번호가 변경되었습니다.')
    clearForm()
  } catch (e: any) {
    toast.error(e?.message || '비밀번호 변경에 실패했습니다.')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.v-card {
  border-radius: 12px;
}
.v-btn {
  font-weight: 600;
  letter-spacing: 0.3px;
}
.v-alert {
  border-radius: 12px;
}
</style>
