# Phase 2 QA 동기 진행 — 2025-10-01

## OTA 채널
- [x] 채널 생성/조회 200 (create=201, get=404)
- [x] 중복 생성 400/409 (dup=400)

## OTA 커미션
- [ ] 커미션 조회 200 + 필드(rate,type) 검증 (code=200, fields=NG)

## Reports /api/reports/sales-tags
- [x] 정상(date_from/to) → 200
- [x] 누락 파라미터 → 빈 배열 (code=200)

## 증빙 경로
- JSON/헤더: docs/runbooks/phase2/2025-10-01_QA/evidence/{json,curl}
- 코드: docs/runbooks/phase2/2025-10-01_QA/reports/*.txt

## 결론
- **QA: 일부 FAIL/PENDING** (상세는 증빙 참조) — 재검증 필요
