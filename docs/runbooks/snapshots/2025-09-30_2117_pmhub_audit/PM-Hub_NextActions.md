# PM-Hub Next Actions (Auto-draft)

아래 체크에서 **FAIL**인 항목만 골라 그대로 실행/보고:

## BE-Core
- /api/me 무토큰 401 실패 → 인증가드 확인(미들웨어/의존성).
- /api/me with token 실패 → INTERNAL_API_TOKEN 검증 또는 /api/me 핸들러 스키마 확인.
- /api/menu 실패 → 라우터/권한 필터/스키마 확인.
- closing calendar items 누락 → /api/closing/calendar 응답 스키마/쿼리 파라미터(month vs date_from/to) 확인.
- Alembic 상태 미수집/비정상 → alembic upgrade head 재검증, 다중 head 발생 시 병합.

## FE-Core
- axios 흔적 발견 → 전량 제거 후 fetch 기반 http.ts로 통일.
- X-Internal-Token 삽입 코드 없음 → http.ts에 헤더 주입 로직 추가.
- requiresAuth 미검출 → 라우터 메타 가드 추가.
- 401 처리/리다이렉트 미검출 → http.ts 전역 401 핸들러에서 /login 리다이렉트 구현.

## QA
- 상태코드 수집 미흡 → qa_status_codes.txt 생성 절차 재수행(curl -w %{http_code}).
