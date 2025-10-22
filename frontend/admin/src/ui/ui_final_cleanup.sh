#!/bin/bash
# ============================================================
# Hotel Admin UI Final Cleanup — move root UI elements to /common
# 실행 위치: /volume1/web/hotel-system/frontend/admin/src/ui
# ============================================================

set -e
BASE_DIR="/volume1/web/hotel-system/frontend/admin/src/ui"
COMMON_DIR="$BASE_DIR/components/common"
LOG_DIR="$BASE_DIR/_runlogs"
LOG_FILE="$LOG_DIR/ui_final_cleanup_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$COMMON_DIR" "$LOG_DIR"

echo "▶ [1/3] 공통 컴포넌트 이동 시작..." | tee -a "$LOG_FILE"

# 공통 대상 목록
FILES=(
  "Badge.vue"
  "Button.vue"
  "ProgressBar.vue"
  "ProgressRing.vue"
  "Tooltip.vue"
)

for f in "${FILES[@]}"; do
  if [ -f "$BASE_DIR/$f" ]; then
    mv -v "$BASE_DIR/$f" "$COMMON_DIR/" | tee -a "$LOG_FILE"
  fi
done

echo "✅ [2/3] 이동 완료 — theme.ts, tokens.ts는 그대로 유지" | tee -a "$LOG_FILE"

echo "▶ [3/3] 최종 구조 확인:" | tee -a "$LOG_FILE"
tree -L 2 "$BASE_DIR" | tee -a "$LOG_FILE" || ls -R "$BASE_DIR" | tee -a "$LOG_FILE"

echo
echo "✅ Hotel Admin UI Final Cleanup 완료!"
echo "📝 로그: $LOG_FILE"
