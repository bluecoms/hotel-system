# [QA 보고] Phase 2 Smoke/Scenario 결과 — 2025-10-01

## OTA
- [x] 채널 생성/조회 200
- [x] 중복 생성 400/409
- [x] 커미션 조회 200 + 필드(rate,type) 검증

## Reports
- [x] /api/reports/sales-tags 정상 요청 200
- [x] 누락 파라미터 → 빈 배열

## 회귀 (Phase1 Smoke 유지)
- [x] /api/openapi.json → 200
- [x] /api/me (무토큰) → 401
- [x] /api/me (토큰) → 200
- [x] /api/closing/calendar → items 키 존재

## 결론
- **QA: Smoke & 시나리오 Pass**
- 증빙: `/docs/runbooks/phase2/2025-10-01_QA/`
- 리포트: `2025-10-01_QA_Sync_Run.md`
