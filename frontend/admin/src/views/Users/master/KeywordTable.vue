<!-- ============================================================================
Hotel Admin System — KeywordTable (키워드 관리)
-------------------------------------------------------------------------------
버전: v2025-10-18 FINAL (API 경로 정규화)
파일경로: src/views/Users/master/KeywordTable.vue
작성자: Hotel-System Dev Team

[목적]
  • 인사/운영 시스템 내 “키워드 관리” 탭
  • 공통 컴포넌트 MasterTable 기반으로 /api/keywords CRUD 처리
  • 필드 구성: group_name, k, v, weight, is_active

[백엔드 API]
  - GET    /api/keywords
  - POST   /api/keywords
  - PUT    /api/keywords/{id}
  - DELETE /api/keywords/{id}

[프런트 연동]
  • http.ts(fetch 기반) → baseURL=/api
  • 따라서 api-base="keywords" 로 지정 (중복 /api 방지)
  • MasterTable 에서 CRUD, 검색, 사용여부 토글 통합 관리

[UI]
  • 아이콘: mdi-tag-multiple-outline
  • 포인트 컬러: purple
=============================================================================== -->
<template>
  <MasterTable
    title="키워드 목록"
    api-base="keywords"
    icon="mdi-tag-multiple-outline"
    color="purple"
  />
</template>

<script setup lang="ts">
/* ============================================================================
  스크립트 로직
============================================================================ */
import MasterTable from '@/ui/components/users/master/MasterTable.vue'
</script>
