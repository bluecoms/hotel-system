# Phase 3 — Reports 스모크/회귀 결과 (2025-10-02)

## 1) 스모크 스니펫 (복붙)
```bash
BASE="http://127.0.0.1:8000"; TOK="${TOK:-dev-admin-token}"

# 빈 파라미터 → 200 & []
A=$(curl -s -H "X-Internal-Token: $TOK" "$BASE/api/reports/sales-tags" | jq -c '.')
echo "$A" | jq type | grep -q '"array"' && echo "OK: empty array" || echo "NG"

# 정상 범위 → 200 & array
B=$(curl -s -H "X-Internal-Token: $TOK"   "$BASE/api/reports/sales-tags?date_from=2025-10-01&date_to=2025-10-31" | jq -c '.')
echo "$B" | jq type | grep -q '"array"' && echo "OK: array" || echo "NG"

# 회귀(정책 경로)
curl -s -o /dev/null -w "%{http_code}\n" "$BASE/api/openapi.json"   # 200
curl -s -o /dev/null -w "%{http_code}\n" "$BASE/api/me"            # 401
curl -s -o /dev/null -w "%{http_code}\n" -H "X-Internal-Token: $TOK" "$BASE/api/me"  # 200
curl -sf "$BASE/api/closing/calendar?month=$(date +%Y-%m)" | python -m json.tool | grep -q '"items"'
```

## 2) 증빙 저장 경로
- `/docs/runbooks/phase3/{DATE}_QA/evidence/reports_sales_tags_empty.json`
- `/docs/runbooks/phase3/{DATE}_QA/evidence/reports_sales_tags_oct.json`
- 리포트: `/docs/runbooks/phase3/{DATE}_QA/reports/Phase3_Smoke_Reports.md`

## 3) 체크 결과 입력란
- [ ] 빈 파라미터 → 200 & []
- [ ] 정상 범위 → 200 & array
- [ ] /api/openapi.json → 200
- [ ] /api/me (무토큰) → 401
- [ ] /api/me (토큰) → 200
- [ ] /api/closing/calendar → items 키 존재

## 4) 메모
- sales-tags 집계 로직 구현 이후 합산 값 검증 케이스를 추가로 확장 예정.
