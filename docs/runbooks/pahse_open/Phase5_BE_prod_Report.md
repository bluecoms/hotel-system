# 📢 [PM-Hub] Phase 5 BE(prod) 결과 보고 (2025-10-04)

## ✅ 수행 내역

### 라우터 권한 SSOT 일원화
- `app/core/auth.py`의 `require_roles`만 사용
- `/api/menu`, `/api/reports`, `/api/closing` 라우터에 `Depends(require_roles(["ADMIN"]))` 적용
- 불필요한 `deps.py` 제거

### 라우터 정리
- **menu.py** → ADMIN 전용 메뉴(JSON)
- **reports.py** → Sales Tags 조회 + CSV Export
- **closing.py** → Calendar(month/date_range), `property_code/date_from/date_to/items` 필드 항상 포함

### main.py
- 모든 라우터 include (`me/menu/reports/closing/ota/users/upload/audit`)
- `/api/health` 헬스체크 추가
- CORS 미들웨어 유지
- startup 시 dev 모드에만 안전한 create_all + 임시 컬럼 보강

### 로컬 검증
- `/api/openapi.json` → 200
- 무토큰 → 401
- 토큰 → 200 정상 응답
- `/api/reports/sales-tags` JSON PASS, CSV Export 헤더 PASS
- `/api/closing/calendar` month/date_range 응답에 필드 보장

### 운영 도메인(Nginx 프록시) 검증
- `/api/health` → 200
- `/api/menu` 무토큰 401, 토큰 200 + 메뉴 JSON PASS
- `/api/reports/sales-tags` → 데이터 정상 조회
- `/api/reports/sales-tags/export` → CSV 다운로드 헤더 정상
- `/api/closing/calendar` → month/date_range 모두 정상 응답

### 증빙 스냅샷 & 커밋
경로: `backend/docs/runbooks/phase5/2025-10-04_BE_prod/evidence/`

포함 파일:
- `health.status`, `openapi.status`
- `menu_wo.status`, `menu.json`
- `sales_tags.json`, `sales_tags_export.headers`
- `closing_month.json`, `closing_range.json`

커밋 메시지:
```
Phase5 BE(prod): nginx 프록시 스모크 PASS 증빙(2025-10-04)
```

---

## 📌 BE 전달 요약
- 인증/권한 체계: SSOT(`auth.py`) 기반 정리 완료 → `require_roles(["ADMIN"])`
- 엔드포인트: menu/reports/closing 응답 스펙 확정
- 운영 환경(Nginx 프록시): 토큰 인증 및 모든 주요 API 정상 PASS
- 증빙: `docs/runbooks/phase5/2025-10-04_BE_prod/evidence/*` 저장 및 커밋 완료
