<template>
  <v-container fluid class="page-shell py-6">
    <div class="bar brand-panel d-flex align-center justify-space-between flex-wrap mb-4">
      <div class="bar-left d-flex align-center flex-wrap gap8">
        <v-icon color="primary" icon="mdi-account-circle-outline" size="22" />
        <h2 class="text-h6 font-weight-bold">{{ user?.name || '사용자 상세' }}</h2>
        <span class="text-muted text-body-2">{{ user?.email }}</span>
      </div>

      <div class="bar-right d-flex align-center gap8 mt-2 mt-sm-0">
        <v-chip
          size="small"
          :color="user?.is_active ? 'green' : 'grey-lighten-1'"
          :text-color="user?.is_active ? 'white' : 'grey-darken-1'"
          label
        >
          {{ user?.is_active ? '활성' : '비활성' }}
        </v-chip>
        <v-btn
          variant="outlined"
          color="primary"
          prepend-icon="mdi-arrow-left"
          @click="router.push('/admin/users')"
        >
          목록으로
        </v-btn>
      </div>
    </div>

    <v-card class="rounded-xl elevation-1">
      <v-tabs v-model="tab" color="primary" grow>
        <v-tab value="profile">프로필</v-tab>
        <v-tab value="contract">계약서</v-tab>
      </v-tabs>

      <v-divider />

      <v-card-text class="pa-6">
        <v-window v-model="tab">
          <v-window-item value="profile">
            <v-form ref="formRef" @submit.prevent="saveProfile" class="py-3">
              <v-row dense>
                <v-col cols="12" md="4">
                  <v-text-field v-model="form.name" label="이름" />
                </v-col>
                <v-col cols="12" md="4">
                  <v-text-field v-model="form.email" label="이메일" />
                </v-col>
                <v-col cols="12" md="4">
                  <v-select v-model="form.role" :items="roleItems" label="역할(Role)" />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field v-model="form.department" label="부서" />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field v-model="form.position" label="직책" />
                </v-col>
                <v-col cols="12">
                  <v-textarea v-model="form.memo" label="메모" rows="3" />
                </v-col>
              </v-row>

              <div class="d-flex justify-end mt-4 gap8">
                <v-btn variant="text" @click="router.push('/admin/users')">취소</v-btn>
                <v-btn color="primary" :loading="saving" @click="saveProfile">저장</v-btn>
              </div>
            </v-form>
          </v-window-item>

          <v-window-item value="contract">
            <ContractTab :user-id="userId" />
          </v-window-item>
        </v-window>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import http from '@/services/http'
import ContractTab from '@/views/Admin/HR/ContractTab.vue'
import { useToast } from '@/ui/composables/useToast'

const route = useRoute()
const router = useRouter()
const { success, error } = useToast()

const userId = Number(route.params.id)
const user = ref<any>(null)
const tab = ref('profile')
const form = ref<any>({
  name: '',
  email: '',
  role: '',
  department: '',
  position: '',
  memo: '',
})
const roleItems = ['SUPERADMIN', 'ADMIN', 'FRONT', 'HK', 'FNB']
const saving = ref(false)

async function loadUser() {
  try {
    const r = await http.get(`/users/${userId}`)
    user.value = r
    Object.assign(form.value, r)
  } catch {
    error('사용자 정보를 불러오지 못했습니다.')
  }
}

async function saveProfile() {
  try {
    saving.value = true
    await http.put(`/users/${userId}`, form.value)
    success('저장되었습니다.')
  } catch {
    error('저장 실패')
  } finally {
    saving.value = false
  }
}

onMounted(loadUser)
</script>

<style scoped src="@/styles/toolbar.scss"></style>

<style scoped>
.page-shell {
  max-width: 1280px;
  margin: 0 auto;
}
</style>
