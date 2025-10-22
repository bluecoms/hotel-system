<template>
  <v-container class="page-shell py-6">
    <div class="bar mb-4 d-flex align-center gap8">
      <v-icon color="primary" icon="mdi-database-cog-outline" size="22" />
      <div>
        <h2 class="text-h6 font-weight-bold">사용자 기준정보 관리</h2>
        <div class="text-body-2 text-medium-emphasis">부서 · 직책 · 사번 정책</div>
      </div>
    </div>

    <v-card class="rounded-xl elevation-1">
      <v-tabs v-model="tab" color="primary" grow>
        <v-tab value="dept">부서 코드</v-tab>
        <v-tab value="title">직책 코드</v-tab>
        <v-tab value="empno">사번 정책</v-tab>
      </v-tabs>
      <v-divider />

      <v-window v-model="tab" class="pa-4">
        <v-window-item value="dept"><DeptTable /></v-window-item>
        <v-window-item value="title"><TitleTable /></v-window-item>
        <v-window-item value="empno"><EmpNoPolicy /></v-window-item>
      </v-window>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import DeptTable from '@/views/Users/master/DeptTable.vue'
import TitleTable from '@/views/Users/master/TitleTable.vue'
import EmpNoPolicy from '@/views/Users/master/EmpNoPolicy.vue'
const tab = ref<'dept' | 'title' | 'empno'>('dept')
</script>

<style scoped src="@/styles/toolbar.scss"></style>
