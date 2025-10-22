<!-- ============================================================================
Hotel Admin System — OtaAliasTable (OTA 채널 관리)
-------------------------------------------------------------------------------
버전: v2025-10-18 FINAL (API 경로 정규화)
파일경로: src/views/Users/master/OtaAliasTable.vue
작성자: Hotel-System Dev Team

[목적]
  • OTA 채널(별칭) 관리 탭
  • MasterTable 컴포넌트를 사용하여 /api/ota/channels CRUD 관리
  • 필드 구성: k(패턴), v(표준명), weight, is_active

[백엔드 API]
  - GET    /api/ota/channels
  - POST   /api/ota/channels
  - PUT    /api/ota/channels/{id}
  - DELETE /api/ota/channels/{id}

[프런트 연동]
  • fetch 기반(http.ts) → baseURL=/api
  • 따라서 api-base="ota/channels" 로 지정 (/api 중복 방지)
  • MasterTable에서 CRUD, 검색, 사용 여부 토글 일원화 처리

[UI]
  • 아이콘: mdi-earth
  • 포인트 컬러: indigo
=============================================================================== -->
<template>
  <MasterTable
    title="OTA 채널 (별칭) 목록"
    api-base="ota/channels"
    icon="mdi-earth"
    color="indigo"
  />
</template>

<script setup lang="ts">
/* ============================================================================
  스크립트 로직
============================================================================ */
import MasterTable from '@/ui/components/users/master/MasterTable.vue'
</script>
