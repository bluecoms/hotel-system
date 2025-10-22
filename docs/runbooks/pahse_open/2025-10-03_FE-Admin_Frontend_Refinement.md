# 📢 [PM-Hub] Admin Frontend 정비 결과 보고 (FE-Core) — 2025-10-03

## 1) 공통 인프라/환경
- **.env**
  - `VITE_API_BASE_URL` : API 베이스 (예: `/api` 또는 `http://host:port/api`)
  - `VITE_ADMIN_TOKEN` *(선택)* : 초기 내부 토큰 주입 시 사용 (없으면 `localStorage`에서 로드)
- **파비콘**: `public/favicon.ico` 추가(404 제거)

---

## 2) HTTP 레이어 통합 — `src/services/http.ts`
- **토큰 키 표준화**
  - 현행 키: `ADMIN_TOKEN` (localStorage)
  - 레거시 호환: `internalToken` ⇒ **동기 저장/삭제** 유지
- **자동 헤더**
  - `X-Internal-Token: <token>`
  - (DEV) `X-Debug-Role: <role>` — `http.setDebugRole('ADMIN'|'SUPERADMIN'|null)` 지원
  - `Accept: application/json`, `Accept-Language: ko-KR`
- **401 처리 공통화**
  - 토큰/세션 정리 후 **`/login?redirect=<현재경로>`** 로 1회 이동(루프 방지)
- **반환 타입**
  - JSON 우선, 204 처리 포함, **Blob 다운로드 유틸(`getBlob`)** 제공
- **사용 규칙**
  - 화면은 **반드시** `import http from '@/services/http'` (named import 금지)

---

## 3) 라우터 구성 — `src/router/index.ts`
- **지연 로딩 + 역할 가드 적용**
- **경로 매핑(필수)**
  - `/` → Dashboard
  - `/closing` → Closing Calendar *(roles: ['ADMIN','SUPERADMIN'])*
  - `/closing/board` → Closing Board *(roles: ['ADMIN','SUPERADMIN'])*
  - `/ota` → OTA Management *(roles: ['ADMIN','SUPERADMIN'])*
  - `/ota/list` → OTA Channel List *(roles: ['ADMIN','SUPERADMIN'])*
  - `/admin/reports/sales-tags` → Sales Tags Report *(roles: ['ADMIN','SUPERADMIN'])*
  - `/admin/upload/sales-front` → Sales Front Upload *(roles: ['ADMIN','SUPERADMIN'])*
  - `/admin/users` → Users *(roles: ['SUPERADMIN'])*
- **네비 가드**
  - 진입 시 `auth.bootstrap()` 선 호출(401 루프 방지)
  - 인증 필요(기본값 `true`) + 역할 체크
  - 문서 제목: `Hotel Admin — ${to.meta.title}` 자동 세팅
- *(옵션)*
  - `/admin/ota/commissions` → 커미션 화면
  - `/admin/keywords` → 키워드 룰 관리/테스트

---

## 4) 사이드바 메뉴 정적화 — `src/router/menu.ts` + `App.vue`
- **메뉴 소스**: `src/router/menu.ts` (정적 정의) → **/api/menu 의존 제거**
- **노출 제어**: 메뉴 스토어가 **auth.roles + 라우터 메타**로 필터링해 `visibleItems` 생성
- **App.vue**
  - `<v-navigation-drawer :items="menu.visibleItems">` 바인딩
  - 전역 `<ToastHost/>`, `<ConfirmHost/>` **1회 삽입 완료**
  - 우상단 프로필: **Logout** 시 토큰 클리어 + `/login` 이동

---

## 5) 화면별 핵심 변경
### Closing
- Board / Calendar **정상 동작**
- 업로드/버전/복구/무거래일 등록 로직 연결
- **SUPERADMIN만** Day Close/Reopen 버튼 노출
- 헤더 검증(간단 CSV 헤더 점검) 및 **다중 파트 업로드** 지원(F&B 페어 등)

### OTA
- 탭 3개: **Sales / Channel Aliases / Channel Fees**
- 기간 쿼리 **URL 동기화**(`router.replace`) → 새로고침 시 상태 유지
- **CSV Export** 내장
- Alias/Fee **CRUD 연결** (키: `sales.channel.alias`, `sales.channel.fee`)

### Users
- **목록/페이징/검색**
- **SUPERADMIN:** Activate/Deactivate, Employee Import, Map Employee
- 에러/성공 메시지 **표준화**

---

## 6) 메시지/에러 처리 (DoD 반영)
- 전역 `<ToastHost/>` 사용
- 각 화면은 `useToast()`로 **성공/에러 한국어 메시지** 노출
- 에러 우선순위: `response.data.detail` → `error.message` → 기본 문구
- 기존 `v-alert`는 유지 가능하되, **토스트 우선**으로 통일 권장

---

## 7) 테스트 가이드(로컬)
1. `.env`의 `VITE_API_BASE_URL` 확인
2. `localStorage.ADMIN_TOKEN` 또는 `.env VITE_ADMIN_TOKEN` 설정
3. 페이지 접근
   - 무토큰 → `/login?redirect=...` 이동 확인
   - 토큰 유효 → 대시보드 및 **메뉴(역할 필터링)** 노출
4. Closing/OTA/Users **CRUD 액션** 수행 → 토스트 메시지/상태 확인

---

## 8) 알려진/선택 과제
- `public/favicon.ico` 추가(이미지 제공 시 교체 가능)
- 커미션/키워드 관리 라우트는 필요 시 활성화
- 일부 화면의 하단 `v-alert` → **토스트로 점진 통일**

---

## ✅ 결론
- HTTP/라우팅/메뉴/화면별 기능까지 **정비 완료**
- 에러/성공 메시지, 권한/가드, URL 상태 동기화 **일관성 확보**
- **DoD 충족**, MVP 빌드 & 스냅샷 진행 가능
