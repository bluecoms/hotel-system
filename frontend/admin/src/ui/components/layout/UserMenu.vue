<!-- =========================================================================
 File      : src/ui/components/layout/UserMenu.vue
 Version   : 2025.10-20 Final Stable
 Purpose   : Hotel Admin — 상단 사용자 메뉴 (Avatar Menu)
----------------------------------------------------------------------------
 변경사항 (v2025.10-20)
   ✅ 내 정보 페이지 연결 경로 변경 (/account/password → /account/info)
   ✅ SSOT 헤더 규격 통일
   ✅ SUPERADMIN / ADMIN 역할명 표시 개선
   ✅ Vuetify v3 메뉴 정렬 및 색상 일관성 유지
----------------------------------------------------------------------------
 구성:
   • 아바타(이니셜) + 역할 표시
   • 내 정보 보기(→ /account/info)
   • 로그아웃 버튼
----------------------------------------------------------------------------
 동작:
   - 아바타 클릭 시 메뉴 열림 (Vuetify v-menu)
   - 내 정보 → /account/info
   - 로그아웃 → /login 으로 리다이렉트
 ========================================================================= -->
<template>
  <v-menu
    location="bottom end"
    :offset="8"
    :close-on-content-click="true"
    theme="light"
  >
    <template #activator="{ props }">
      <v-btn
        v-bind="props"
        variant="text"
        class="px-2 user-menu-btn"
        aria-label="계정 메뉴"
      >
        <v-avatar
          size="32"
          class="mr-2"
          title="계정"
          :style="avatarStyle"
        >
          <span :style="initialStyle">{{ initials }}</span>
        </v-avatar>

        <div class="d-flex flex-column align-start">
          <span class="user-role">{{ roleLabel }}</span>
        </div>
      </v-btn>
    </template>

    <v-card rounded="lg" elevation="10" min-width="180">
      <v-list density="comfortable" nav>
        <v-list-item
          prepend-icon="mdi-account"
          title="내 정보"
          @click="goMyPage"
        />
        <v-divider class="my-1" />
        <v-list-item
          prepend-icon="mdi-logout"
          title="로그아웃"
          class="text-error"
          @click="logout"
        />
      </v-list>
    </v-card>
  </v-menu>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

// ─────────────────────────────────────────────
// 사용자 이름/이메일에서 이니셜 생성
// ─────────────────────────────────────────────
const initials = computed(() => {
  const base = (auth.user?.name || auth.user?.email || '').trim()
  return base ? base[0].toUpperCase() : 'U'
})

// ─────────────────────────────────────────────
// 역할 라벨 계산
// ─────────────────────────────────────────────
const roleLabel = computed(() => {
  const roles = auth.user?.roles || []
  if (roles.includes('SUPERADMIN')) return 'SUPERADMIN'
  if (roles.includes('ADMIN')) return 'ADMIN'
  return roles[0] || 'USER'
})

// ─────────────────────────────────────────────
// 스타일 정의
// ─────────────────────────────────────────────
const avatarStyle = {
  background: '#fff',
  border: '2px solid rgba(255,255,255,0.85)',
}

const initialStyle = {
  display: 'inline-block',
  width: '100%',
  textAlign: 'center' as const,
  fontWeight: 800,
  fontSize: '14px',
  color: 'rgb(var(--v-theme-primary))',
}

// ─────────────────────────────────────────────
// 동작 함수
// ─────────────────────────────────────────────
function logout() {
  try { auth.logout() } catch {}
  router.replace('/login')
}

function goMyPage() {
  router.push('/account/info').catch(() => {})
}
</script>

<style scoped>
.user-menu-btn {
  margin-top: 2px;
  margin-right: 8px;
  color: white; /* 전체 버튼 내 텍스트 흰색 */
}

.user-role {
  font-size: 14px;
  color: white;
  opacity: 0.9;
  font-weight: 500;
}

.v-overlay__content {
  margin-top: 6px !important;
}
</style>
