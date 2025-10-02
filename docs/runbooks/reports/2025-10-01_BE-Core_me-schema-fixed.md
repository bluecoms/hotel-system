#  BE-Core 완료 보고 — /api/me 응답 스키마 확정 (2025-10-01)

## 0) 요약
- **작업 개요:** `/api/me` 응답 스키마 고정
- **판정:** DoD PASS
- **근거:** FE 가드가 요구하는 스키마와 정확히 일치하도록 고정

## 1) 변경 요지
- `app/core/me_router.py` 수정
  - 응답을 `{ "user": { "email": "dev@local", "roles": ["ADMIN"] } }` 로 고정
  - `roles`는 대문자 배열, 최소 `["ADMIN"]` 포함
- 인증은 **`X-Internal-Token` 헤더만** 사용 (`require_user` 경유)
- 토큰 누락 → 401 (기존 QA 확인 유지)

## 2) DoD 체크
- [x] with-token (`dev-admin-token`) → 200 OK
- [x] 응답에 최상위 `user` 키, `roles=["ADMIN"]`
- [x] without-token → 401 Unauthorized

## 3) 증빙
- 스냅샷:  
  `docs/runbooks/snapshots/2025-10-01_pmhub_audit/api_me_with_token.json`
- Git commit:  
