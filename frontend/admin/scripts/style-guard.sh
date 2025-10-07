#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.."; pwd)"
cd "$ROOT"

echo "▶ Style Guard: 하드코딩 색/px/중복 오버라이드 체크 시작"

# 제외 대상(정상 파일)
EXCLUDES='(src/styles/tokens\.css|src/plugins/vuetify\.ts|src/ui/tokens\.ts|dist/|\.bak_|node_modules/)'

# 1) 하드코딩 색(#abc / #aabbcc)
FOUND_COLOR=$(grep -RIn --include='*.{vue,css,scss,ts}' '#[0-9A-Fa-f]\{3,6\}' src \
  | grep -Ev "$EXCLUDES" || true)

# 2) px 직입력(유틸/토큰 외부)
FOUND_PX=$(grep -RIn --include='*.{vue,css,scss}' -E '[^0-9][0-9]{1,3}px[^a-zA-Z]' src \
  | grep -Ev "$EXCLUDES|src/styles/" || true)

# 3) Vuetify 컴포넌트 색 강제 오버라이드(대표 패턴)
FOUND_OVERRIDE=$(grep -RIn --include='*.css' -E '^\s*\.(v-btn|v-tabs|v-app-bar|v-chip|v-text-field|v-select)\b.*\{.*(color:|background-color:)' src/styles \
  | grep -Ev "$EXCLUDES" || true)

EXIT=0

if [[ -n "$FOUND_COLOR" ]]; then
  echo "❌ 하드코딩 색 발견:"
  echo "$FOUND_COLOR"
  EXIT=1
else
  echo "✅ 하드코딩 색 없음"
fi

if [[ -n "$FOUND_PX" ]]; then
  echo "❌ px 직입력 발견(토큰화 필요):"
  echo "$FOUND_PX"
  EXIT=1
else
  echo "✅ px 직입력 없음(스타일 폴더 외)"
fi

if [[ -n "$FOUND_OVERRIDE" ]]; then
  echo "❌ Vuetify 컴포넌트 색 오버라이드 발견(테마에 위임 필요):"
  echo "$FOUND_OVERRIDE"
  EXIT=1
else
  echo "✅ Vuetify 색 오버라이드 없음(styles/*)"
fi

if [[ $EXIT -ne 0 ]]; then
  echo "⛔ Style Guard 실패: tokens.css/테마로 이관 후 재시도하세요."
  exit 1
fi

echo "🎉 Style Guard 통과"
