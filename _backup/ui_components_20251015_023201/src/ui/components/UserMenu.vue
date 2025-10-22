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

const initials = computed(() => {
  const base = (auth.user?.name || auth.user?.email || '').trim()
  return base ? base[0].toUpperCase() : 'U'
})

const roleLabel = computed(() => {
  const roles = auth.user?.roles || []
  return roles.includes('SUPERADMIN') ? 'SUPERADMIN' : roles[0] || 'USER'
})

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

function logout() {
  try { auth.logout() } catch {}
  router.replace('/login')
}

function goMyPage() {
  router.push('/account/password').catch(() => {})
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
