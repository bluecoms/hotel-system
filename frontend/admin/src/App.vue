<template>
  <v-app>
    <v-app-bar flat color="primary">
      <v-app-bar-nav-icon @click="drawer = !drawer" />
      <v-app-bar-title>Hotel Admin</v-app-bar-title>
      <v-spacer />
      <v-menu>
        <template #activator="{ props }">
          <v-btn v-bind="props" variant="text" prepend-icon="mdi-account">
            {{ auth.user?.name ?? 'Admin' }}
          </v-btn>
        </template>
        <v-list>
          <v-list-item @click="logout">
            <v-list-item-title>Logout</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </v-app-bar>

    <v-navigation-drawer v-model="drawer" width="260">
      <v-list density="comfortable" nav>
        <!-- 권한 필터된 메뉴 -->
        <v-list-item
          v-for="m in menu.visibleItems"
          :key="m.to"
          :title="m.label"
          :to="m.to"
          color="primary"
          :active="isActive(m.to)"
          link
        />
      </v-list>
      <v-divider class="my-2" />
      <div class="px-4 py-2 text-caption">v0.1.0</div>
    </v-navigation-drawer>

    <v-main>
      <v-container fluid class="py-6">
        <router-view />
      </v-container>
    </v-main>

  <ToastHost />
  <ConfirmHost />
  </v-app>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMenuStore } from '@/stores/menu'
import { useAuthStore } from '@/stores/auth'
import ToastHost from '@/ui/components/ToastHost.vue'
import ConfirmHost from '@/ui/components/ConfirmHost.vue'

const drawer = ref(true)
const route = useRoute()
const router = useRouter()
const menu = useMenuStore()
const auth = useAuthStore()

function isActive(to: string) {
  return route.path === to || route.path.startsWith(to + '/')
}
function logout() {
  auth.logout()
  router.replace('/login')
}

onMounted(() => {
  menu.load().catch(() => {})
})
</script>

<style>
html, body, #app { height: 100%; }
</style>
