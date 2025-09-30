#  BE-Core 작업 완료 합본 보고 (2025-09-30~10-01)

## 0) 전체 요약
-  `/openapi.json` 복구 (FastAPI 기본 OpenAPI/Docs 강제 노출, 헬스 엔드포인트 `/api/ops/ping`)
-  `/api/me` 인증/스키마 복구 (`Depends(require_user)`, `{ "user": {...} }` 반환, 토큰 없을 시 401)
-  `/api/closing/calendar` 응답에 `items: []` 항상 포함 (month/date_from/date_to 모두 지원)

## 1) 상세 작업 내역

### 1-1) `/openapi.json` 복구
- **변경:**  
  - `app/main.py` → `FastAPI(openapi_url="/openapi.json")` 보장  
  - 헬스 라우트 `/api/ops/ping` 추가  
- **DoD:**  
  - `be_openapi.json` 비어있지 않고 `paths` 키 존재  
- **증빙:**  
  - 스냅샷: `docs/runbooks/snapshots/2025-09-30_2117_pmhub_audit/be_openapi.json`  
  - 커밋:  
    ```
    BE-Core: restore /openapi.json; add /api/ops/ping; snapshot be_openapi.json (2025-09-30_2117)
    ```

### 1-2) `/api/me` 가드·스키마 복구
- **변경:**  
  - `app/core/auth.py` → `require_user()` (헤더 `X-Internal-Token`, 로컬 `dev-admin-token`)  
  - `app/core/me_router.py` → `/api/me` 라우트, `Depends(require_user)` 적용  
  - 응답 스키마 `{ "user": {...} }`  
- **DoD:**  
  - with-token → 200 & `user` 키 존재  
  - without-token → 401  
- **증빙:**  
  - 스냅샷:  
    - `api_me_with_token.json`  
    - `api_me_wo_token.headers`  
  - 커밋:  
    ```
    BE-Core: restore /api/me guard+schema; snapshots (2025-10-01)
    ```

### 1-3) `/api/closing/calendar` 응답 보장
- **변경:**  
  - `app/schemas/closing.py` → `ClosingItem`, `ClosingCalendarResp(items=[])`  
  - `app/operations/closing/router.py` → month=YYYY-MM 처리, date_from/to 처리, 항상 `items` 포함  
- **DoD:**  
  - `api_closing_calendar.json` 내 `items` 키 존재(빈 배열 가능)  
- **증빙:**  
  - 스냅샷: `api_closing_calendar.json`  
  - 커밋:  
    ```
    BE-Core: ensure closing/calendar items key; snapshots (2025-10-01)
    ```

## 2) 검증 명령 요약
```bash
TOK=dev-admin-token

# 1) openapi.json
curl -sI http://127.0.0.1:8000/openapi.json | head -n1

# 2) /api/me
curl -s -o /dev/null -w "%{http_code}\n" -H "X-Internal-Token: $TOK" http://127.0.0.1:8000/api/me   # 200
curl -s -o /dev/null -w "%{http_code}\n"                         http://127.0.0.1:8000/api/me       # 401
curl -s -H "X-Internal-Token: $TOK" http://127.0.0.1:8000/api/me | python -m json.tool | head -n20

# 3) /api/closing/calendar
curl -s -H "X-Internal-Token: $TOK" \
  "http://127.0.0.1:8000/api/closing/calendar?month=$(date +%Y-%m)" \
  | python -m json.tool | head -n40
