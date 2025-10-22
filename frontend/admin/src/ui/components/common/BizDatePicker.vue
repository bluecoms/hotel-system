<!-- ============================================================
 Hotel Admin — BizDatePicker Component (v2025.10 Final / Full Commented)
---------------------------------------------------------------
 위치: src/ui/components/common/BizDatePicker.vue

 목적:
   • Business Date(업무 일자) 전용 선택 컨트롤 컴포넌트
   • Dashboard/Reports/Closing 등 일 단위 페이지에서 사용
   • 하루 전/후 이동(◀ ▶) 및 Today 버튼 기능 제공
   • SmartFilterBar 내 삽입 시 날짜 제어를 담당

 디자인 특징:
   • Glass 톤(흰색 반투명 배경 + 부드러운 그림자)
   • 둥근형 라운드 + 중심 정렬 + 간결한 포커스
=========================================================== -->

<template>
  <!-- ============================================================
       ▣ 전체 컨테이너 (bizdate-picker)
       ------------------------------------------------------------
       - 날짜 컨트롤 전체를 감싸는 카드형 Wrapper
       - 좌우 버튼 + 날짜 + Today 버튼 구성
  ============================================================ -->
  <div class="bizdate-picker">
    <!-- ◀ 이전일 이동 버튼 -->
    <v-btn
      icon
      variant="text"
      color="primary"
      class="nav-btn"
      @click="shiftDay(-1)"
    >
      <v-icon>mdi-chevron-left</v-icon>
    </v-btn>

    <!-- ▣ 날짜 표시 영역 -->
    <div class="date-display">
      <div class="date-box">{{ formattedDate }}</div>
    </div>

    <!-- ▶ 다음일 이동 버튼 -->
    <v-btn
      icon
      variant="text"
      color="primary"
      class="nav-btn"
      @click="shiftDay(1)"
    >
      <v-icon>mdi-chevron-right</v-icon>
    </v-btn>

    <!-- ▣ Today 버튼 -->
    <v-btn
      variant="tonal"
      color="primary"
      class="today-btn"
      size="small"
      @click="setToday"
    >
      Today
    </v-btn>
  </div>
</template>

<script setup lang="ts">
/* ============================================================
   BizDatePicker Logic Section
   ------------------------------------------------------------
   - v-model 기반으로 날짜를 상위 컴포넌트와 동기화
   - 하루 전/후 이동 및 Today로 변경 기능 제공
=========================================================== */

import { ref, watch, computed } from 'vue'

/* ▣ Props 정의
   ------------------------------------------------------------
   - modelValue: 부모로부터 전달받는 현재 날짜(YYYY-MM-DD)
*/
const props = defineProps<{ modelValue: string }>()

/* ▣ Emits 정의
   ------------------------------------------------------------
   - update:modelValue: 날짜 변경 시 부모로 전달 (v-model 대응)
*/
const emit = defineEmits<{ 'update:modelValue': [string] }>()

/* ▣ 내부 상태 (model)
   ------------------------------------------------------------
   - 초기값: props.modelValue || 오늘 날짜
   - 내부에서 날짜 이동 시 즉시 emit
*/
const model = ref(props.modelValue || new Date().toISOString().slice(0, 10))

/* ▣ 외부 값 변경 감시
   ------------------------------------------------------------
   - 부모에서 modelValue 변경 시 내부 model도 동기화
*/
watch(() => props.modelValue, (v) => {
  if (v && v !== model.value) model.value = v
})

/* ▣ 표시용 날짜 (computed)
   ------------------------------------------------------------
   - 현재 model 값 그대로 표시 (YYYY-MM-DD)
*/
const formattedDate = computed(() => model.value)

/* ▣ 하루 이동 (n = ±1)
   ------------------------------------------------------------
   - 현재 날짜에서 n일을 더하거나 빼서 이동
   - ISO 포맷으로 변환 후 emit
*/
function shiftDay(n: number) {
  const d = new Date(model.value)
  d.setDate(d.getDate() + n)
  const next = d.toISOString().slice(0, 10)
  model.value = next
  emit('update:modelValue', next)
}

/* ▣ 오늘 날짜로 이동
   ------------------------------------------------------------
   - 현재 날짜를 오늘로 변경하고 emit
*/
function setToday() {
  const today = new Date().toISOString().slice(0, 10)
  model.value = today
  emit('update:modelValue', today)
}
</script>

<style scoped>
/* ============================================================
   BizDatePicker — Perfect Centered Compact Ver.
   ------------------------------------------------------------
   디자인 포인트:
     • Glass 톤 흰색 반투명 카드
     • 둥근형 라운드 및 미묘한 그림자
     • 내부 요소 완전 중앙 정렬
=========================================================== */

/* ▣ 전체 컨테이너 */
.bizdate-picker {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px; /* ✅ 버튼 간 여백 축소로 균형감 향상 */
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-lg);
  padding: 10px 20px;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.05);
  backdrop-filter: blur(6px);
  transition: all 0.25s ease;
}
.bizdate-picker:hover {
  box-shadow: 0 5px 14px rgba(30, 64, 175, 0.12);
}

/* ▣ 날짜 표시 영역 */
.date-display {
  flex: none;
  min-width: 160px; /* ✅ 날짜 영역 폭 (Compact 버전) */
  display: flex;
  justify-content: center;
}

/* ▣ 날짜 텍스트 박스 */
.date-box {
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(96, 165, 250, 0.12);
  border-radius: var(--radius-md);
  padding: 8px 20px; /* ✅ 좌우 여백 */
  font-weight: 700;
  font-size: 1.05rem;
  color: var(--v-theme-primary);
  line-height: 1;
  min-height: 42px;
  box-shadow: inset 0 0 0 1px rgba(96, 165, 250, 0.25);
  transition: all 0.2s ease;
}
.date-box:hover {
  background: rgba(59, 130, 246, 0.18);
  box-shadow: inset 0 0 0 1px rgba(59, 130, 246, 0.35);
}

/* ▣ ◀ / ▶ 버튼 */
.nav-btn {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}
.nav-btn:hover {
  background-color: rgba(59, 130, 246, 0.1);
  transform: scale(1.05);
}

/* ▣ Today 버튼 */
.today-btn {
  height: 38px;
  min-width: 76px;
  font-weight: 600;
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-xs);
  transition: all 0.2s ease;
}
.today-btn:hover {
  box-shadow: 0 3px 6px rgba(37, 99, 235, 0.25);
  transform: translateY(-1px);
}
</style>
