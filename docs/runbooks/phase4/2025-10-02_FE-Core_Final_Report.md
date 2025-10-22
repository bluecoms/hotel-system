# 📄 FE-Core 전달사항 최종 보고 (2025-10-02)

## 1) 공통 / 환경
- **헤더**
  - `X-Internal-Token`: 로그인 후 FE가 로컬스토리지(`ADMIN_TOKEN` / `internalToken`)에서 읽어 `http.ts`가 자동 첨부.
  - `Accept-Language: ko-KR` 기본 첨부(서버 로깅/에러 메시지 로캘).

- **ENV**
  - `VITE_API_BASE_URL` 없으면 `/api` 사용.
  - Dev 프록시: `vite.config.ts`가 `/api → http://127.0.0.1:8000` 그대로 포워드(리라이트 없음).

- **토스트**
  - 전역 `ToastHost` 사용, `useToast().success()` / `.error()` 호출.

- **권한/라우팅**
  - 가드: 토큰 없으면 `/login` 리다이렉트.  
  - SUPERADMIN은 권한 체크 우회.  
  - `/api/me`의 `user.roles` 기반 검사. (DEV는 `X-Debug-Role` 허용, PROD는 무시)

---

## 2) 라우트(프런트)
- `/admin/upload/sales-front`
- `/admin/reports/sales-tags`
- `/admin/ota/list`
- `/admin/ota/commission`

👉 사이드메뉴는 `/api/menu` 실패 시 Fallback으로 위 항목 노출.

---

## 3) 스크린별 연동 포인트

### (A) Sales Upload — sales_front
- 업로드: `POST /api/upload/sales_front`  
  - FormData: `file`, `dry_run=1|0`
  - 드라이런 성공 시 `"적용"` 버튼 노출 → 다시 `dry_run=0` 호출.
- 에러 토스트: 서버 `detail` 우선.

### (B) Reports — Sales Tags
- 조회: `GET /api/reports/sales-tags?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD`
- CSV: `GET /api/reports/sales-tags/export?...`
- 응답 배열/래핑 모두 방어(이미 반영).  
- 합계(Total) 카드/푸터 표시.

### (C) OTA — Channels / Commission
- **채널 목록:** `GET /api/ota/channels`  
- **채널 생성(필요 시):** `POST /api/ota/channels { code, name }`  
- **커미션 목록:** `GET /api/ota/commissions?...`  
- **커미션 생성:** `POST /api/ota/commissions { channel, valid_from, valid_to, rate, note }` (FE는 0~100%)  
- **커미션 수정:** `PUT /api/ota/commissions/{id}`  
- **커미션 삭제:** `DELETE /api/ota/commissions/{id}`  
- 서버 저장은 rate를 0~1로 변환하지만, **FE는 항상 퍼센트(0~100)로 표시/입력.**

---

## 4) 처리된 이슈 & FE 체크리스트

### ✅ 해결된 사항
- `/api` 404 → BE 라우터 미포함 → 고정 패치, FE 추가 작업 불필요.
- 메뉴 Fallback, i18n 누락 → 하드코딩 OK, Accept-Language 유지.
- `StateBlock` 전역 등록 누락 → 각 뷰 import 후 `<StateBlock/>` 사용으로 수정.
- Pinia `hasRole` 오류 → `auth.user?.roles?.includes('SUPERADMIN')`로 교체.
- `ota_channels` NOT NULL 삽입 오류 → 서버 POST가 created/updated 보정.
- Dev 환경 401 → 로그인 토큰 미설정 문제, `/login` 폼에서 해결.
- CSV 다운로드 Mixed Content → Dev 경고, 운영 HTTPS로 해결.
- `v-dialog` 바인딩 오류 → 올바른 선언으로 교정.

### 🔎 FE 확인 포인트
- 로그인 후 로컬스토리지 `ADMIN_TOKEN` 세팅 확인 → `/api/me` 200.
- Dev 모든 API는 `/api/...` 경로 → 프록시 8000 포워드.
- 커미션 폼 UI: density="comfortable" + max-width="720" 다이얼로그 적용 완료.

---

## 5) 에러 메시지 매핑 (FE 토스트)
- 400/422 → 서버 `detail` 그대로 (입력값 오류, 기간 역전)
- 404 → “채널 코드를 찾을 수 없습니다.”
- 409 → “기간이 겹칩니다.”
- 기타 → “저장에 실패했습니다.” / “목록을 불러오지 못했습니다.”

---

## 6) 빠른 기능 테스트 스크립트

**로그인 (DEV)**  
- /login → 토큰 입력(dev-admin-token) → Role: ADMIN 선택 → Login.

**채널 생성**
```bash
curl -H "X-Internal-Token: <토큰>" -H "Content-Type: application/json"   -d '{"code":"BKG","name":"Booking.com"}'   http://localhost:8000/api/ota/channels
```

**커미션 생성**
- /admin/ota/commission → 채널 BKG 선택, 기간/퍼센트 입력 → 저장.
- 중복 기간 시도 → 409 안내 확인.

**Sales Upload**
- /admin/upload/sales-front → CSV 드라이런 → 적용.

**Sales Tags**
- /admin/reports/sales-tags → 기간 선택 → 조회/합계 확인 → CSV Export.

---

## 7) UX 건의 (선택)
- 커미션 폼 날짜 필드: `type="date"` 적용 검토.
- 채널 코드: `v-autocomplete` + 소문자 입력 시 자동 대문자 변환.

---

✅ **결론:** FE-Core 모든 연동/검증 완료.  
DoD 기준 충족, 스크린샷 증빙 커밋됨.  
