<template>
  <v-container class="py-12 text-center">
    <v-row justify="center">
      <v-col cols="12" md="6" class="d-flex flex-column align-center">
        <v-icon color="grey" size="64" class="mb-4">mdi-clock-outline</v-icon>
        <h2 class="text-h5 mb-2">준비 중입니다</h2>
        <p class="text-body-2 text-medium-emphasis mb-6">
          이 페이지는 아직 개발 중이에요.<br>
          곧 사용할 수 있게 될 예정입니다.
        </p>
        <v-btn color="primary" to="/">대시보드로 돌아가기</v-btn>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
</script>

<style scoped>
.v-icon {
  opacity: 0.6;
}
</style>
