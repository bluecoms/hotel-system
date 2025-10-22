<!-- ============================================================================
  File      : src/App.vue
  Version   : 2025.10-22 Final Stable (Property Sync · AppBar 개선)
  Purpose   : Hotel Admin — App Layout (Fullscreen/Login 대응 + Property 표시)
  ------------------------------------------------------------------------------
  목적:
    • 일반 페이지 → 상단바(AppBar) + 사이드바(SidebarNav) + 컨텐츠 유지
    • 로그인/전체화면 → 상단바/사이드바 제거, 전체화면 렌더링
    • 현재 선택된 지점(Property)을 상단바 우측에 표시

  주요 변경사항 (2025-10-22)
    ✅ Pinia Property Store 연동 (usePropertyStore)
    ✅ AppBar 우측에 지점 코드(MOP 등) 표시
    ✅ 로그인 페이지 등 fullscreen 라우트 분리
============================================================================ -->

<template>
  <v-app>
    <!-- ───────────── 일반 레이아웃 ───────────── -->
    <template v-if="!isFullscreen">
      <!-- 상단바(AppBar) -->
      <v-app-bar
        app
        color="primary"
        elevation="1"
        density="comfortable"
        class="appbar--brand"
        height="56"
      >
        <v-app-bar-nav-icon
          color="white"
          class="ml-2"
          @click="drawer = !drawer"
        />
        <v-app-bar-title class="text-white font-weight-bold d-flex align-center">
          <v-icon icon="mdi-hotel" size="18" class="mr-1" />
          호텔 관리자 시스템
        </v-app-bar-title>

        <!-- ✅ 현재 지점(Property) 표시 -->
        <v-chip
          v-if="property.current"
          class="mr-3 font-weight-medium"
          color="white"
          text-color="primary"
          variant="elevated"
          size="small"
          label
        >
          {{ property.current }} • Mokpo Ocean Hotel
        </v-chip>

        <v-spacer />
        <UserMenu class="mr-2" />
      </v-app-bar>

      <!-- 사이드바 -->
      <SidebarNav v-model="drawer" app width="260" />

      <!-- 메인(컨텐츠) -->
      <v-main app class="main-layout">
        <v-container fluid class="page-container">
          <router-view v-slot="{ Component }">
            <transition name="fade-fast" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </v-container>
      </v-main>
    </template>

    <!-- ───────────── 전체화면(로그인 등) ───────────── -->
    <template v-else>
      <v-main app class="main-layout page--fullscreen">
        <router-view v-slot="{ Component }">
          <transition name="fade-fast" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </v-main>
    </template>

    <!-- 공통 Host -->
    <ToastHost />
    <ConfirmHost />
  </v-app>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import ToastHost from '@/ui/components/common/ToastHost.vue'
import ConfirmHost from '@/ui/components/common/ConfirmHost.vue'
import UserMenu from '@/ui/components/layout/UserMenu.vue'
import SidebarNav from '@/ui/components/layout/SidebarNav.vue'
import { usePropertyStore } from '@/stores/property'

/* 상태 */
const drawer = ref(true)
const route = useRoute()
const property = usePropertyStore()

/**
 * 전체화면 여부:
 * - 라우트 메타 fullscreen === true
 * - 로그인 페이지(name === 'login')
 */
const isFullscreen = computed<boolean>(() => {
  return route.meta?.fullscreen === true || route.name === 'login'
})
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

/* 상단바 (브랜드 컬러 그라데이션) */
.appbar--brand {
  background: linear-gradient(90deg, var(--brand-primary), var(--brand-accent));
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}

/* 메인 컨테이너 */
.main-layout {
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-background));
  height: 100%;
  min-height: 100vh;
  overflow-y: auto;
}

/* 페이지 컨테이너(일반 페이지 전용) */
.page-container {
  padding: 24px 20px 40px;
  max-width: 1280px;
  margin: 0 auto;
  width: 100%;
}

/* 전체화면 전용 (로그인/특수 페이지) */
.page--fullscreen {
  padding: 0 !important;
  margin: 0 !important;
  min-height: 100vh;
  min-height: 100dvh;
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
