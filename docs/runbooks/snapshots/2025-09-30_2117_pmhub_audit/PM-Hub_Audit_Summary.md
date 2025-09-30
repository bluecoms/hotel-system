# PM-Hub T0 Audit Summary

## 1) BE-Core
- Python/Pip: (see be_python_version.txt / be_pip_version.txt)
- Alembic: heads/current 확인 (be_alembic_status.txt)
- API 기동/스냅샷: openapi.json, /api/me, /api/menu, /api/closing/calendar 캡처

## 2) FE-Core
- axios 사용 여부: fe_scan_axios.txt (있으면 규약 위반)
- 인증/가드/리다이렉트 단서: fe_scan_internal_token.txt, fe_scan_requiresAuth.txt, fe_scan_401.txt, fe_scan_redirect.txt

## 3) QA
- /api/me 토큰 유/무 상태코드: qa_status_codes.txt (무토큰 401이 정상)

## 4) 결론(초안)
- BE DoD: alembic upgrade head 통과 & 핵심 API 200 OK면 Pass
- FE DoD: axios 흔적 0, requiresAuth/401→/login 리다이렉트 근거 확인되면 Pass
- QA DoD: 증빙 파일(이 폴더) 커밋 & 체크리스트 업데이터

> 세부 내용은 개별 파일 참고. 다음 액션: 미통과 항목만 지정/지시.
