<template>
  <div class="filter-bar">
    <div class="filter-left">
      <slot name="left" />
    </div>
    <div class="filter-right">
      <slot name="right" />
    </div>
  </div>
</template>

<script setup lang="ts"></script>

<style scoped>
.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  padding: 4px 0;
}
.filter-left,
.filter-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
