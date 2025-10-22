# Hotel System 백엔드 폴더 구조 (2025-10-11 기준 최신 SSOT 반영판)

> **문서 목적 (SSOT)**
>
> 이 문서는 백엔드 폴더 구조의 **단일 진실 원본(Single Source of Truth)** 입니다.
> 모든 설계/개발/리팩터링/QA 문서는 본 구조를 기준으로 작성·검증합니다.
> “⚙️ 예정” 항목이 구현되면 반드시 본 문서를 **즉시 갱신**합니다.

- 문서 버전: `2025-10-11` (Phase 1 finalized → Phase 2 준비판 포함)
- 적용 범위: backend/app 하위 전체 (엔진/어댑터/모델/라우터/서비스/스키마/DB infra)
- 유지 책임: **BE-Core** (SSOT Merge Engine/DB 변경 시 갱신 주체)

---

## 1) Canonical Tree

```
backend/app/
├─ core/
│  ├─ auth.py
│  ├─ locale.py
│  ├─ i18n.py
│  ├─ hashing.py
│  ├─ settings.py
│  ├─ settings_merge.py          # ⚙️ 예정
│  ├─ dev_bootstrap.py           # ✅ startup hook / seed 등록
│  ├─ audit.py                   # ✅ core-level 로깅 유틸
│  ├─ normalize.py               # ✅ CSV 파서 공통화
│  ├─ normalize_bank.py          # ✅ 입금전용 정규화기
│  ├─ employees_import.py        # ✅ 인사 데이터 import 유틸
│  ├─ payments.py                # ✅ 결제처리/테스트용
│  ├─ me_router.py               # ✅ /api/me self정보
│  ├─ keywords.py                # ✅ 키워드 관리용
│  ├─ snapshot.py                # ✅ 구조/데이터 스냅샷
│  └─ __init__.py
│
├─ datasets/
│  ├─ adapters/
│  │  ├─ base.py                 # ✅ DatasetAdapter, CanonRecord
│  │  ├─ rooms_status.py         # ✅ RoomsStatusAdapter
│  │  ├─ sales_front.py          # ⚙️ 예정
│  │  ├─ fnb_tenders.py          # ⚙️ 예정
│  │  ├─ fnb_items.py            # ⚙️ 예정
│  │  ├─ expenses.py             # ⚙️ 예정
│  │  ├─ bank_ledger.py          # ⚙️ 예정
│  │  └─ __init__.py             # ✅ 자동 export
│  └─ schemas/
│     ├─ rooms_status.py         # ⚙️ 예정
│     ├─ sales_front.py          # ⚙️ 예정
│     ├─ fnb_tenders.py          # ⚙️ 예정
│     ├─ fnb_items.py            # ⚙️ 예정
│     ├─ expenses.py             # ⚙️ 예정
│     ├─ bank_ledger.py          # ⚙️ 예정
│     └─ __init__.py
│
├─ db/
│  ├─ base_class.py              # ✅ DeclarativeBase
│  ├─ base.py                    # ✅ Base (metadata)
│  ├─ session.py                 # ✅ get_db
│  └─ __init__.py
│
├─ merge_engine/
│  ├─ engine.py                  # ✅ normalize→parse→execute
│  ├─ repository.py              # ✅ Canon/History CRUD
│  ├─ policies.py                # ✅ 중복/누락 정책 (Phase 2 준비)
│  ├─ planner.py                 # ✅ 드라이런 계획 (Phase 2 준비)
│  ├─ diff.py                    # ✅ Canon 대비 변경 계산 (Phase 2 준비)
│  ├─ audit.py                   # ⚙️ 예정
│  └─ __init__.py                # ✅ 자동 export
│
├─ models/
│  ├─ base.py
│  ├─ mixins.py
│  ├─ audit.py                   # ✅ merge_batches, merge_changelog
│  ├─ canon.py                   # ✅ rooms_status_canon, rooms_status_history
│  ├─ closing.py
│  ├─ bank.py
│  ├─ board.py
│  ├─ keyword.py
│  ├─ ota.py
│  ├─ user.py
│  ├─ role.py
│  ├─ employee.py
│  └─ __init__.py                # ✅ export 통합
│
├─ routers/
│  ├─ upload.py
│  ├─ closing.py
│  ├─ bank.py
│  ├─ reports.py
│  ├─ reports_sales.py
│  ├─ reports_bank.py
│  ├─ board.py
│  ├─ users.py
│  ├─ employees.py
│  ├─ menu.py
│  ├─ audit.py
│  ├─ keywords.py
│  ├─ ota.py
│  ├─ merge.py                   # ✅ /api/merge/batches, /api/merge/logs
│  ├─ debug.py
│  ├─ health.py
│  └─ __init__.py                # ✅ include_router export
│
├─ schemas/
│  ├─ closing.py
│  ├─ board.py
│  ├─ reports.py
│  ├─ merge.py                   # ✅ MergeBatch/ChangeLog/DryRun/Exec
│  ├─ users.py
│  ├─ employees.py
│  ├─ keywords.py
│  ├─ ota.py
│  ├─ auth.py
│  └─ __init__.py
│
├─ services/
│  ├─ merge_service.py           # ✅ router → engine bridge
│  ├─ upload_service.py
│  ├─ upload_apply.py            # ⚙️ 레거시(폐기 예정)
│  └─ __init__.py                # ✅ 자동 export
│
├─ main.py                       # ✅ 라우팅/미들웨어/예외표준
└─ __init__.py
```

---

## 2) 상태 요약 (Phase 1 기준 → Phase 2 준비 반영)

| 모듈/경로                     | 상태 | 설명 |
|------------------------------|------|------|
| `core.hashing`               | ✅   | `make_key_hash`, `make_record_hash` 사용 |
| `merge_engine.engine`        | ✅   | Dry-run/Execute 통합, Canon/History 반영 |
| `merge_engine.repository`    | ✅   | Canon/History CRUD + MergeBatch/ChangeLog 기록 |
| `merge_engine.policies`      | ✅   | 중복/누락 정책(first/last/latest, soft/hard) |
| `merge_engine.planner`       | ✅   | 드라이런 계획 산출(inserted/updated/deleted/noop) |
| `merge_engine.diff`          | ✅   | key_hash 기반 변경 계산 + 정책 적용 |
| `services.merge_service`     | ✅   | Router → Engine 브리지, 예외/로그 표준화 |
| `models.audit.py`            | ✅   | ORM: `merge_batches`, `merge_changelog` |
| `models.canon.py`            | ✅   | `rooms_status_canon`, `rooms_status_history` |
| `routers.merge.py`           | ✅   | `/api/merge/batches`, `/api/merge/logs/{id}` |
| `schemas.merge.py`           | ✅   | DryRun/Execute/Batch/ChangeLog 스키마 |
| `datasets.schemas/*`         | ⚙️   | 예정: dataset별 Pydantic schema |
| `merge_engine.audit.py`      | ⚙️   | 예정: 감사 리포트/헬퍼 |

> **원칙:** “⚙️ 예정” 구현 시 표와 트리의 해당 파일 상태를 ✅로 즉시 갱신.

---

## 3) 변경 관리 원칙

- **문서 위치(SSOT)**: `docs/runbooks/structure_backend_YYYY-MM-DD.md`
  - 본 문서는 **날짜 버전 누적** (덮어쓰기 금지)
  - 최신판을 README/CONTRIBUTING에 링크
- **갱신 트리거**
  1) Alembic 마이그레이션 추가/변경 (테이블/인덱스/제약 포함)  
  2) 새 모듈/파일 생성 (예: `merge_engine.diff`)  
  3) 라우터/서비스 추가 또는 API 계약 변경  
  4) Phase 전환 (0.5 → 1, 1 → 2 등)
- **코드 주석 버전 헤더 예시**
  ```python
  # version: 2025-10-11 Phase 1 finalized (+ Phase 2 prep)
  ```
- **폴더 계층 변경 금지**
  - 기존 계층 하위에만 파일 추가
  - 이동/이름 변경은 RFC 승인 필요

---

## 4) 운영 점검/스냅샷 절차

```bash
# 1) 구조 스냅샷 저장
cd /volume1/web/hotel-system/backend/app
tree -L 3 > ../../../docs/runbooks/snapshots/backend_tree_$(date +%F).txt

# 2) 최신 SSOT 문서와 차이 비교
diff -u   docs/runbooks/structure_backend_2025-10-11.md   docs/runbooks/snapshots/backend_tree_$(date +%F).txt | less
```
* 차이가 있으면 본 문서를 **우선 갱신**하고 커밋 메시지에 `SSOT:structure updated` 포함.

---

## 5) 프런트엔드 연동 주의사항 (요약)

- 업로드 엔드포인트(공통): `POST /api/upload/{dataset}`
  - 사용 가능: `rooms_status` (확장 예정: `sales_front`, `fac_sales`, `expenses`, `bank_ledger` …)
- 공통 form 필드:

| 필드             | 의미                 | 비고           |
|------------------|----------------------|----------------|
| `business_date`  | YYYY-MM-DD           | **필수**       |
| `property_code`  | 예: MOP              | 기본 MOP       |
| `dry_run`        | 0/1                  | 기본 1         |
| `split_by_date`  | 0/1                  | 옵션           |
| `source_kind`    | daily/weekly/monthly | 기본 daily     |
| `file`           | CSV (multipart)      | **필수**       |

### 올바른 업로드 예시 (브라우저/프런트)

```ts
// TypeScript/React 예시
async function uploadDataset(
  dataset: "rooms_status"|"sales_front"|"fac_sales"|"expenses"|"bank_ledger",
  file: File,
  opts: {
    business_date: string;
    property_code?: string;
    dry_run?: 0 | 1;
    source_kind?: "daily" | "weekly" | "monthly";
  }
) {
  const form = new FormData();
  form.append("business_date", opts.business_date);
  form.append("property_code", opts.property_code ?? "MOP");
  form.append("dry_run", String(opts.dry_run ?? 1));
  form.append("source_kind", opts.source_kind ?? "daily");
  form.append("file", file, file.name);

  const res = await fetch(`/api/upload/${dataset}`, {
    method: "POST",
    headers: {
      "X-Internal-Token": "dev-admin-token", // 운영에서는 실제 토큰 적용
    },
    body: form, // ✅ multipart/form-data (Content-Type 자동 설정)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Upload failed (${res.status})`);
  }
  return res.json();
}
```

### 올바른 업로드 예시 (cURL)

```bash
# Dry-run
curl -s -H "X-Internal-Token: dev-admin-token"   -F business_date=2025-10-11   -F property_code=MOP   -F dry_run=1   -F "file=@backend/_uploads/rooms_status_MOP_2025-10-11_1.csv;type=text/csv"   http://192.168.0.6:8001/api/upload/rooms_status | jq .

# Execute
curl -s -H "X-Internal-Token: dev-admin-token"   -F business_date=2025-10-11   -F property_code=MOP   -F dry_run=0   -F "file=@backend/_uploads/rooms_status_MOP_2025-10-11_1.csv;type=text/csv"   http://192.168.0.6:8001/api/upload/rooms_status | jq .
```

> ❌ 잘못된 예시: `Content-Type: application/json` 으로 파일을 JSON 본문에 넣는 방식 — **불가** (반드시 multipart/form-data).

---

## 6) DB/마이그레이션 주의사항 (SQLite)

- **DROP/ALTER 최소화**: SQLite `batch_alter_table` 시 임시 테이블을 사용 → “NOT NULL” 추가 시 **DEFAULT** 또는 데이터 백필(UPDATE) 선행.
- **운영 전 백업 필수**:
  ```bash
  sqlite3 /path/hotel.db ".backup '/path/hotel_pre_fix_$(date +%F).db'"
  alembic upgrade head
  ```
- **롤백**:
  ```bash
  mv /path/hotel_pre_fix_*.db /path/hotel.db
  ```
- **FK 명 없는 drop_constraint 금지**: `drop_constraint(None, type_='foreignkey')`는 에러 → 반드시 주석 처리 또는 명시적 이름 사용.
- **현행 핵심 테이블**:
  - `merge_batches(id, dataset, property_code, business_date, file_name, record_count, dry_run, status, mode, missing_policy, source_kind, session_id, version_no, created_at, completed_at, notes)`
  - `merge_changelog(id, batch_id, dataset, property_code, business_date, key_hash, record_hash, action, payload, created_at)`
  - `rooms_status_canon(id, key_hash, record_hash, valid_on, payload_json, last_batch_id, updated_at)`
  - `rooms_status_history(id, key_hash, record_hash, valid_on, payload_json, source_batch_id, created_at)`

> Alembic 자동 생성 후, SQLite에 부적합한 DROP/ALTER/constraint 조작은 반드시 수동 편집으로 제거/치환.

---

## 7) Backend 엔드포인트·흐름 상호 참조

- `routers/upload.py` → `services/merge_service.py` → `merge_engine/engine.py`
  - 엔진: `normalize → parse → (dry_run? preview : repository.persist)`
  - repository: `MergeAuditRepository.create_batch → CanonRepository.upsert_record → finalize_batch`
- `routers/merge.py`
  - `GET /api/merge/batches` : 배치 목록, 필터/페이지네이션
  - `GET /api/merge/logs/{batch_id}` : 특정 배치의 변경 로그 상세
- 공통 로그 라인 (uvicorn.log):
  - 시작: `[MERGE_SERVICE] start dataset=... dry_run=... bytes=...`
  - 엔진 완료: `[MERGE_ENGINE] Applied dataset=..., rows=..., upserted=...`
  - 서비스 완료: `[MERGE_SERVICE] done ok=... dry_run=... rows=... batch_id=...`

---

## 8) QA 체크리스트

- [ ] `/api/upload/rooms_status` dry_run=1 호출 시 200 + preview 응답
- [ ] dry_run=0 호출 시 200 + `batch_id` + `result`(inserted/upserted/noop) 출력
- [ ] `rooms_status_canon`, `rooms_status_history`에 레코드 반영 확인
- [ ] `merge_batches.status = DONE` 및 `record_count`/`notes` 갱신 확인
- [ ] 동일 파일 재업로드 시 NOOP 집계 증가(또는 결과 불변) 확인
- [ ] 에러 케이스: 어댑터 normalize/parse 실패 시 `detail` 에러 반환 확인
- [ ] Alembic upgrade head 수행 시 무중단/무손실 보장 (사전 백업)

---

## 9) 배포/운영 정보

- 개발 서버 : `http://192.168.0.6:8001`
- 운영 서버 : `http://127.0.0.1:8000`
- 로그 : `/volume1/web/hotel-system/logs/uvicorn.log`
- 업로드 캐시/테스트: `/volume1/web/hotel-system/backend/_uploads/`

**파일 보관 규칙**

```
/volume1/web/hotel-system/backend/_uploads/
 ├─ rooms_status/MOP/2025-09-23/...
 ├─ sales_front/MOP/2025-09-23/...
 ├─ fac_sales/MOP/2025-09-23/...
 ├─ bank_ledger/MOP/2025-09-23/...
 └─ expenses/MOP/2025-09-23/...
```
- 파일명 패턴: `{dataset}_{property_code}_{YYYY-MM-DD}_{seq}.csv`

---

## 10) 변경 로그 템플릿 (본 문서용)

```md
## YYYY-MM-DD
- 변경자: @owner
- 변경 요약:
  - (예) merge_engine.repository 추가: Canon/History upsert + batch logging
  - (예) models.audit/canon ORM 반영
- QA 결과:
  - dry_run=1 / 0 각각 200 OK
  - Canon/History INSERT/UPSERT/NOOP 검증 완료
```

---

## 11) 부록 — 프런트 샘플 호출 (교정본)

```bash
# 드라이런
curl -s -H "X-Internal-Token: dev-admin-token"   -F business_date=2025-10-07   -F property_code=MOP   -F dry_run=1   -F "file=@backend/_uploads/rooms_status_MOP_2025-10-07_1.csv;type=text/csv"   http://192.168.0.6:8001/api/upload/rooms_status | jq .

# 실행
curl -s -H "X-Internal-Token: dev-admin-token"   -F business_date=2025-10-07   -F property_code=MOP   -F dry_run=0   -F "file=@backend/_uploads/rooms_status_MOP_2025-10-07_1.csv;type=text/csv"   http://192.168.0.6:8001/api/upload/rooms_status | jq .
```

```ts
// 프런트에서 변경 로그 조회 (예: 배치 완료 후)
async function loadMergeLogs(batchId: number) {
  const res = await fetch(`/api/merge/logs/${batchId}`, {
    headers: { "X-Internal-Token": "dev-admin-token" }
  });
  if (!res.ok) throw new Error("Failed to load logs");
  return res.json(); // { id, dataset, ..., changes: [...] }
}
```

---

## 12) Phase 2: SSOT 통합 확장 (전체 구현 체크리스트)

1) **DB Schema 확장**
   - `merge_batches`, `merge_changelog`를 Canon/History 관리에 맞게 확장.
   - 필요 시 Alembic:
     ```bash
     alembic revision --autogenerate -m "extend merge_* for SSOT"
     alembic upgrade head
     ```
2) **Model 확장 (Canonical 및 History)**
   - `app/models/canon.py` 내 컬럼/제약 최신화 → Alembic 반영.
3) **Diff/Policy 확장**
   - `app/merge_engine/diff.py`에서 INSERT/UPSERT/NOOP/DELETE 분류.
   - `missing_policy`/`dedupe_policy` 적용 (ignore/soft_delete/hard_delete, first/last/latest).
4) **서비스 계층 통합**
   - `run_merge_service()` Dry-run vs Execute 분기, 예외/로그 표준화.
5) **API 확장**
   - `/api/merge/batches` 필터/페이징/정렬, `/api/merge/logs/{batch_id}` 상세.
6) **프런트엔드 연계**
   - `POST /api/upload/{dataset}`로 multipart 업로드.
   - 배치 상태/로그 UI 제공(자동 새로고침 혹은 폴링).

---

## 13) 장애 대응 / 트러블슈팅 메모

- **`'session_id' is an invalid keyword argument for MergeBatch'`**
  - ORM/마이그레이션 싱크 확인. 컬럼 추가 후 `alembic upgrade head` 필수.
- **`'version_no' is an invalid keyword argument for MergeBatch'`**
  - 동일. 모델/스키마 동기화.
- **`NOT NULL constraint failed: merge_batches.business_date`**
  - `create_batch()` 호출 시 `business_date` 전달 누락. 폼/엔진 코드 확인.
- **`SQLite Date type only accepts Python date objects`**
  - `rooms_status_canon.valid_on`에 문자열 저장 시. 저장 전에 `date`로 변환.
- **BOM/개행 문제**
  - UTF-8 BOM 제거/CRLF 정규화 (`engine._decode_bytes` + adapter.normalize).
- **Idempotency**
  - 동일 파일 반복 업로드 시 `noop` 증가/변동 없음 확인. `merge_batches.notes` 요약 남김.

---

## 14) Dataset & CSV 스펙 (프런트 가이드 포함)

> **주의:** 아래 스펙은 현 시점 기준 운영 가능한 최소 컬럼 집합입니다. “⚙️ 예정” 어댑터는 추후 확정 시 본 문서 갱신.

### 14.1 `rooms_status` ✅
- **CSV 헤더(권장):** `business_date,property_code,room_no,status_code,is_dirty,hk_note`
- **키:** `(business_date, property_code, room_no)`
- **예시:**
  ```csv
  business_date,property_code,room_no,status_code,is_dirty,hk_note
  2025-10-11,MOP,101,OCC,0,
  2025-10-11,MOP,102,VAC,0,
  2025-10-11,MOP,103,DIRTY,0,
  ```

### 14.2 `sales_front` ⚙️
- **CSV 헤더(임시):** `business_date,property_code,tag,amount`
- **키:** `(business_date, property_code, tag)`
- **예시:**
  ```csv
  business_date,property_code,tag,amount
  2025-10-11,MOP,ROOM_ONLY,150000
  2025-10-11,MOP,BREAKFAST,50000
  2025-10-11,MOP,PACKAGE,200000
  ```

### 14.3 `fac_sales` ⚙️
- **CSV 헤더(임시):** `business_date,property_code,facility_code,tag,amount`
- **키:** `(business_date, property_code, facility_code, tag)`
- **예시:**
  ```csv
  business_date,property_code,facility_code,tag,amount
  2025-10-11,MOP,RESTAURANT,DINNER,350000
  2025-10-11,MOP,SPA,MASSAGE,180000
  ```

### 14.4 `expenses` ⚙️
- **CSV 헤더(임시):** `business_date,property_code,account_code,amount,note`
- **키:** `(business_date, property_code, account_code)`
- **예시:**
  ```csv
  business_date,property_code,account_code,amount,note
  2025-10-11,MOP,6001,80000,식자재 구입
  2025-10-11,MOP,6002,120000,세탁용품 구입
  ```

### 14.5 `bank_ledger` ⚙️
- **CSV 헤더(임시):** `business_date,property_code,bank_account,amount,memo`
- **키:** `(business_date, property_code, bank_account, memo)` *(tx id 도입 시 변경 가능)*
- **예시:**
  ```csv
  business_date,property_code,bank_account,amount,memo
  2025-10-11,MOP,KB-111-222-333,250000,입금
  2025-10-11,MOP,KB-111-222-333,-120000,출금
  ```

**프런트 공통 처리 팁**
- 파일 전송은 **반드시 multipart/form-data**.
- 헤더에 내부 토큰: `X-Internal-Token: dev-admin-token` (운영에서는 실제 토큰/세션으로 대체).
- 업로드 후 응답이 `dry_run=true`이면 미리보기(최대 3행) 기반으로 **확정/취소** UI 제공.
- `dry_run=0` 실행 후 `batch_id`가 반환되면 `/api/merge/logs/{batch_id}` 조회 버튼/링크 제공.
- (선택) 업로드 내역 로컬 캐시: 파일명 규칙으로 자동 그룹화/중복 업로드 방지 UI.

---

## 15) API 응답 스키마 & 예시

### 15.1 Dry-run 응답(예시)
```json
{
  "ok": true,
  "dry_run": true,
  "dataset": "rooms_status",
  "mode": "snapshot",
  "counts": {"rows": 3},
  "preview": [
    {
      "key_tuple": ["2025-10-11","MOP","101"],
      "key_hash": "<sha256>",
      "record_hash": "<sha256>",
      "payload": { "business_date": "2025-10-11", "property_code": "MOP", "room_no": "101", "status_code": "OCC", "is_dirty": "0", "hk_note": "" }
    }
  ]
}
```

### 15.2 Execute 응답(예시)
```json
{
  "ok": true,
  "dry_run": false,
  "dataset": "rooms_status",
  "mode": "snapshot",
  "batch_id": 7,
  "result": { "inserted": 0, "upserted": 0, "noop": 3 },
  "counts": { "rows": 3 }
}
```

### 15.3 변경 로그 조회 응답(예시)
```json
{
  "id": 7,
  "dataset": "rooms_status",
  "property_code": "MOP",
  "business_date": "2025-10-11",
  "record_count": 3,
  "status": "DONE",
  "notes": "inserted=0, upserted=0, noop=3",
  "created_at": "2025-10-11T03:53:31.870557",
  "completed_at": "2025-10-11T03:53:31.987498",
  "changes": [
    {
      "id": 10,
      "batch_id": 7,
      "dataset": "rooms_status",
      "property_code": "MOP",
      "business_date": "2025-10-11",
      "key_hash": "<sha256>",
      "record_hash": "<sha256>",
      "action": "NOOP",
      "payload": {"room_no":"101","status_code":"OCC", "...": "..."},
      "created_at": "2025-10-11T03:53:31.906448"
    }
  ]
}
```

---

## 16) 프런트 작업 가이드 (UX/에러/폴링)

- **Dataset 선택**: 드롭다운(rooms_status / sales_front / fac_sales / expenses / bank_ledger)
- **업로드 흐름**: 파일 선택 → `dry_run=1` 업로드 → 프리뷰 표시 → “실행(반영)” 버튼으로 동일 파일 `dry_run=0` 호출.
- **에러 처리**: 응답 `{ detail: "...error..." }` 메시지를 토스트/다이얼로그로 표준화.
- **폴링**: 실행 후 `batch_id` 확보 시 `/api/merge/logs/{id}` 3~5초 폴링 (상태 DONE/FAILED 감시).
- **i18n**: 스키마 키는 영문 고정, 라벨/메시지만 현지화.
- **접근 제어**: 관리자 전용 메뉴. 헤더 `X-Internal-Token` 또는 앱 로그인 세션 사용.
- **파일 크기 가이드**: CSV 10MB 내 권장(서버 제한 정책 수립 예정).
- **중복 업로드 방지**: 동일 파일명/해시 경고. 결과 `noop` 증가로 idempotent 보장.

---

## 17) 개발/운영 검증 커맨드 (개발 서버: 192.168.0.6:8001)

```bash
# 0) Alembic 상태
alembic heads

# 1) 구조 확인 (tree 미설치 환경)
find app/datasets -maxdepth 2 -type f | sort
find app/merge_engine -maxdepth 1 -type f | sort

# 2) rooms_status 업로드 (샘플 경로는 환경에 맞게 변경)
curl -s -H "X-Internal-Token: dev-admin-token"   -F business_date=2025-10-11 -F property_code=MOP -F dry_run=1   -F "file=@backend/_uploads/rooms_status_MOP_2025-10-11_1.csv;type=text/csv"   http://192.168.0.6:8001/api/upload/rooms_status | jq .

# 3) 배치 로그 확인 (예: 7번)
curl -s -H "X-Internal-Token: dev-admin-token"   http://192.168.0.6:8001/api/merge/logs/7 | jq .
```

---

## 18) 남은 작업 (프런트 연계 관점)

- [ ] `sales_front` / `fac_sales` / `expenses` / `bank_ledger` 어댑터 **정식 구현** (normalize/parse)
- [ ] 각 dataset별 CSV 컬럼/밸리데이션 **확정** 및 본 문서 갱신
- [ ] `/api/upload/{dataset}` → 업로드 UI 공통 컴포넌트화 (프리뷰 테이블/확정 다이얼로그)
- [ ] `/api/merge/batches` 목록/필터 UI + `/api/merge/logs/{id}` 상세 화면
- [ ] 에러/토스트/로딩 스피너 표준화
- [ ] 파일 중복/해시 체크(선택) 및 사용자 경고 UX
- [ ] 운영 토큰/세션 연동 방식 최종 확정
- [ ] 진행상태 텔리메트리(선택): 엔진/리포지토리 로그 이벤트를 FE에 노출

---

### 결론

본 문서는 **백엔드 구조의 SSOT** 입니다.  
개발/배포/QA 전 과정에서 본 문서와 실제 트리의 일치가 보장되도록 주기적으로 스냅샷과 diff를 수행하고, 변경이 생기면 **즉시 갱신**합니다.
