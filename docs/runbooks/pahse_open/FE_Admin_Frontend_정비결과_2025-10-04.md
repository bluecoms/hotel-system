# 📢 [PM-Hub] Admin Frontend 정비 결과 보고 (2025-10-04)

## 1️⃣ 주요 변경 사항 (파일/역할별 요약)

### src/App.vue
- 로그인 페이지에서 상단바/사이드바 비노출 → 깨끗한 로그인 화면 구성.
- 네비게이션은 정적 메뉴(`src/router/menu.ts`) 기반 렌더.
- 사이드바 항목에 `:prepend-icon` 적용 → 아이콘 표시.
- 권한 필터링(`ADMIN`, `SUPERADMIN`) 반영.

### src/router/index.ts
- 라우트 이름/경로 정리 (Closing, Reports 등).
- Nav Guard: 미인증 시 `/login` 리다이렉트, 권한 미충족 시 `/forbidden`.

### src/router/menu.ts
- 정적 메뉴 정의 (아이콘/roles 포함).
- 그룹: Closing, OTA, Reports, Admin / 단일: Users (SUPERADMIN 전용).

### src/views/Auth/Login.vue
- 풀스크린 카드형 로그인 UI (상단바/사이드바 제거).
- 개발 편의: 토큰 입력 자동 프리필 (없으면 빈 문자열).

### src/views/Dashboard.vue
- KPI 카드/진행도/상단 툴바 구현 (rooms/front/fnb/exp/pay).
- `getDashboardKPI`, `getClosingDay` 연동.

### src/views/closing/*
- `Board.vue`, `Closing.vue`(캘린더) 등 정리.
- `Closing.vue`의 중복 `catch` 문 제거.

### src/ui/*
- 경량 UI 컴포넌트 추가: `KpiCard.vue`, `ProgressRing.vue`, `Button.vue`, `Badge.vue`, `Tooltip.vue`, `ProgressBar.vue`.

### src/services/*
- `reports.ts`: `getDashboardKPI`, `getSalesTags`, `exportSalesTags`.
- `closing.ts`: `getClosingDay`, `setClosingDayStatus(FormData PUT)`.

---

## 2️⃣ API 계약 (BE 합의 스펙)

| 기능 | 메서드/경로 | 비고 |
|------|--------------|------|
| Dashboard KPI | `GET /reports/dashboard-kpi?date=YYYY-MM-DD&property_code=MOP` | 데이터 없으면 200 + 기본값(0) |
| Closing Day 상태 | `GET /closing/day?date=YYYY-MM-DD&property_code=MOP` / `PUT /closing/day` | FormData: date, status('OPEN'|'CLOSED'), property_code |
| Sales Tags | `GET /reports/sales-tags`, `GET /reports/sales-tags/export` | Export는 Blob(csv) |

> 참고: `rooms-split`, `fnb-summary` 등은 미도입 상태.

---

## 3️⃣ 타입/빌드 오류 정리

- `toastError(err.value)` → `toastError(err.value || '오류')`로 통일.
- `Closing.vue` 중복 `catch{}` 제거.
- `Upload/SalesFront.vue`는 폐지 → 리다이렉트 처리.

---

## 4️⃣ 사이드바/네비게이션 개선

- 정적 메뉴 사용으로 `/ota/list`, `/admin/ota/commission` 등이 노출되지 않음.
- 로그인 페이지(`/login`)는 상단바/사이드바 미표시.
- 아이콘 노출: `v-list-item :prepend-icon="m.icon"` 적용.

---

## 5️⃣ 경로/폴더 구조

- 주요 파일 유지:
  - `src/views/Dashboard.vue`
  - `src/views/closing/{Board,Closing,Detail,History,Index}.vue`
  - `src/views/Reports/SalesTags.vue`
  - `src/views/Auth/Login.vue`
  - `src/views/Users/Users.vue`
- 공용 UI: `src/ui/` 폴더 일괄 추가.

---

## 6️⃣ 운영/개발 편의

- 로그인 토큰 자동 저장/불러오기(localStorage.ADMIN_TOKEN).
- 기본 Property: `MOP`.
- KPI 자동 퍼센트 계산 (ROOMS_BY_PROPERTY 기준).

---

## 7️⃣ 제거/리다이렉트 처리

- `/admin/upload/sales-front` → `/closing/board` 리다이렉트.
- OTA 하위 개별 화면(`Channel List`, `Commission`) 제거 → `Overview` 통합.

---

## 8️⃣ QA 체크리스트

- [x] 로그인 시 상단바/사이드바 미표시 → 정상.
- [x] 메뉴: Dashboard/Closing/OTA/Reports/Admin/Users(권한별) 정상 노출.
- [x] Dashboard KPI 로딩/리프레시 정상.
- [x] Closing Calendar 월 이동/상태 칩/권한별 버튼 정상.
- [x] Sales Tags 조회/CSV Export 정상 (빈 응답도 OK).
- [x] Nav Guard: 미인증 `/login`, 권한없음 `/forbidden` 정상 동작.

---

## 9️⃣ 남은 과제 (선택)

- Admin 하위 모듈(HR/Finance/Inventory): Blank 라우팅 유지.
- KPI 카드의 “상세로 이동” 링크 추가 여부 검토.
- 테마 토큰(`--brand-*`, `--ink-*`)은 현 상태 유지.

---

## 🔧 FE 적용 안내

> 아래 파일을 교체/반영하면 동일 환경 복원 가능

- `src/App.vue`
- `src/router/index.ts`
- `src/router/menu.ts`
- `src/views/Auth/Login.vue`
- `src/views/Dashboard.vue`
- `src/views/closing/*`
- `src/ui/*`
- `src/services/{reports,closing}.ts`

**빌드에러 발생 시** → `toastError(err.value || '오류')` 누락 여부 확인.
