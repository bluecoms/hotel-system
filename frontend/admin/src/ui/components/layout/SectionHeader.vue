<!-- ============================================================================
  File    : src/ui/components/layout/SectionHeader.vue
  Version : 2025.10 Final Stable (Phase3 SSOT UI)
  Purpose : 섹션 타이틀 바(아이콘 + 제목 + 툴팁) 공통 컴포넌트
  ------------------------------------------------------------------------------
  특징:
    ✅ 각 탭 상단 제목줄을 일관된 UI로 제공
    ✅ 아이콘 + 굵은 제목 + (옵션) 설명 툴팁 + 하단 구분선
    ✅ Board.vue / DocsAdmin 등 어디서든 재사용 가능
  ------------------------------------------------------------------------------
  Props:
    • icon : string   → MDI 아이콘 이름 (예: 'mdi-bed-outline')
    • title: string   → 섹션 제목 (예: '객실 매출 업로드')
    • hint : string?  → (옵션) 설명 툴팁 텍스트
============================================================================ -->

<template>
  <div class="d-flex align-center justify-space-between mb-2">
    <div class="d-flex align-center" style="gap:8px">
      <v-icon :icon="icon" size="20" />
      <span class="text-subtitle-1 font-weight-bold">{{ title }}</span>
      <v-tooltip v-if="hint" :text="hint">
        <template #activator="{ props }">
          <v-icon v-bind="props" icon="mdi-information-outline" size="18" />
        </template>
      </v-tooltip>
    </div>
  </div>
  <v-divider class="mb-4" />
</template>

<script setup lang="ts">
defineProps<{
  icon: string
  title: string
  hint?: string
}>()
</script>
