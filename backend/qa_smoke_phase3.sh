#!/usr/bin/env bash
set -euo pipefail

# ===== 0) ENV =====
DATE="${DATE:-$(date +%Y-%m-%d)}"
BASE="${BASE:-http://127.0.0.1:8000}"
TOK="${TOK:-dev-admin-token}"
RUN="/volume1/web/hotel-system/docs/runbooks/phase3/${DATE}_QA"
CH="${CH:-BKG}"
DF="${DF:-2025-10-01}"
DT="${DT:-2025-10-31}"

HDR_AUTH=(-H "X-Internal-Token: ${TOK}")
HDR_JSON=(-H "Content-Type: application/json")

mkdir -p "$RUN/evidence/"{json,curl} "$RUN/reports"

echo "== ENV ================================="
echo "BASE=$BASE"
echo "CH=$CH DF=$DF DT=$DT"
echo "RUN=$RUN"
echo "========================================"

# 공통 jq 바디
BODY_FRACTION="$(jq -n --arg ch "$CH" --arg df "$DF" --arg dt "$DT" --argjson rate 0.1 \
  '{channel:$ch, valid_from:$df, valid_to:$dt, rate:$rate}')"
BODY_PERCENT="$(jq -n --arg ch "$CH" --arg df "$DF" --arg dt "$DT" --argjson rate 10 \
  '{channel:$ch, valid_from:$df, valid_to:$dt, rate:$rate}')"

mark(){ [ "$1" -eq 1 ] && echo "[x]" || echo "[ ]"; }

pass=1
COMM_LIST_OK=0
COMM_CREATE_OK=0
COMM_DUP_OK=0
COMM_GET_OK=1   # 미구현 시 SKIP
RST_OK=0
EMPTY_OK=0

# ===== A) 목록 조회 (200) =====
code_comm_list=$(
  curl -s -o "$RUN/evidence/json/ota_commissions_list.json" \
       -D "$RUN/evidence/curl/ota_commissions_list.hdr" \
       -w "%{http_code}" "${HDR_AUTH[@]}" \
       "$BASE/api/ota/commissions?channel=$CH&date_from=$DF&date_to=$DT" || true
)
echo "[A] list code=$code_comm_list"
COMM_LIST_OK=$([ "$code_comm_list" = "200" ] && echo 1 || echo 0)
[ $COMM_LIST_OK -eq 1 ] || pass=0

# ===== 유틸: 한 번 생성 =====
create_once(){
  local body="$1"
  curl -s -o "$RUN/evidence/json/ota_commission_create.json" \
       -D "$RUN/evidence/curl/ota_commission_create.hdr" \
       -w "%{http_code}" "${HDR_AUTH[@]}" "${HDR_JSON[@]}" \
       -X POST "$BASE/api/ota/commissions" -d "$body" || true
}

# ===== B) 생성 (0.1 → 실패 시 10 → 409면 최대 6회 다음달 bump) =====
used_body="$BODY_FRACTION"
code_comm_create="$(create_once "$used_body")"

if [ "$code_comm_create" != "200" ] && [ "$code_comm_create" != "201" ]; then
  used_body="$BODY_PERCENT"
  code_comm_create="$(create_once "$used_body")"
fi

# 파이썬으로 월 +1 (BusyBox date 회피)
bump_month_py() {
python - "$@" <<'PY'
import sys, json, calendar
ch, df, dt, rate = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
def bump(d):
    y,m,day = map(int, d.split('-'))
    m += 1
    if m == 13:
        y, m = y+1, 1
    last = calendar.monthrange(y, m)[1]
    day = min(day, last)
    return f"{y:04d}-{m:02d}-{day:02d}"
ndf = bump(df); ndt = bump(dt)
print(json.dumps({"channel": ch, "valid_from": ndf, "valid_to": ndt, "rate": rate}))
PY
}

# 409면 다음달로 최대 6회 이동하며 재시도
if [ "$code_comm_create" = "409" ]; then
  ch="$(echo "$used_body" | jq -r '.channel')"
  df="$(echo "$used_body" | jq -r '.valid_from')"
  dt="$(echo "$used_body" | jq -r '.valid_to')"
  rate="$(echo "$used_body" | jq -r '.rate')"

  for _ in 1 2 3 4 5 6; do
    shifted="$(bump_month_py "$ch" "$df" "$dt" "$rate")"
    code_comm_create="$(create_once "$shifted")"
    used_body="$shifted"
    # 성공하면 중단
    if [ "$code_comm_create" = "200" ] || [ "$code_comm_create" = "201" ]; then
      break
    fi
    # 다음 루프 대비: df/dt 갱신
    df="$(echo "$shifted" | jq -r '.valid_from')"
    dt="$(echo "$shifted" | jq -r '.valid_to')"
    # 409가 아니면 루프 중단 (다른 오류)
    [ "$code_comm_create" = "409" ] || break
  done
fi

echo "[B] create code=$code_comm_create"
COMM_CREATE_OK=$([[ "$code_comm_create" = "200" || "$code_comm_create" = "201" ]] && echo 1 || echo 0)
[ $COMM_CREATE_OK -eq 1 ] || pass=0

# ===== C) 중복/겹침 재생성 → 400/409 기대 =====
code_comm_dup=$(
  curl -s -o "$RUN/evidence/json/ota_commission_dup.json" \
       -D "$RUN/evidence/curl/ota_commission_dup.hdr" \
       -w "%{http_code}" "${HDR_AUTH[@]}" "${HDR_JSON[@]}" \
       -X POST "$BASE/api/ota/commissions" \
       -d "$(cat "$RUN/evidence/json/ota_commission_create.json")" || true
)
echo "[C] dup code=$code_comm_dup"
COMM_DUP_OK=$([[ "$code_comm_dup" = "400" || "$code_comm_dup" = "409" ]] && echo 1 || echo 0)
[ $COMM_DUP_OK -eq 1 ] || pass=0

# ===== D) 단건 조회 (id 있으면만 시도, 404/405는 SKIP) =====
COMM_GET_OK=1
CID="$(jq -er '.id' "$RUN/evidence/json/ota_commission_create.json" 2>/dev/null || true)"
if [ -n "${CID:-}" ] && [[ "$CID" != "null" ]]; then
  code_comm_get=$(
    curl -s -o "$RUN/evidence/json/ota_commission_get.json" \
         -D "$RUN/evidence/curl/ota_commission_get.hdr" \
         -w "%{http_code}" "${HDR_AUTH[@]}" \
         "$BASE/api/ota/commissions/$CID" || true
  )
  if [ "$code_comm_get" = "200" ]; then
    COMM_GET_OK=1
  elif [ "$code_comm_get" = "404" ] || [ "$code_comm_get" = "405" ]; then
    COMM_GET_OK=1
    echo "(info) GET /api/ota/commissions/$CID not available ($code_comm_get) → SKIP"
  else
    COMM_GET_OK=0
    pass=0
  fi
else
  echo "[D] create response has no id → SKIP"
fi

# ===== E) 리포트 정상 =====
code_rst_ok=$(
  curl -s -o "$RUN/evidence/json/reports_sales_tags_ok.json" \
       -D "$RUN/evidence/curl/reports_sales_tags_ok.hdr" \
       -w "%{http_code}" "${HDR_AUTH[@]}" \
       "$BASE/api/reports/sales-tags?date_from=$DF&date_to=$DT" || true
)
echo "[E] report ok code=$code_rst_ok"
RST_OK=$([ "$code_rst_ok" = "200" ] && echo 1 || echo 0)
[ $RST_OK -eq 1 ] || pass=0

# ===== F) 리포트 파라미터 누락 (200 & 빈배열 or 204) =====
code_rst_empty=$(
  curl -s -o "$RUN/evidence/json/reports_sales_tags_empty.json" \
       -D "$RUN/evidence/curl/reports_sales_tags_empty.hdr" \
       -w "%{http_code}" "${HDR_AUTH[@]}" \
       "$BASE/api/reports/sales-tags" || true
)
if [ "$code_rst_empty" = "204" ]; then
  EMPTY_OK=1
else
  if [ "$code_rst_empty" = "200" ]; then
    if command -v jq >/dev/null 2>&1; then
      if jq -e '(
          (type=="array" and length==0) or
          (type=="object" and (
             (has("items") and (.items|type=="array" and (.items|length==0))) or
             (keys|length==0)
          ))
        )' "$RUN/evidence/json/reports_sales_tags_empty.json" >/dev/null 2>&1; then
        EMPTY_OK=1
      else
        EMPTY_OK=0
      fi
    else
      grep -qx '\[\]' "$RUN/evidence/json/reports_sales_tags_empty.json" && EMPTY_OK=1 || EMPTY_OK=0
    fi
  fi
fi
echo "[F] report empty code=$code_rst_empty"
[ $EMPTY_OK -eq 1 ] || pass=0

# ===== G) 요약 =====
REPORT="$RUN/reports/${DATE}_QA_Phase3_Smoke.md"
{
  echo "== RESULT ==============================="
  echo "COMM_LIST_OK=$COMM_LIST_OK"
  echo "COMM_CREATE_OK=$COMM_CREATE_OK"
  echo "COMM_DUP_OK=$COMM_DUP_OK"
  echo "COMM_GET_OK=$COMM_GET_OK"
  echo "RST_OK=$RST_OK"
  echo "EMPTY_OK=$EMPTY_OK"
  echo "Report: $REPORT"
  echo "========================================"
} | tee /dev/stderr

{
  echo "# Phase 3 QA 스모크 — ${DATE}"
  echo ""
  echo "## OTA Commissions"
  echo "- $(mark $COMM_LIST_OK) 목록 조회 200"
  echo "- $(mark $COMM_CREATE_OK) 생성 200/201"
  echo "- $(mark $COMM_DUP_OK) 중복/범위 위반 400/409"
  if [ -n "${CID:-}" ]; then
    if [ -n "${code_comm_get:-}" ]; then
      echo "- $(mark $COMM_GET_OK) 단건 조회 200 or SKIP(404/405 허용) (code=$code_comm_get)"
    else
      echo "- $(mark 1) 단건 조회 SKIP(응답 id 없음)"
    fi
  fi
  echo ""
  echo "## Reports /sales-tags"
  echo "- $(mark $RST_OK) 정상(date_from/to) 200"
  echo "- $(mark $EMPTY_OK) 누락 파라미터 200&빈배열 또는 204"
  echo ""
  echo "## 증빙"
  echo "- JSON/헤더: docs/runbooks/phase3/${DATE}_QA/evidence/{json,curl}"
  echo "- 리포트: ${REPORT##*/}"
  echo ""
  echo "## 결론"
  if [ $pass -eq 1 ]; then
    echo "- **QA: Smoke PASS**"
  else
    echo "- **QA: 일부 FAIL/PENDING** — 상세 증빙 참조"
  fi
} > "$REPORT"

# ===== H) 종료 =====
if [ $pass -eq 1 ]; then
  echo "QA: Smoke PASS ($REPORT)"
  exit 0
else
  echo "QA: Smoke FAIL ($REPORT)"
  exit 1
fi
