# 📢 [PM-Hub] BE-Core Phase 4 완료 보고 (2025-10-03)

## 1) 완료 범위

- **Alembic 마이그레이션**
  - `sales_front` 테이블 + 유니크/인덱스 보장
    - `ux_sales_front_date_tag(business_date, tag)`
    - `idx_sales_front_date`, `idx_sales_front_tag_date`
  - `audit_logs` 테이블 생성

- **Upload API**
  - `POST /api/upload/sales_front`
  - CSV 업로드(dry-run 지원), i18n 에러 메시지 통일
  - 중복 시 `409`, 성공 시 `null`
  - 감사로그: `SALES_FRONT_UPLOAD`

- **Export API**
  - `GET /api/reports/sales-tags/export`
  - 기간별 태그 합계 CSV 반환
  - 파일명: `sales-tags_YYYYMMDD-YYYYMMDD.csv`
  - Content-Type: `text/csv; charset=utf-8`

- **OTA API 정리**
  - 채널/커미션 CRUD
  - 리스트 페이징 (`limit/offset/total`)
  - 기간 겹침 검증
  - 감사로그 기록 (`OTA_CHANNEL_CREATE`, `OTA_COMMISSION_CREATE/UPDATE`)

- **공통 유틸**
  - `app/core/audit.py`: 감사 로깅
  - `app/core/auth.py`: `require_user`, `require_roles(["ADMIN"])`
  - `app/core/i18n.py`, `app/core/locale.py`: 다국어(i18n) 훅
  - `set_lang`, `_t()` 기반 detail 메시지

- **기타**
  - 대시보드/클로징/업로드 파이프 보강
  - `.gitignore` 정리(DB/캐시/node_modules 제외)

---

## 2) 적용 및 실행 절차

```bash
cd /volume1/web/hotel-system/backend
. ../venv39_py39/bin/activate

# Alembic 마이그레이션 적용
alembic upgrade head
```

생성/보장 객체:

- `sales_front(business_date TEXT, tag TEXT, amount INTEGER)`
- `audit_logs(id, ts, actor, action, target, meta_json)`
- 인덱스: `ux_sales_front_date_tag`, `idx_sales_front_date`, `idx_sales_front_tag_date`

서버 재시작 (uvicorn or systemd) 후 API 이용 가능.

---

## 3) 엔드포인트 요약

### Upload
- `POST /api/upload/sales_front`
- Form: `file`(CSV), `dry_run`
- 헤더: `X-Internal-Token` 필요
- 응답: 성공 시 `null`, 에러는 i18n 메시지
- 감사로그 기록

### Reports Export
- `GET /api/reports/sales-tags/export?date_from=&date_to=`
- CSV 스트리밍: `tag,sales_amount,count`
- 파일명: `sales-tags_YYYYMMDD-YYYYMMDD.csv`

### OTA
- `GET /api/ota/channels?limit=&offset=` → `{ total, items }`
- `POST /api/ota/channels` → 중복 시 400
- `GET /api/ota/channels/{id}/history`
- `GET /api/ota/commissions?...&limit&offset=` → `{ total, items }`
- `POST /api/ota/commissions` → 기간 겹침 409, 역전 422
- `PUT /api/ota/commissions/{id}` → 부분 수정
- 감사로그 기록

---

## 4) 요청 헤더 (공통)

- `X-Internal-Token`: 필수 (운영)
- `X-Debug-Role`: DEV에서만 허용 (기본 ADMIN)

---

## 5) 응답/에러 정책

- 400: 입력 형식 오류
- 401: 인증 실패
- 403: 권한 없음
- 404: 대상 없음
- 409: 리소스 충돌(중복/기간 겹침)
- 422: 유효성 오류(기간 역전 등)

모든 에러: `{"detail":"…"}`  
메시지 다국어(i18n) 적용 (ko-KR → 한국어)

---

## 6) FE 연동 포인트

- 업로드 성공 시 `null` → 토스트 “업로드 완료”
- 409/422 시 메시지 기반 처리
- Export 파일명 고정 → 프론트 rename 불필요
- OTA 목록 페이징 → `total` 기반 페이지네이션
- FE http 클라이언트: 자동으로 `X-Internal-Token` 첨부

---

## 7) QA 체크리스트

- 업로드 정상 → 200 + 감사로그
- dry_run → DB 미반영
- 중복 업로드 → 409
- Export → CSV 다운로드 OK
- OTA → CRUD + 페이징 검증
- 에러 메시지 한국어 일관성

---

## 8) 코드 구조 (핵심)

- `app/routers/upload.py` — 업로드
- `app/routers/reports.py` — Export
- `app/routers/ota.py` — OTA
- `app/core/auth.py` — 인증/권한
- `app/core/audit.py` — 감사로깅
- `app/core/i18n.py`, `app/core/locale.py` — 다국어
- `alembic/versions/*phase4_upload_export_audit_paging*.py`

---

✅ **결론**: BE-Core Phase 4 목표 범위 **모두 구현/적용 완료**.  
➡️ FE는 Upload/Export/OTA 페이징 연동 및 메시지 처리만 반영하면 됨.  
