#!/bin/bash
# ============================================================
# Hotel Admin — UI import path fixer (2025-10-15)
# ============================================================

set -e
echo "▶ import 경로 자동 수정 중..."

fix() {
  local old="$1"
  local new="$2"
  grep -Rl "$old" . | while read -r f; do
    sed -i "s|$old|$new|g" "$f"
    echo "  ↳ $f"
  done
}

fix "@/ui/components/common/ToastHost.vue" "@/ui/components/common/ToastHost.vue"
fix "@/ui/components/common/ConfirmHost.vue" "@/ui/components/common/ConfirmHost.vue"
fix "@/ui/components/layout/UserMenu.vue" "@/ui/components/layout/UserMenu.vue"
fix "@/ui/components/common/StateBlock.vue" "@/ui/components/common/StateBlock.vue"
fix "@/ui/components/common/SmartFilterBar.vue" "@/ui/components/common/SmartFilterBar.vue"
fix "@/ui/components/common/NoTxnModal.vue" "@/ui/components/common/NoTxnModal.vue"
fix "@/ui/components/common/BaseChart.vue" "@/ui/components/common/BaseChart.vue"

echo "✅ 경로 자동 수정 완료!"
echo "이후 npm run dev 로 확인하세요."
