# Phase 3 QA 보고서 — RBAC 스모크/회귀 (2025-10-02)

## 1) 권한 시나리오
- [x] ADMIN /api/ota/channels → 200
- [x] USER /api/ota/channels → 403
- [x] MENU(Admin) → OTA/Reports 노출
- [x] MENU(User) → OTA/Reports 숨김

## 2) 회귀
- [x] /api/openapi.json → 200
- [x] /api/me 무토큰=401 / 토큰=200
- [x] /api/closing/calendar → items 존재
- [x] /api/reports/sales-tags 빈/정상 → 200

## 3) 증빙
- Evidence: `/docs/runbooks/phase3/2025-10-02_QA/evidence/`  
  - ota_admin_200.txt  
  - ota_user_403.txt  
  - menu_admin.json  
  - menu_user.json  
- Report: `Phase3_RBAC_Smoke.md`

## 4) 결론
- **QA: RBAC 스모크 PASS + 회귀 PASS**
