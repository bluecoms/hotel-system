# 🟩 MVP 인수 — 구현/개선 요약 보고

## 📌 개요
- 보호 라우트 + 인증 플로우 정비  
- `/api/me` 표준 응답 고정  
- Closing 캘린더 스키마/라우터 분리  
- FE 라우터 가드·권한·로그아웃 정상화  
- DEV 환경 역할 에뮬(`X-Debug-Role`) 지원  

---

## 🔧 변경 사항

### 백엔드
- **`app/core/auth.py` 신설/정비**
  - `require_token`: 무토큰 → 401, `dev-admin-token` 허용
  - `current_user`: `X-Debug-Role` 직접 읽음(대소문자 모두 허용), 기본=ADMIN
  - Settings: `.env`의 추가 키 무시(`extra="ignore"`)  

- **`app/core/me_router.py` 추가**
  - `GET /api/me` → `{ "user": { email, name, roles[] } }` 반환  

- **CORS**: `allow_headers`에 `X-Internal-Token`, `X-Debug-Role` 포함  

- **Closing 분리**
  - `app/schemas/closing.py` (또는 `app/operations/closing/schemas.py`)
  - `ClosingItem`, `ClosingCalendarResp(items: List[...] = [])`
  - `GET /api/closing/calendar`: month/date_from~date_to → 항상 `items: []` 보장  

---

### 프런트엔드
- **`src/router/index.ts`**
  - `meta.roles`: 문자열 배열 통일(`['ADMIN','SUPERADMIN']`)
  - 가드: 대소문자 정규화, SUPERADMIN 우선 통과, 미인증→/login  

- **`src/services/http.ts`**
  - `X-Internal-Token` + `X-Debug-Role` 자동 부착
  - 메모리 변수 + `localStorage.debugRole` 반영  

- **`src/stores/auth.ts`**
  - `/api/me` 스키마 대응(`{user:...}` / 직접 객체 모두 수용)
  - 중복 bootstrap 방지, 표시명 폴백
  - Logout: 토큰/디버그롤 제거 + `/login` 이동 + 이후 `/api/me` 미호출  

---

## 📝 운영 메모
- DEV 토큰: `dev-admin-token`
- DEV 역할 에뮬:
  - 헤더: `X-Debug-Role: ADMIN | SUPERADMIN`
  - FE 콘솔: `localStorage.setItem('debugRole','SUPERADMIN')`
- 실배포 전환 시: `require_user` → JWT 검증으로 교체 (헤더 기반 유지)  

---

## ✅ 검증 결과 (통과)
- `/api/me`
  - with token → 200
  - without token → 401
  - `X-Debug-Role: SUPERADMIN` → `roles=["SUPERADMIN"]`  

- **FE 동작**
  - ADMIN → `/closing/board` 접근 OK, `/admin/users`는 403
  - SUPERADMIN → `/admin/users` 접근 OK
  - Logout → `/login` 이동, 저장 키 제거, 로그인 화면에서 `/api/me` 미호출  

---

## 📋 DoD 체크리스트
- [x] 보호 라우트: `Depends(require_user)` 강제 보호
- [x] `/api/me` = `{ user: {...} }` 스키마 반환
- [x] Closing 캘린더 응답 = 기본 `items: []` 보장
- [x] FE 라우팅 가드/권한/로그아웃 정상 동작
- [x] DEV 역할 에뮬 및 토큰 플로우 문서화  

---

👉 결론: **MVP 인증/권한 플로우 & Closing 캘린더 분리 작업 인수 조건 충족 (PASS)**
