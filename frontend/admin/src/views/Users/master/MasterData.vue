<!-- ============================================================================
# File      : src/views/Users/master/MasterData.vue
# Version   : 2025.10-30 · v4.0 (Positions & Titles · SSOT Final Stable)
# Purpose   : Hotel Admin — 기준/정제 정보 '카테고리 탭' 통합 관리 화면
# ----------------------------------------------------------------------------
# ✅ 이번 패치 요약
#   • 직위(Position) + 직책(Titles) 구조를 v4.0 백엔드 API와 완전 동기화
#   • API 베이스 /api/master/* 규칙 통일 (titles, positions, ranks 등)
#   • MasterTable 공통 컴포넌트 구조 최신화
# ----------------------------------------------------------------------------
# 카테고리/탭 구성:
#   1) 조직·인사  : 부서 / 직책 / 직위 / 직급 / 급여등급 / 사번정책(전용 폼)
#   2) 재무·지점  : 지점코드(Property) / 은행코드(Bank)
#   3) 운영기준정보: 하우스키핑 상태 / OTA 기준채널(SSOT) / OTA 운영채널 / OTA 수수료
#   4) 콘텐츠관리 : 키워드 관리
# ----------------------------------------------------------------------------
# 트러블슈팅 팁:
#   [TIP-1] 사번정책은 단일 정책 → EmpNoPolicyForm으로 렌더. (MasterTable 사용 금지)
#           API 경로: /api/master/empno-policy
#   [TIP-2] Property는 /api/properties (마스터 prefix 아님)
#   [TIP-3] OTA 기준채널: /api/master/ota-channels (SSOT)
#   [TIP-4] OTA 운영/수수료: /api/ota/channels, /api/ota/commissions
# ============================================================================ -->
<template>
  <v-container class="page-shell py-6">
    <!-- ▣ 상단 헤더 -->
    <div class="bar mb-4 d-flex align-center gap-2">
      <v-icon color="primary" icon="mdi-database-cog-outline" size="22" />
      <div>
        <h2 class="text-h6 font-weight-bold">기준/정제 정보 관리</h2>
        <div class="text-body-2 text-medium-emphasis">
          카테고리 탭으로 정리된 기준/정제 정보(SSOT) 화면 — MasterTable 공통 컴포넌트 최대 활용
        </div>
      </div>
    </div>

    <!-- ▣ 1차: 카테고리 탭 -->
    <v-card class="rounded-xl elevation-1">
      <v-tabs v-model="category" color="primary" grow>
        <v-tab value="org">조직·인사</v-tab>
        <v-tab value="finance">재무·지점</v-tab>
        <v-tab value="operation">운영 기준정보</v-tab>
        <v-tab value="content">콘텐츠 관리</v-tab>
      </v-tabs>

      <v-divider />

      <!-- ▣ 2차: 카테고리별 하위 탭 & 컨텐츠 -->
      <v-window v-model="category" class="pa-4" transition="fade-transition">

        <!-- 1) 조직·인사 -->
        <v-window-item value="org">
          <v-tabs v-model="orgTab" color="secondary" density="comfortable" class="mb-2" grow>
            <v-tab v-for="t in orgTabs" :key="t.key" :value="t.key">{{ t.title }}</v-tab>
          </v-tabs>

          <v-window v-model="orgTab" class="mt-2">
            <v-window-item v-for="t in orgTabs" :key="t.key" :value="t.key">
              <EmpNoPolicyForm v-if="t.kind === 'empnoForm'" />
              <MasterTable
                v-else
                :title="t.title"
                :api-base="t.apiBase"
                :icon="t.icon"
                :color="t.color"
                :id-key="t.idKey ?? 'id'"
                :code-key="t.codeKey ?? defaultCodeKeys"
                :name-key="t.nameKey ?? defaultNameKeys"
              />
            </v-window-item>
          </v-window>
        </v-window-item>

        <!-- 2) 재무·지점 -->
        <v-window-item value="finance">
          <v-tabs v-model="financeTab" color="secondary" density="comfortable" class="mb-2" grow>
            <v-tab v-for="t in financeTabs" :key="t.key" :value="t.key">{{ t.title }}</v-tab>
          </v-tabs>

          <v-window v-model="financeTab" class="mt-2">
            <v-window-item v-for="t in financeTabs" :key="t.key" :value="t.key">
              <MasterTable
                :title="t.title"
                :api-base="t.apiBase"
                :icon="t.icon"
                :color="t.color"
                :id-key="t.idKey ?? 'id'"
                :code-key="t.codeKey ?? defaultCodeKeys"
                :name-key="t.nameKey ?? defaultNameKeys"
              />
            </v-window-item>
          </v-window>
        </v-window-item>

        <!-- 3) 운영 기준정보 -->
        <v-window-item value="operation">
          <v-tabs v-model="opTab" color="secondary" density="comfortable" class="mb-2" grow>
            <v-tab v-for="t in opTabs" :key="t.key" :value="t.key">{{ t.title }}</v-tab>
          </v-tabs>

          <v-window v-model="opTab" class="mt-2">
            <v-window-item v-for="t in opTabs" :key="t.key" :value="t.key">
              <MasterTable
                v-if="t.kind === 'masterTable'"
                :title="t.title"
                :api-base="t.apiBase"
                :icon="t.icon"
                :color="t.color"
                :id-key="t.idKey ?? 'id'"
                :code-key="t.codeKey ?? defaultCodeKeys"
                :name-key="t.nameKey ?? defaultNameKeys"
              />
              <OtaAliasTable v-else-if="t.kind === 'otaActive'" />
              <OtaFeeTable   v-else-if="t.kind === 'otaFee'" />
            </v-window-item>
          </v-window>
        </v-window-item>

        <!-- 4) 콘텐츠 관리 -->
        <v-window-item value="content">
          <v-tabs v-model="contentTab" color="secondary" density="comfortable" class="mb-2" grow>
            <v-tab v-for="t in contentTabs" :key="t.key" :value="t.key">{{ t.title }}</v-tab>
          </v-tabs>

          <v-window v-model="contentTab" class="mt-2">
            <v-window-item v-for="t in contentTabs" :key="t.key" :value="t.key">
              <KeywordTable v-if="t.key === 'keywords'" />
            </v-window-item>
          </v-window>
        </v-window-item>

      </v-window>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import MasterTable from '@/ui/components/users/master/MasterTable.vue'
import EmpNoPolicyForm from '@/views/Users/master/EmpNoPolicyForm.vue'
import OtaAliasTable from '@/views/Users/master/OtaAliasTable.vue'
import OtaFeeTable   from '@/views/Users/master/OtaFeeTable.vue'
import KeywordTable  from '@/views/Users/master/KeywordTable.vue'

/* ▣ 카테고리 상태 */
const category = ref<'org' | 'finance' | 'operation' | 'content'>('org')

/* ▣ 공통 키맵 */
const defaultCodeKeys = ['code', 'dept_code', 'title_code', 'rank_code', 'position_code']
const defaultNameKeys = ['name', 'dept_name', 'title_name', 'rank_name', 'position_name']

/* ▣ 1) 조직·인사 */
const orgTab = ref('departments')
const orgTabs = [
  { key: 'departments', title: '부서 코드',  apiBase: '/api/master/departments',  icon: 'mdi-office-building', color: 'teal' },
  { key: 'titles',      title: '직책 코드',  apiBase: '/api/master/titles',       icon: 'mdi-account-tie',     color: 'indigo' },
  { key: 'positions',   title: '직위 코드',  apiBase: '/api/master/positions',    icon: 'mdi-account-star',    color: 'blue-grey' },
  { key: 'ranks',       title: '직급 코드',  apiBase: '/api/master/ranks',        icon: 'mdi-stairs-up',       color: 'deep-purple' },
  { key: 'salary',      title: '급여 등급',  apiBase: '/api/master/salary-grades',icon: 'mdi-cash-100',        color: 'green' },
  { key: 'empno',       title: '사번 정책',  kind: 'empnoForm',                   icon: 'mdi-badge-account',   color: 'cyan' },
]

/* ▣ 2) 재무·지점 */
const financeTab = ref('property')
const financeTabs = [
  { key: 'property', title: '지점 코드', apiBase: '/api/properties',   icon: 'mdi-domain',  color: 'blue' },
  { key: 'banks',    title: '은행 코드', apiBase: '/api/master/banks', icon: 'mdi-bank',    color: 'blue-grey' },
]

/* ▣ 3) 운영 기준정보 */
const opTab = ref('hk')
const opTabs = [
  { key: 'hk',          title: '하우스키핑 상태', kind: 'masterTable', apiBase: '/api/master/hk-status',    icon: 'mdi-broom', color: 'orange' },
  { key: 'ota_master',  title: 'OTA 기준채널',    kind: 'masterTable', apiBase: '/api/master/ota-channels', icon: 'mdi-earth', color: 'deep-purple' },
  { key: 'ota_active',  title: 'OTA 운영채널',    kind: 'otaActive',   icon: 'mdi-earth-box', color: 'purple' },
  { key: 'ota_fee',     title: 'OTA 수수료',      kind: 'otaFee',      icon: 'mdi-cash-percent', color: 'purple-darken-2' },
]

/* ▣ 4) 콘텐츠 관리 */
const contentTab = ref('keywords')
const contentTabs = [{ key: 'keywords', title: '키워드 관리' }]
</script>

<style scoped>
.bar { align-items: center; }
.page-shell { max-width: 1280px; margin: 0 auto; }
</style>
