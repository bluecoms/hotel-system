<!-- src/App.vue -->
<template>
  <v-app>
    <!-- 상단바 -->
    <v-app-bar
      v-if="!isLoginPage"
      app
      color="primary"
      elevation="1"
      density="comfortable"
      class="appbar--brand"
      height="56"
    >
      <v-app-bar-nav-icon color="white" class="ml-2" @click="drawer = !drawer" />
      <v-app-bar-title class="text-white font-weight-bold">
        <v-icon icon="mdi-hotel" size="18" class="mr-1" />
        호텔 관리자 시스템
      </v-app-bar-title>
      <v-spacer />
      <UserMenu class="mr-2" />
    </v-app-bar>

    <!-- 사이드바 -->
    <SidebarNav v-if="!isLoginPage" v-model="drawer" app width="260" />

    <!-- 메인 -->
    <v-main app class="main-layout">
      <v-container fluid class="page-container">
        <router-view v-slot="{ Component }">
          <transition name="fade-fast" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </v-container>
    </v-main>

    <ToastHost />
    <ConfirmHost />
  </v-app>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import ToastHost from '@/ui/components/ToastHost.vue'
import ConfirmHost from '@/ui/components/ConfirmHost.vue'
import UserMenu from '@/ui/components/UserMenu.vue'
import SidebarNav from '@/ui/components/layout/SidebarNav.vue'

const drawer = ref(true)
const route = useRoute()
const isLoginPage = computed(() => route.name === 'login')
</script>

<style>
html,
body,
#app {
  height: 100%;
  background: rgb(var(--v-theme-background));
  font-family: var(--app-font, 'Inter', 'Noto Sans KR', sans-serif);
  overflow-x: hidden;
}

/* 상단바 */
.appbar--brand {
  background: linear-gradient(90deg, var(--brand-primary), var(--brand-accent));
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}

/* 메인 */
.main-layout {
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-background));
  height: 100%;
  min-height: 100vh;
  overflow-y: auto;
}

/* 페이지 컨테이너 */
.page-container {
  padding: 24px 20px 40px;
  max-width: 1280px;
  margin: 0 auto;
  width: 100%;
}

/* 로그인 전용 */
.login-bg {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e0eaff, #f8fafc);
}

/* 전환 효과 */
.fade-fast-enter-active,
.fade-fast-leave-active {
  transition: opacity 0.15s ease;
}
.fade-fast-enter-from,
.fade-fast-leave-to {
  opacity: 0;
}
</style>
