<template>
  <v-container class="py-10" style="max-width:480px">
    <h2 class="text-h5 mb-6">Login (DEV)</h2>

    <v-select
      v-model="role"
      :items="roleItems"
      label="Role"
      density="comfortable"
      class="mb-3"
    />
    <v-text-field
      v-model="token"
      label="Internal Token"
      density="comfortable"
      class="mb-4"
    />

    <v-btn color="primary" class="mt-2" @click="go">Login</v-btn>

    <v-alert v-if="err" type="warning" class="mt-4">{{ err }}</v-alert>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// DEV용 간편 로그인: SUPERADMIN 권한 기본
type Role = 'SUPERADMIN' | 'ADMIN'
const role = ref<Role>('SUPERADMIN')
const roleItems = ['SUPERADMIN','ADMIN']
const token = ref('dev-admin-token')

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const err = ref<string | null>(null)

async function go() {
  err.value = null
  try {
    await auth.devLogin(role.value, token.value)
    const redirect = (route.query.redirect as string) || '/dashboard'
    router.replace(redirect)
  } catch (e:any) {
    err.value = e?.message ?? '로그인 실패'
  }
}
</script>
