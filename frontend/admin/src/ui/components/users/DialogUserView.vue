<!-- =========================================================================
 File      : src/ui/components/users/DialogUserView.vue
 Version   : 2025.10-21 Final Stable
 Purpose   : Hotel Admin — 공용 사용자 상세보기 다이얼로그 (재사용 가능 컴포넌트)
----------------------------------------------------------------------------
 변경사항 (v2025.10-21)
   ✅ SSOT 규격 주석 통일 및 재사용 목적 명시
   ✅ 현재는 관리자용 사용자 관리(Users.vue)에서 사용 중
   ✅ 추후 다른 모듈(로그/인사 등)에서도 다이얼로그 형태로 재사용 가능
   ✅ BoardViewDialog 기반 — 로딩·에러·빈값 피드백 일관 유지
   ✅ SUPERADMIN 전용 “비밀번호 초기화” 버튼 포함
----------------------------------------------------------------------------
 구성:
   • 사용자 기본정보 (이름 / 이메일 / 권한 / 상태)
   • 생성·수정일 등 메타 표시
   • 네트워크 예외 시 명확한 경고 출력 및 재시도 버튼
   • 상위 컴포넌트에서 v-model / @update 로 개방형 제어 가능
----------------------------------------------------------------------------
 비고:
   • 페이지용(MyInfo.vue)과 달리 다이얼로그 형태로 언제든 import하여 호출 가능
   • 예: Users.vue, HR 기록 페이지 등에서 "사용자 상세보기" 팝업으로 사용
 ========================================================================= -->

<template>
  <BoardViewDialog
    v-model="open"
    title="사용자 상세보기"
    icon="mdi-account-outline"
    :item="user"
  >
    <template #content>
      <!-- 로딩 상태 -->
      <div v-if="loading" class="py-4">
        <v-skeleton-loader type="list-item-two-line" class="mb-2" />
        <v-skeleton-loader type="list-item-two-line" class="mb-2" />
        <v-skeleton-loader type="list-item-two-line" class="mb-2" />
        <v-skeleton-loader type="list-item-two-line" />
      </div>

      <!-- 에러 상태 -->
      <v-alert
        v-else-if="errorText"
        type="error"
        variant="tonal"
        border="start"
        class="mb-3"
      >
        {{ errorText }}
        <template #append>
          <v-btn size="small" variant="text" @click="retry">다시 시도</v-btn>
        </template>
      </v-alert>

      <!-- 정상/빈 데이터 -->
      <div v-else>
        <v-list density="compact">
          <!-- 이름 -->
          <v-list-item>
            <v-list-item-title class="font-weight-bold">이름</v-list-item-title>
            <v-list-item-subtitle class="d-flex align-center" style="gap:8px">
              <span>{{ user?.name || '—' }}</span>
              <v-btn
                v-if="user?.name"
                size="x-small"
                icon="mdi-content-copy"
                variant="text"
                @click="copy(user.name)"
                :title="'이름 복사'"
              />
            </v-list-item-subtitle>
          </v-list-item>

          <!-- 이메일 -->
          <v-list-item>
            <v-list-item-title class="font-weight-bold">이메일</v-list-item-title>
            <v-list-item-subtitle class="d-flex align-center flex-wrap" style="gap:8px">
              <span>{{ user?.email || '—' }}</span>
              <v-btn
                v-if="user?.email"
                size="x-small"
                icon="mdi-content-copy"
                variant="text"
                @click="copy(user.email)"
                :title="'이메일 복사'"
              />
              <v-btn
                v-if="user?.email"
                size="x-small"
                variant="text"
                prepend-icon="mdi-email-outline"
                :href="`mailto:${user.email}`"
              >메일</v-btn>
            </v-list-item-subtitle>
          </v-list-item>

          <!-- 권한 -->
          <v-list-item>
            <v-list-item-title class="font-weight-bold">권한</v-list-item-title>
            <v-list-item-subtitle>
              <div class="d-flex flex-wrap" style="gap:6px">
                <v-chip
                  v-for="r in (user?.roles || [])"
                  :key="r.code || r"
                  size="small"
                  variant="tonal"
                  color="primary"
                  label
                >
                  {{ r.name || r.code || r }}
                </v-chip>
                <span v-if="!user?.roles || user.roles.length === 0">—</span>
              </div>
            </v-list-item-subtitle>
          </v-list-item>

          <!-- 상태 -->
          <v-list-item>
            <v-list-item-title class="font-weight-bold">상태</v-list-item-title>
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

        <!-- 보조 정보 -->
        <div
          v-if="user?.created_at || user?.updated_at"
          class="mt-2 text-caption text-medium-emphasis"
        >
          <span v-if="user?.created_at">생성: {{ fmt(user.created_at) }}</span>
          <span v-if="user?.updated_at" class="ml-3">수정: {{ fmt(user.updated_at) }}</span>
        </div>

        <!-- SUPERADMIN 전용 버튼 -->
        <div class="mt-5 text-right" v-if="isSuperAdmin">
          <v-btn
            color="primary"
            variant="flat"
            prepend-icon="mdi-lock-reset"
            size="small"
            :to="`/admin/users/password-reset?uid=${user?.id || ''}`"
          >
            비밀번호 초기화
          </v-btn>
        </div>
      </div>
    </template>
  </BoardViewDialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import BoardViewDialog from '@/ui/components/common/BoardViewDialog.vue'
import * as UsersApi from '@/services/users'
import { useAuthStore } from '@/stores/auth'

// ─────────────────────────────────────────────
// v-model props
// ─────────────────────────────────────────────
const props = defineProps<{ modelValue: boolean; userId?: number }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: boolean): void }>()

const open = ref(props.modelValue)
const user = ref<any>(null)
const loading = ref(false)
const errorText = ref('')

// ─────────────────────────────────────────────
// 권한 체크 (SUPERADMIN만 초기화 버튼 표시)
// ─────────────────────────────────────────────
const auth = useAuthStore()
const isSuperAdmin = computed(() =>
  (auth.user?.roles || []).map((r: string) => r.toUpperCase()).includes('SUPERADMIN')
)

// ─────────────────────────────────────────────
// 다이얼로그 열릴 때마다 fetch
// ─────────────────────────────────────────────
watch(
  () => props.modelValue,
  async (v) => {
    open.value = v
    if (!v) return
    if (!props.userId) {
      user.value = null
      errorText.value = '대상 사용자가 지정되지 않았습니다.'
      return
    }
    await fetchUser()
  }
)

// 닫힘 propagate
watch(open, (v) => emit('update:modelValue', v))

async function fetchUser() {
  loading.value = true
  errorText.value = ''
  try {
    user.value = await UsersApi.get(props.userId as number)
  } catch (e: any) {
    errorText.value = '사용자 정보를 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
}

function retry() {
  if (props.userId) fetchUser()
}

function copy(text: string) {
  if (!text) return
  navigator.clipboard?.writeText(text).catch(() => {})
}

function fmt(v: string) {
  try {
    const d = new Date(v)
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    const hh = String(d.getHours()).padStart(2, '0')
    const mm = String(d.getMinutes()).padStart(2, '0')
    return `${y}-${m}-${day} ${hh}:${mm}`
  } catch {
    return v
  }
}
</script>
