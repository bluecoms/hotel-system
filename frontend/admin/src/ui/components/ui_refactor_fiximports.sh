#!/bin/bash
# ============================================================
# Hotel Admin UI Refactor — Components → Domain 자동 정리 + import 경로 수정
# 실행 위치: /volume1/web/hotel-system/frontend/admin/src/ui/components
# ============================================================

set -e
BASE_DIR="/volume1/web/hotel-system/frontend/admin/src/ui/components"
SRC_DIR="/volume1/web/hotel-system/frontend/admin/src"
BACKUP_DIR="/volume1/web/hotel-system/frontend/admin/src/_backup/ui_components_$(date +%Y%m%d_%H%M%S)"

echo "▶ [1/5] 백업 생성 중..."
mkdir -p "$BACKUP_DIR"
cp -r "$BASE_DIR" "$BACKUP_DIR"
echo "✅ 백업 완료 → $BACKUP_DIR"

echo "▶ [2/5] 도메인 폴더 생성..."
cd "$BASE_DIR"
for d in dashboard closing ota reports hr users system account auth; do
  mkdir -p "$d"
done
echo "✅ 폴더 생성 완료"

echo "▶ [3/5] 도메인별 파일 이동..."
# Closing
mv -v DatasetCard.vue DialogUpload.vue BoardList.vue Closing* Merge* closing/ 2>/dev/null || true

# Reports
mv -v BankLedgerSummary.vue KpiCard.vue reports/ 2>/dev/null || true

# HR
mv -v DialogEmployee* DialogLinkAccount.vue hr/ 2>/dev/null || true
mv -v DialogContract* hr/ 2>/dev/null || true

# Users
mv -v DialogUser* DialogRecord* users/ 2>/dev/null || true

# OTA
mv -v Ota* ota/ 2>/dev/null || true

# System
mv -v Role* system/ 2>/dev/null || true

# Account/Auth
mv -v Login* ChangePassword* Forbidden* account/ 2>/dev/null || true
mv -v Auth* auth/ 2>/dev/null || true

echo "✅ 파일 이동 완료"

echo "▶ [4/5] import 경로 자동 수정..."
cd "$SRC_DIR"

replace_imports() {
  local name="$1"
  local domain="$2"
  grep -Rl "@/ui/components/${name}" . | while read -r file; do
    sed -i "s|@/ui/components/${name}|@/ui/components/${domain}/${name}|g" "$file"
    echo "  ↳ $file"
  done
}

replace_imports "DialogEmployee" "hr"
replace_imports "DialogContract" "hr"
replace_imports "DialogLinkAccount" "hr"
replace_imports "DatasetCard" "closing"
replace_imports "DialogUpload" "closing"
replace_imports "BoardList" "closing"
replace_imports "BankLedgerSummary" "reports"
replace_imports "KpiCard" "reports"
replace_imports "DialogUser" "users"
replace_imports "DialogRecord" "users"

echo "✅ import 경로 수정 완료"

echo "▶ [5/5] 검증 권장:"
echo "  1) npm run dev  또는  npm run build"
echo "  2) 경로 오류 시 git diff 또는 백업 복원"
echo "  3) 백업 폴더: $BACKUP_DIR"
echo
echo "✅ Hotel Admin UI Refactor 전체 완료!"
