#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8000}"
TOK="${TOK:-dev-admin-token}"
DATE="${DATE:-$(date +%Y-%m-%d)}"
RUN="/volume1/web/hotel-system/docs/runbooks/phase2/${DATE}_QA"
HDR=(-H "X-Internal-Token: ${TOK}")

mkdir -p "$RUN/evidence/"{json,curl,logs} "$RUN/reports"

pass=1

# --- 1) /api/openapi.json (정책 반영)
code_openapi=$(curl -s -o "$RUN/evidence/json/openapi.json" -D "$RUN/evidence/curl/openapi.hdr" \
  -w "%{http_code}" "$BASE/api/openapi.json" || true)
echo "$code_openapi" > "$RUN/reports/openapi_code.txt"
[ "$code_openapi" = "200" ] || pass=0

# --- 2) /api/me (무토큰 → 401)
code_me_wo=$(curl -s -o "$RUN/evidence/json/me_without.json" -D "$RUN/evidence/curl/me_without.hdr" \
  -w "%{http_code}" "$BASE/api/me" || true)
echo "$code_me_wo" > "$RUN/reports/me_without_code.txt"
[ "$code_me_wo" = "401" ] || pass=0

# --- 3) /api/me (토큰 → 200)
code_me_w=$(curl -s -o "$RUN/evidence/json/me_with.json" -D "$RUN/evidence/curl/me_with.hdr" \
  -w "%{http_code}" "${HDR[@]}" "$BASE/api/me" || true)
echo "$code_me_w" > "$RUN/reports/me_with_code.txt"
[ "$code_me_w" = "200" ] || pass=0

# --- 4) /api/closing/calendar (items 키 존재)
MONTH=$(date +%Y-%m)
curl -sf -D "$RUN/evidence/curl/closing_${MONTH}.hdr" "${HDR[@]}" \
  "$BASE/api/closing/calendar?month=$MONTH" -o "$RUN/evidence/json/closing_${MONTH}.json" || pass=0

# items 키 검사 (jq 있으면 jq, 없으면 grep)
items_ok=0
if command -v jq >/dev/null 2>&1; then
  jq -e 'has("items")' "$RUN/evidence/json/closing_${MONTH}.json" >/dev/null 2>&1 && items_ok=1
else
  grep -q '"items"' "$RUN/evidence/json/closing_${MONTH}.json" && items_ok=1
fi
[ "$items_ok" = "1" ] || pass=0

# --- 요약 리포트 생성
report="$RUN/reports/${DATE}_QA_Report.md"
{
  echo "# Phase 2 QA 보고서 — ${DATE}"
  echo ""
  echo "## Smoke 결과 (정책 반영판)"
  echo "- [$([ "$code_openapi" = "200" ] && echo x || echo ' ')] GET /api/openapi.json → ${code_openapi}"
  echo "- [$([ "$code_me_wo" = "401" ] && echo x || echo ' ')] GET /api/me (무토큰) → ${code_me_wo}"
  echo "- [$([ "$code_me_w"  = "200" ] && echo x || echo ' ')] GET /api/me (토큰) → ${code_me_w}"
  echo "- [$([ "$items_ok" = "1" ] && echo x || echo ' ')] GET /api/closing/calendar?month=${MONTH} → \"items\" 키 존재"
  echo ""
  echo "## 증빙 경로"
  echo "- JSON: docs/runbooks/phase2/${DATE}_QA/evidence/json/"
  echo "- 헤더: docs/runbooks/phase2/${DATE}_QA/evidence/curl/"
  echo "- 코드: docs/runbooks/phase2/${DATE}_QA/reports/*_code.txt"
  echo ""
  echo "## 결론"
  if [ "$pass" = "1" ]; then
    echo "- DoD(Smoke) 충족 → **PASS**"
  else
    echo "- 일부 실패 → **PENDING/FAIL** (세부 사항 위 증빙 참조)"
  fi
} > "$report"

# --- 종료 메시지/코드
if [ "$pass" = "1" ]; then
  echo "QA: Smoke PASS ($report)"
  exit 0
else
  echo "QA: Smoke FAIL ($report)"
  exit 1
fi
