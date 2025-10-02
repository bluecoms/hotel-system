#  BE-Core Phase 2 실행 착수 보고 (2025-10-01)

## 0) 요약
- Alembic `phase2_ota_init` 생성 및 upgrade head PASS
- OTA/Reports API 뼈대 및 인증 가드 적용
- 메뉴(OTA/Reports) 반영

## 1) 작업 상세
- DB: `ota_channels`, `ota_commissions` 테이블 신설(단일 head 유지)
- API:
  - GET/POST `/api/ota/channels`
  - GET `/api/ota/channels/{id}/history`
  - GET `/api/ota/commissions`
  - GET `/api/reports/sales-tags` (MVP: 빈 배열)
- 인증: `X-Internal-Token` only, without-token=401 보장

## 2) DoD
- [x] `alembic upgrade head` 성공
- [x] curl 테스트 200/401 기대대로 동작
- [x] 스냅샷 수집 완료

## 3) 증빙
- 스냅샷: `docs/runbooks/snapshots/2025-10-01_phase2/`
- 커밋: `BE-Core: Phase 2 kickoff — alembic phase2_ota_init, OTA/Reports routers, nav (2025-10-01)`

## 4) curl 요약
```bash
TOK=dev-admin-token
curl -s -H "X-Internal-Token: $TOK" http://127.0.0.1:8000/api/ota/channels | jq .
curl -s -X POST -H "X-Internal-Token: $TOK" -H "Content-Type: application/json" \
  -d '{"code":"BKG","name":"Booking.com"}' http://127.0.0.1:8000/api/ota/channels | jq .
curl -s -H "X-Internal-Token: $TOK" \
  "http://127.0.0.1:8000/api/reports/sales-tags?date_from=2025-09-01&date_to=2025-09-30" | jq .
