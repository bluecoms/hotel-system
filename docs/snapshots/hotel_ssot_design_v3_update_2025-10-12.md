# Hotel System 백엔드 폴더 구조 — SSOT (2025-10-12 업데이트판)

> **문서 목적 (SSOT)**  
> 본 문서는 백엔드 폴더 구조 및 업로드/병합 엔진의 **단일 진실 원본(Single Source of Truth)** 입니다.  
> 모든 설계·개발·리팩터링·QA는 이 문서 기준으로 작성·검증하며, 변경 발생 시 **즉시 갱신**합니다.

- **문서 버전:** `2025-10-12` (Phase 1 → Phase 2 확정, **Phase 3 연결/정책 통합 반영**)
- **적용 범위:** `backend/app` 하위 전체 (엔진/어댑터/모델/라우터/서비스/스키마/DB infra)
- **유지 책임:** **BE-Core** (Merge Engine/DB 변경 시 본 문서 갱신 주체)

---

## 🆕 Phase 3 변경점 / 업데이트 요약 (기존 내용 유지 + 추가 기록)

본 섹션은 **기존 SSOT(2025-10-11)** 을 **그대로 유지**하면서, 이번 작업에서 실제로 바뀐 점을 **추가**로 명시합니다.

### 1) 엔진 전역 정책 모듈 도입 및 앱 초기화 연동
- 신규 파일: `app/core/settings_merge.py`
  - 전역 DEFAULTS/데이터셋별 정책(`DATASET_POLICIES`) 정의
  - 파일/콘솔 **이중 로깅** 초기화 (`/volume1/web/hotel-system/logs/merge_engine.log`)
  - `show_policies()`로 로딩된 정책을 **INFO** 레벨 출력
- `app/main.py`에 **초기화 호출 추가**
  - ```python
    from app.core import settings_merge
    settings_merge.setup_merge_logger()
    settings_merge.show_policies()
    ```
  - 서버 부팅 시 정책 스냅샷이 로그로 남음 (문제 디버깅에 유용)

### 2) FNB 어댑터 반영 & Canon 스키마 통합
- **`app/datasets/adapters/fnb_items.py` 구현**
  - 키: `(business_date, property_code, item_code)`
  - 해시 비교 필드: `(category, qty, amount)`
  - **merge_mode = snapshot** 고정
  - CSV 정규화 시 폼 값으로 `business_date/property_code` 보강, amount 콤마 제거
- **Canon/History 테이블 표준화**
  - `fnb_items_canon` 스키마: `id, key_hash, record_hash, valid_on, payload_json, last_batch_id, updated_at`
  - **중요: 더 이상 raw CSV 파일 보관 X**. 모든 **실제 데이터는 DB의 `payload_json`로 보관**하며, **비교/변경 판단은 해시(key_hash/record_hash)** 기반.
  - 파일 시스템 저장이 없으므로, 업로드 경로에 파일이 남지 않아도 정상 동작임 (**설계 의도**).

### 3) Dry-Run 기본값/정책 확인
- `settings_merge.DEFAULTS["dry_run"]`는 **환경 변수**에 의해 덮어쓸 수 있습니다.
  - 예: `MERGE_DRY_RUN=0|1`(프로젝트 설정에 맞춰 주입)
  - 로그에서 `DEFAULTS: {'dry_run': False, ...}`가 보이는 경우, **실행 모드(커밋)** 기본값으로 동작함.
- 요청 폼의 `dry_run` 값이 **최우선**입니다. (`services/merge_service.py`에서 보정)

### 4) 업로드 → 머지 → 커밋 경로 확정
- 라우터: `routers/upload.py` → 서비스: `services/merge_service.py`
- 엔진: `merge_engine/engine.py` (normalize → parse → execute)
- 리포지토리: `merge_engine/repository.py`
  - `CanonRepository.upsert_record()`에서 **Upsert/Soft-Delete** 수행
  - `merge_batches / merge_changelog`에 **감사 로그** 기록 (`merge_engine/audit.py`)
  - `safe_commit()`으로 트랜잭션 보장

### 5) Alembic 설정 안정화
- `alembic/env.py`에 **SQLite 우회 옵션**(`render_as_batch=True`)과
  **DROP/ALTER 안전가드** 설정 유지
- DB URL은 `APP_DB_URL`(없으면 `sqlite:////volume1/web/hotel-system/backend/hotel.db`) 우선

### 6) 트러블슈팅 결과 반영
- 업로드 결과가 안 보였던 원인들
  1. (의도) 파일시스템 보관 미사용 → `_uploads` 폴더에 **파일이 남지 않음**  
  2. (정상) `fnb_items_canon`에 **payload_json로 저장**되므로, 레거시 칼럼 조회 시 컬럼 없음 에러가 발생  
     - 확인: `SELECT id, key_hash, substr(payload_json,1,80) FROM fnb_items_canon;`
  3. 엔진 초기화 로그 확인으로 정책 정상 반영 확인 (`merge_engine.log`)
- 실제 삽입 검증: `curl`로 업로드 후 `COUNT(*)` 또는 `payload_json` 프리뷰로 확인

---

## ✅ 1) Canonical Tree (Phase 2 최종 구조 — 원문 유지)

```
backend/app/
├─ core/
│  ├─ auth.py
│  ├─ locale.py
│  ├─ i18n.py
│  ├─ hashing.py
│  ├─ settings.py
│  ├─ settings_merge.py          # ✅ Phase 3: 엔진전역 병합정책/모드관리 (신규 반영)
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
│  │  ├─ sales_front.py          # ✅ SalesFrontAdapter (Phase 2 Final)
│  │  ├─ expenses.py             # ✅ ExpensesAdapter (Phase 2 Final)
│  │  ├─ bank_ledger.py          # ✅ BankLedgerAdapter (Phase 2 Final)
│  │  ├─ fnb_items.py            # ✅ FnbItemsAdapter (Phase 3 정상작동, 신규 반영)
│  │  ├─ fnb_tenders.py          # ✅ FnbTendersAdapter (Phase 3 정상작동)
│  │  └─ __init__.py             # ✅ ADAPTERS registry 자동 export
│  └─ schemas/
│     ├─ rooms_status.py         # ✅ RoomsStatusRow
│     ├─ sales_front.py          # ✅ SalesFrontRow
│     ├─ expenses.py             # ✅ ExpensesRow
│     ├─ bank_ledger.py          # ✅ BankLedgerRow
│     ├─ fnb_items.py            # ✅ FnbItemsRow
│     ├─ fnb_tenders.py          # ✅ FnbTendersRow
│     └─ __init__.py             # ✅ 통합 export
│
├─ merge_engine/
│  ├─ engine.py                  # ✅ normalize → parse → execute
│  ├─ repository.py              # ✅ Canon/History CRUD (rooms/fnb 통합)
│  ├─ policies.py                # ✅ 누락/중복 정책
│  ├─ planner.py                 # ✅ DryRun 계획
│  ├─ diff.py                    # ✅ 변경 비교
│  ├─ audit.py                   # ✅ 배치 로그 통합 관리
│  └─ __init__.py                # ✅ ADAPTERS 재-export
│
├─ services/
│  ├─ merge_service.py           # ✅ router → engine bridge
│  ├─ upload_service.py          # ✅ 업로드 분기 → merge_service
│  ├─ upload_apply.py            # ⚙️ 레거시 (폐기 예정)
│  └─ __init__.py
│
├─ routers/
│  ├─ upload.py                  # ✅ /api/upload/{dataset}
│  ├─ merge.py                   # ✅ /api/merge/batches 및 /logs
│  ├─ closing.py
│  ├─ reports.py
│  ├─ reports_sales.py
│  ├─ reports_bank.py
│  ├─ keywords.py
│  ├─ users.py
│  ├─ employees.py
│  ├─ ota.py
│  ├─ board.py
│  ├─ audit.py
│  ├─ debug.py
│  ├─ health.py
│  └─ __init__.py
│
├─ db/
│  ├─ base_class.py              # ✅ DeclarativeBase
│  ├─ base.py                    # ✅ metadata
│  ├─ session.py                 # ✅ get_db()
│  └─ __init__.py
│
├─ models/
│  ├─ base.py
│  ├─ mixins.py
│  ├─ audit.py                   # ✅ merge_batches, merge_changelog
│  ├─ canon.py                   # ✅ rooms_status + fnb_items + fnb_tenders Canon/History
│  ├─ closing.py
│  ├─ bank.py
│  ├─ ota.py
│  ├─ user.py
│  ├─ role.py
│  ├─ employee.py
│  └─ __init__.py
│
├─ schemas/
│  ├─ merge.py                   # ✅ MergeBatch, ChangeLog 스키마
│  ├─ closing.py
│  ├─ board.py
│  ├─ reports.py
│  ├─ users.py
│  ├─ employees.py
│  ├─ ota.py
│  ├─ auth.py
│  └─ __init__.py
│
├─ main.py                       # ✅ FastAPI App Entry
└─ __init__.py
```

---

## 2) 상태 요약 (Phase 2 반영 — 원문 유지)

| 모듈/경로                         | 상태 | 설명 |
|----------------------------------|------|------|
| `datasets.adapters.sales_front`  | ✅   | 스냅샷형 업로드 (`tag`-별 금액) |
| `datasets.adapters.expenses`     | ✅   | 스냅샷형 업로드 (`account_code`-별 금액/메모) |
| `datasets.adapters.bank_ledger`  | ✅   | append 기본, `txn_id` 기준(미제공시 라인키 생성) |
| `datasets.schemas.*`             | ✅   | `sales_front/expenses/bank_ledger` 완료 |
| `merge_engine.__init__`          | ✅   | adapters 레지스트리 재-export(ADAPTERS/get_adapter) |
| `routers.merge.get_merge_logs`   | ✅   | Pydantic v2 호환 문자열 ISO8601로 반환 |

> **주의:** `pay_settlement` → **`bank_ledger`** 로 명칭 통합(레거시 alias 유지).

---

## 3) 변경 관리 원칙（원문 유지）

- **문서 위치(SSOT)**: `docs/runbooks/structure_backend_YYYY-MM-DD.md`  
  - 본 문서는 덮어쓰지 않고 **날짜 버전으로 누적**합니다.  
  - 최신판을 프로젝트 README/CONTRIBUTING에 링크합니다.
- **갱신 트리거**
  1. Alembic 마이그레이션 추가/변경 (테이블/인덱스/제약 포함)
  2. 새 모듈/파일 생성 (예: fnb_* 어댑터)
  3. 라우터/서비스 추가 또는 **API 계약 변경**
  4. Phase 전환 (1 → 2 등)
- **코드 주석 버전 헤더:**
  ```python
  # version: 2025-10-11 Phase 2
  ```
- **폴더 계층 변경 금지**
  - 기존 계층 하위에만 파일 추가
  - 계층 이동/이름 변경은 RFC(승인 문서)로 별도 합의

---

## 4) 운영 점검/스냅샷 절차（원문 유지）

```bash
# 1) 구조 스냅샷 저장
cd /volume1/web/hotel-system/backend/app
tree -L 3 > ../../../docs/runbooks/snapshots/backend_tree_$(date +%F).txt

# 2) 최신 SSOT 문서와 차이 비교
diff -u   docs/runbooks/structure_backend_2025-10-11.md   docs/runbooks/snapshots/backend_tree_$(date +%F).txt | less
```

---

## 5) 프런트 연동 규격 (데이터셋별 — 원문 + 설명 확장)

### 공통 업로드 엔드포인트
`POST /api/upload/{dataset}` (multipart/form-data)

**폼 필드**

| 필드 | 타입 | 설명 | 필수 | 기본 |
|---|---|---|---|---|
| `business_date` | string | YYYY-MM-DD | ✅ | - |
| `property_code` | string | 호텔 코드 (예: MOP) | ↔️ | `MOP` |
| `dry_run` | 0/1 | 1=미리보기, 0=실반영 | ↔️ | `settings_merge.DEFAULTS.dry_run` |
| `source_kind` | enum | daily/weekly/monthly | ↔️ | `daily` |
| `mode` | enum | (선택) append/snapshot 강제 | ❌ | - |
| `file` | file | CSV 업로드 | ✅ | - |

**중요: 저장 방식 안내 (프런트 설명 필수)**  
- 업로드된 파일은 **서버 파일시스템에 보관하지 않습니다.**  
- **정규화된 로우**가 `payload_json`(Canon)으로 DB에 저장되며,  
  **동일 키**의 변경 여부는 `record_hash` 비교로 판단합니다.  
- 따라서 프런트에서는 업로드 후 **batch 결과/요약/변경내역**을 기준으로 UX를 구성하고,  
  **원본 파일 다운로드 링크는 제공하지 않습니다.** (기획 의도)

**응답 스키마**
- Dry-run: `MergeDryRunResp { ok, dataset, property_code, business_date, summary{inserted,updated,deleted,noop}, details{...}, missing_result{} }`
- Execute:  `MergeExecResp   { ok, batch_id, dataset, property_code, business_date, summary{...}, completed_at, notes }`

> 모든 날짜/시간은 **ISO-8601 문자열**

---

### Dataset: `rooms_status` (Append 기본 — 원문 유지)

- 키: `(business_date, property_code, room_no)`  
- 필드: `room_no, status_code, is_dirty, hk_note`  
- 모드: `split_by_date=1`일 때만 snapshot, 기본은 append

CSV 예시
```csv
business_date,property_code,room_no,status_code,is_dirty,hk_note
2025-10-11,MOP,101,OC,1,VIP
2025-10-11,MOP,102,VC,0,
```

샘플 호출
```bash
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-10-11 -F property_code=MOP -F dry_run=1 \
  -F "file=@backend/_uploads/rooms_status_MOP_2025-10-11.csv;type=text/csv" \
  http://192.168.0.6:8001/api/upload/rooms_status | jq .
```

---

### Dataset: `sales_front` (Snapshot — 원문 유지)

- 키: `(business_date, property_code, tag)`  
- 필드: `tag, amount` (amount 숫자 문자열 허용)

CSV 예시
```csv
business_date,property_code,tag,amount
2025-10-11,MOP,ROOM_ONLY,150000
2025-10-11,MOP,BREAKFAST,50000
2025-10-11,MOP,PACKAGE,200000
```

샘플 호출
```bash
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-10-11 -F property_code=MOP -F dry_run=1 \
  -F "file=@backend/_uploads/sales_front_MOP_2025-10-11.csv;type=text/csv" \
  http://192.168.0.6:8001/api/upload/sales_front | jq .
```

---

### Dataset: `expenses` (Snapshot — 원문 유지)

- 키: `(business_date, property_code, account_code)`  
- 필드: `account_code, amount, note`

CSV 예시
```csv
business_date,property_code,account_code,amount,note
2025-10-11,MOP,6001,80000,식자재 구입
2025-10-11,MOP,6002,120000,세탁용품 구입
2025-10-11,MOP,6003,40000,소모품 구입
```

샘플 호출
```bash
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-10-11 -F property_code=MOP -F dry_run=1 \
  -F "file=@backend/_uploads/expenses_MOP_2025-10-11.csv;type=text/csv" \
  http://192.168.0.6:8001/api/upload/expenses | jq .
```

---

### Dataset: `bank_ledger` (Append 기본 — 원문 유지)

- 키: `(business_date, property_code, txn_id)` (`txn_id` 없으면 라인키 생성)
- 필드: `account_no, direction(in/out), amount, memo)`

CSV 예시
```csv
business_date,property_code,txn_id,account_no,direction,amount,memo
2025-10-11,MOP,TXN-0001,110-2222-3333,in,450000,POS 입금
2025-10-11,MOP,,110-2222-3333,out,120000,공과금
```

샘플 호출
```bash
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-10-11 -F property_code=MOP -F dry_run=1 \
  -F "file=@backend/_uploads/bank_ledger_MOP_2025-10-11.csv;type=text/csv" \
  http://192.168.0.6:8001/api/upload/bank_ledger | jq .
```

---

### Dataset: `fnb_items` (Snapshot — **신규/확정**)

- 키: `(business_date, property_code, item_code)`  
- 값 필드: `category, qty, amount` (amount 콤마 제거, qty 문자열 허용)  
- 모드: 기본 `snapshot`  
- 저장: Canon 테이블 `payload_json`(전문) + `key_hash/record_hash`

CSV 예시
```csv
business_date,property_code,item_code,category,qty,amount
2025-09-23,MOP,LOUNGE,식음료,1,395000
```

샘플 호출
```bash
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F property_code=MOP \
  -F business_date=2025-10-12 \
  -F dry_run=0 \
  -F "file=@backend/_uploads/fnb_items_test.csv;type=text/csv" \
  http://192.168.0.6:8001/api/upload/fnb_items | jq .
```

DB 확인
```sql
-- Canon 스키마 확인
.schema fnb_items_canon

-- 데이터 프리뷰 (payload_json 전문은 길 수 있어 앞부분만 확인)
SELECT id, key_hash, substr(payload_json,1,120) FROM fnb_items_canon ORDER BY id DESC LIMIT 5;
```

---

## 6) Merge 엔진 동작 규약 (요약 — 원문 유지 + 해시 설명 보강)

| 항목 | rooms_status | sales_front | expenses | bank_ledger | fnb_items |
|---|---|---|---|---|---|
| 기본 모드 | append | snapshot | snapshot | append | snapshot |
| 키 필드 | date, prop, room_no | date, prop, tag | date, prop, account_code | date, prop, txn_id* | date, prop, item_code |
| 변경 판단 | `hash(payload)` | `amount` | `amount+note` | `account_no+direction+amount+memo` | `category+qty+amount` |
| 누락 정책 | soft_delete | soft_delete | soft_delete | ignore | soft_delete |

**해시/저장 정책**  
- Canon은 **payload_json**으로 최신 스냅샷 보관  
- `key_hash`: 키 필드 기반 해시 (유니크)  
- `record_hash`: 비교 필드 기반 해시 → 값이 바뀌면 **update**로 처리  
- **파일은 저장하지 않음** (설계 의도)

---

## 7) Backend 엔드포인트·흐름（원문 유지 + 연결도 명시）

- `routers/upload.py` → `services/merge_service.py` → `merge_engine/engine.py`  
  - 엔진: `normalize → parse → (dry_run? preview : repository.persist)`  
  - 리포지토리:  
    - `MergeAuditRepository.create_batch()`  
    - `CanonRepository.upsert_record()` (**key_hash/record_hash 비교, snapshot/append 정책 반영**)  
    - `finalize_batch()` (**merge_batches/merge_changelog** 기록)
- `routers/merge.py`  
  - `GET /api/merge/batches` : 배치 목록 (필터/정렬/페이징)  
  - `GET /api/merge/logs/{batch_id}` : 특정 배치의 변경 로그 상세

응답 예 (/api/merge/logs/7)
```json
{
  "id": 7,
  "dataset": "rooms_status",
  "property_code": "MOP",
  "business_date": "2025-10-11",
  "record_count": 3,
  "status": "DONE",
  "created_at": "2025-10-11T03:53:31.870557",
  "completed_at": "2025-10-11T03:53:31.987498",
  "changes": [
    { "id": 10, "action": "noop", "key_hash": "...", "created_at": "2025-10-11T03:53:31.906448" }
  ]
}
```

---

## 8) QA 체크리스트（원문 유지）

- [ ] `/api/upload/*` 각 데이터셋 dry_run=1 → 200 + summary OK  
- [ ] dry_run=0 → 200 + `batch_id` + summary OK  
- [ ] `merge_batches.status= DONE`, `record_count` 반영  
- [ ] `/api/merge/logs/{batch_id}` → 변경내역 정상 반환(ISO 문자열)  
- [ ] 동일 파일 재업로드 → `noop` 증가 또는 불변  
- [ ] CSV 헤더 일부 미제공 시 폼 값으로 보강되는지 확인  
- [ ] 금액 필드 콤마 제거/공백 처리 확인  
- [ ] 오류 행 메시지 `Invalid row: ...` 가독성 확인

---

## 9) 배포/운영 정보（원문 유지）

- 개발 서버 : `http://192.168.0.6:8001`  
- 운영 서버 : `http://127.0.0.1:8000`  
- 로그 : `/volume1/web/hotel-system/logs/uvicorn.log`  
- 업로드 캐시/테스트: `/volume1/web/hotel-system/backend/_uploads/`

**파일 보관 규칙 (참고용 안내만 유지)**  
> 현재 설계에서는 **파일을 영구 보관하지 않음**.  
> 아래 경로는 **테스트/수동 업로드용** 디렉터리 구조 예시입니다.

```
/volume1/web/hotel-system/backend/_uploads/
 ├─ rooms_status/MOP/2025-10-11/...
 ├─ sales_front/MOP/2025-10-11/...
 ├─ bank_ledger/MOP/2025-10-11/...
 └─ expenses/MOP/2025-10-11/...
```
- 파일명 패턴: `{dataset}_{property_code}_{YYYY-MM-DD}_{seq}.csv`

---

## 10) 프런트 개발 유의사항 (상세 — 원문 유지 + UX 가이드 확장)

1) **multipart만 허용**: `Content-Type: multipart/form-data` (브라우저 자동)  
2) **인증 헤더**: 개발 환경 `X-Internal-Token: dev-admin-token`  
3) **에러 처리**: `!res.ok` → `res.json().detail` 우선 노출  
4) **재업로드 UX**: 동일 키는 idempotent. 실행 후 합계/차이 재표시  
5) **시간 포맷**: ISO-8601 문자열 → `new Date()` 파싱 가능  
6) **인코딩**: UTF-8 권장, BOM 허용(엔진 제거), CR/LF 혼용 허용  
7) **금액 필드**: 콤마 허용, 엔진에서 제거 후 숫자 비교  
8) **bank_ledger 주의**: `txn_id` 없으면 라인키 생성 → 중복 업로드 주의  
9) **레거시 라우팅**: `pay_settlement` → `bank_ledger` 처리  
10) **로그 뷰**: 실행 후 `batch_id`로 `/api/merge/logs/{id}` 이동/폴링  
11) **파일 미보관 설계에 따른 UX**:  
    - 결과 패널에는 **요약(삽입/갱신/삭제/무변경)**, **합계**, **배치 ID** 표시  
    - 필요 시 **payload 요약(표)** 지원, 원본 파일 다운로드 버튼은 **표시하지 않음**

**프런트 Fetch 스니펫** (원문 유지)
```ts
async function upload(dataset: string, file: File, opts: {
  business_date: string;
  property_code?: string;
  dry_run?: 0 | 1;
  mode?: 'append' | 'snapshot';
  source_kind?: 'daily' | 'weekly' | 'monthly';
}) {
  const form = new FormData();
  form.append("business_date", opts.business_date);
  form.append("property_code", opts.property_code ?? "MOP");
  form.append("dry_run", String(opts.dry_run ?? 1));
  if (opts.mode) form.append("mode", opts.mode);
  form.append("source_kind", opts.source_kind ?? "daily");
  form.append("file", file, file.name);

  const res = await fetch(`/api/upload/${dataset}`, {
    method: "POST",
    headers: { "X-Internal-Token": "dev-admin-token" },
    body: form,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Upload failed");
  return data;
}
```

**서버 REPL 확인** (원문 유지)
```python
from app.merge_engine import ADAPTERS, get_adapter
print("datasets:", sorted(ADAPTERS.keys()))
print("sales_front adapter:", type(get_adapter("sales_front")).__name__)
print("expenses adapter:", type(get_adapter("expenses")).__name__)
print("bank_ledger adapter:", type(get_adapter("bank_ledger")).__name__)
```

---

## 11) Phase 2 확장 체크리스트（원문 유지 + 현황 반영）

- [x] **FNB 어댑터(fnb_items, fnb_tenders) 설계/구현** → **반영됨**  
- [ ] rooms_status의 Canon/History 확장 검토(필요시)  
- [x] merge_engine.audit 구현 및 대시보드 노출(백엔드 로그 기준)  
- [ ] `/api/merge/batches` 프런트 목록/필터 UI  
- [ ] 업로드 히스토리/재업로드 UX 개선(파일명/사이즈 노출 대신 **요약/배치 기반 뷰**)  

---

## 12) 장애 대응 / 트러블슈팅（원문 유지 + 실사례 추가）

- **`ResponseValidationError: created_at should be string`**  
  → 라우터에서 ISO 문자열로 변환하여 반환(수정됨).

- **`NOT NULL constraint failed: merge_batches.business_date`**  
  → 폼에서 business_date 누락. 업로드 폼 검증 추가.

- **`SQLite Date type only accepts Python date objects`**  
  → 저장 전 필드 변환 필요. (엔진/리포지토리에서 처리)

- **BOM/개행 문제**  
  → 엔진 정규화 처리. CSV는 UTF-8 권장.

- **중복 txn (`bank_ledger`)**  
  → `txn_id` 제공 권장. 미제공 시 라인키로 병합되어 재업로드 중복 가능.

- **파일이 서버에 안 남는다? (이번 이슈)**  
  → **정상**. 설계상 파일 보관하지 않으며, DB Canon에 `payload_json`으로 저장됨.  
  → 확인 쿼리:
  ```sql
  SELECT id, key_hash, substr(payload_json,1,120)
  FROM fnb_items_canon
  ORDER BY id DESC LIMIT 5;
  ```

---

## 13) 부록: 샘플 데이터/검증 커맨드

```bash
# 샘플 CSV
cat > backend/_uploads/fnb_items_test.csv <<'CSV'
business_date,property_code,item_code,category,qty,amount
2025-09-23,MOP,LOUNGE,식음료,1,395000
CSV

# 업로드 (execute)
TOKEN=dev-admin-token
curl -s -H "X-Internal-Token: $TOKEN" \
  -F property_code=MOP \
  -F business_date=2025-10-12 \
  -F dry_run=0 \
  -F "file=@backend/_uploads/fnb_items_test.csv;type=text/csv" \
  http://192.168.0.6:8001/api/upload/fnb_items | jq .

# DB 확인
sqlite3 /volume1/web/hotel-system/backend/hotel.db "\
  SELECT COUNT(*) FROM fnb_items_canon; \
  SELECT id, key_hash, substr(payload_json,1,120) FROM fnb_items_canon ORDER BY id DESC LIMIT 5; \
"
```

---

### 결론

- 본 문서는 **기존 SSOT 원문을 유지**하면서, **Phase 3 연결/정책/어댑터 반영**을 **추가 기록**했습니다.  
- 프런트는 **파일 미보관 설계**를 전제로, **배치 결과/변경 요약** 중심의 UX를 구성해 주세요.  
- 변경 발생 시 이 문서를 **즉시 갱신**합니다.