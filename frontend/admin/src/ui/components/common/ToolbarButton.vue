<!-- ===========================================================
  Hotel Admin — src/ui/components/ToolbarButton.vue
  Version: 2025-10-17 Stable v1.2
  -------------------------------------------------------------
  목적:
    • page-shell.vue의 <slot name="toolbar"> 내부에서 사용하는
      표준 버튼 컴포넌트
    • Vuetify <v-btn>의 스타일/속성을 일원화 (색상·아이콘·크기)
    • 모든 Toolbar 버튼은 이 컴포넌트를 통해 시각적 일관성을 유지

  사용 예시:
    <ToolbarButton icon="mdi-refresh" @click="load">불러오기</ToolbarButton>
    <ToolbarButton color="secondary" variant="tonal" icon="mdi-plus">추가</ToolbarButton>

  주의:
    - size="small" 고정 (툴바 버튼 통일)
    - 부모에서 v-toolbar, page-shell 등의 레이아웃 안에 배치
=========================================================== -->

<template>
  <v-btn
    :color="color"
    :variant="variant"
    :prepend-icon="icon"
    size="small"
    class="font-weight-600"
    v-bind="$attrs"
  >
    <slot />
  </v-btn>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    icon?: string
    color?: string
    variant?: 'flat' | 'tonal' | 'text' | 'outlined'
  }>(),
  {
    color: 'primary',
    variant: 'flat',
  }
)
</script>
