<!-- ============================================================================
Hotel Admin System — OtaFeeTable (OTA 수수료 관리)
-------------------------------------------------------------------------------
버전: v2025-10-18 FINAL (API 경로 정규화)
파일경로: src/views/Users/master/OtaFeeTable.vue
작성자: Hotel-System Dev Team

[목적]
  • OTA 수수료 관리 탭
  • MasterTable 컴포넌트를 사용하여 /api/ota/commissions CRUD 관리
  • 필드 구성: channel, rate(%), note, is_active

[백엔드 API]
  - GET    /api/ota/commissions
  - POST   /api/ota/commissions
  - PUT    /api/ota/commissions/{id}
  - DELETE /api/ota/commissions/{id}

[프런트 연동]
  • fetch 기반(http.ts) → baseURL=/api
  • 따라서 api-base="ota/commissions" 로 지정 (/api 중복 방지)
  • MasterTable 내부에서 CRUD, 검색, 사용 여부 토글 일원화 처리

[UI]
  • 아이콘: mdi-cash-percent
  • 포인트 컬러: teal
=============================================================================== -->
<template>
  <MasterTable
    title="OTA 수수료 목록"
    api-base="ota/commissions"
    icon="mdi-cash-percent"
    color="teal"
  />
</template>

<script setup lang="ts">
/* ============================================================================
  스크립트 로직
============================================================================ */
import MasterTable from '@/ui/components/users/master/MasterTable.vue'
</script>
