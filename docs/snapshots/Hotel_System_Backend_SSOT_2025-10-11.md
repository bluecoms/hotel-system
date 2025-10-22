# Hotel System 백엔드 폴더 구조 (2025-10-11 기준 최신 SSOT 반영판)

> **문서 목적 (SSOT)**
>
> 이 문서는 백엔드 폴더 구조의 **단일 진실 원본(Single Source of Truth)** 입니다.
> 모든 설계/개발/리팩터링/QA 문서는 본 구조를 기준으로 작성·검증합니다.
> “⚙️ 예정” 항목이 구현되면 반드시 본 문서를 **즉시 갱신**합니다.

* 문서 버전: `2025-10-11` (Phase 1 finalized → Phase 2 확장 반영)
* 적용 범위: backend/app 하위 전체 (엔진/어댑터/모델/라우터/서비스/스키마/DB infra)
* 유지 책임: **BE-Core** (SSOT Merge Engine/DB 변경 시 갱신 주체)

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
│  │  ├─ sales_front.py          # ✅ SalesFrontAdapter
│  │  ├─ expenses.py             # ✅ ExpensesAdapter
│  │  ├─ bank_ledger.py          # ✅ BankLedgerAdapter
│  │  ├─ fnb_tenders.py          # ✅ 
│  │  ├─ fnb_items.py            # ✅ 
│  │  └─ __init__.py             # ✅ 자동 export + ADAPTERS registry
│  └─ schemas/
│     ├─ rooms_status.py         # ✅ 
│     ├─ sales_front.py          # ✅ SalesFrontRow
│     ├─ expenses.py             # ✅ ExpensesRow
│     ├─ bank_ledger.py          # ✅ BankLedgerRow
│     ├─ fnb_tenders.py          # ✅ 
│     ├─ fnb_items.py            # ✅ 
│     └─ __init__.py             # ✅ 통합 export
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
│  ├─ policies.py                # ✅ 중복/누락 정책 (Phase 2)
│  ├─ planner.py                 # ✅ 드라이런 계획 (Phase 2)
│  ├─ diff.py                    # ✅ Canon 대비 변경 계산 (Phase 2)
│  ├─ audit.py                   # ✅ 
│  └─ __init__.py                # ✅ 자동 export + adapters 재-export
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

## 2) 상태 요약 (Phase 2 반영)

| 모듈/경로                         | 상태 | 설명 |
|----------------------------------|------|------|
| `datasets.adapters.sales_front`  | ✅   | 스냅샷형 업로드 (`tag`-별 금액) |
| `datasets.adapters.expenses`     | ✅   | 스냅샷형 업로드 (`account_code`-별 금액/메모) |
| `datasets.adapters.bank_ledger`  | ✅   | append 기본, `txn_id` 기준(미제공시 라인키 생성) |
| `datasets.schemas.*`             | ✅   | `sales_front/expenses/bank_ledger` 완료,  |
| `merge_engine.__init__`          | ✅   | adapters 레지스트리 재-export(ADAPTERS/get_adapter) |
| `routers.merge.get_merge_logs`   | ✅   | Pydantic v2 호환 문자열 ISO8601로 반환 |

> **주의:** `pay_settlement` → **`bank_ledger`** 로 명칭 통합(레거시 alias 유지).

---

## 3) 변경 관리 원칙

* **문서 위치(SSOT)**: `docs/runbooks/structure_backend_YYYY-MM-DD.md`
  * 본 문서는 덮어쓰지 않고 **날짜 버전으로 누적**합니다.
  * 최신판을 프로젝트 README/CONTRIBUTING에 링크합니다.
* **갱신 트리거**
  1. Alembic 마이그레이션 추가/변경 (테이블/인덱스/제약 포함)
  2. 새 모듈/파일 생성 (예: fnb_* 어댑터)
  3. 라우터/서비스 추가 또는 **API 계약 변경**
  4. Phase 전환 (1 → 2 등)
* **코드 주석 버전 헤더**:
  ```python
  # version: 2025-10-11 Phase 2
  ```
* **폴더 계층 변경 금지**
  * 기존 계층 하위에만 파일 추가
  * 계층 이동/이름 변경은 RFC(승인 문서)로 별도 합의

---

## 4) 운영 점검/스냅샷 절차

```bash
# 1) 구조 스냅샷 저장
cd /volume1/web/hotel-system/backend/app
tree -L 3 > ../../../docs/runbooks/snapshots/backend_tree_$(date +%F).txt

# 2) 최신 SSOT 문서와 차이 비교
diff -u   docs/runbooks/structure_backend_2025-10-11.md   docs/runbooks/snapshots/backend_tree_$(date +%F).txt | less
```

---

## 5) 프런트 연동 규격 (데이터셋별)

### 공통 업로드 엔드포인트
`POST /api/upload/{dataset}` (multipart/form-data)

**폼 필드**

| 필드 | 타입 | 설명 | 필수 | 기본 |
|---|---|---|---|---|
| `business_date` | string | YYYY-MM-DD | ✅ | - |
| `property_code` | string | 호텔 코드 (예: MOP) | ↔️ | `MOP` |
| `dry_run` | 0/1 | 1=미리보기, 0=실반영 | ↔️ | `1` |
| `source_kind` | enum | daily/weekly/monthly | ↔️ | `daily` |
| `mode` | enum | (선택) append/snapshot 강제 | ❌ | - |
| `file` | file | CSV 업로드 | ✅ | - |

**응답 스키마**
- Dry-run: `MergeDryRunResp { ok, dataset, property_code, business_date, summary{inserted,updated,deleted,noop}, details{...}, missing_result{} }`
- Execute:  `MergeExecResp   { ok, batch_id, dataset, property_code, business_date, summary{...}, completed_at, notes }`

> 날짜/시간은 **ISO-8601 문자열**로 반환.

---

### Dataset: `rooms_status` (Append 기본)
- **키**: `(business_date, property_code, room_no)`  
- **필드**: `room_no, status_code, is_dirty, hk_note`  
- **모드**: form.mode가 없으면 `split_by_date=1`일 때만 snapshot, 기본은 append  
- **CSV 예시**
```csv
business_date,property_code,room_no,status_code,is_dirty,hk_note
2025-10-11,MOP,101,OC,1,VIP
2025-10-11,MOP,102,VC,0,
```
- **샘플 호출**
```bash
curl -s -H "X-Internal-Token: dev-admin-token"   -F business_date=2025-10-11 -F property_code=MOP -F dry_run=1   -F "file=@backend/_uploads/rooms_status_MOP_2025-10-11.csv;type=text/csv"   http://192.168.0.6:8001/api/upload/rooms_status | jq .
```

---

### Dataset: `sales_front` (Snapshot)
- **키**: `(business_date, property_code, tag)`  
- **필드**: `tag, amount` (amount는 숫자 문자열 허용)  
- **모드**: 기본 `snapshot`  
- **CSV 예시**
```csv
business_date,property_code,tag,amount
2025-10-11,MOP,ROOM_ONLY,150000
2025-10-11,MOP,BREAKFAST,50000
2025-10-11,MOP,PACKAGE,200000
```
- **샘플 호출**
```bash
curl -s -H "X-Internal-Token: dev-admin-token"   -F business_date=2025-10-11 -F property_code=MOP -F dry_run=1   -F "file=@backend/_uploads/sales_front_MOP_2025-10-11.csv;type=text/csv"   http://192.168.0.6:8001/api/upload/sales_front | jq .
```

---

### Dataset: `expenses` (Snapshot)
- **키**: `(business_date, property_code, account_code)`  
- **필드**: `account_code, amount, note`  
- **모드**: 기본 `snapshot`  
- **CSV 예시**
```csv
business_date,property_code,account_code,amount,note
2025-10-11,MOP,6001,80000,식자재 구입
2025-10-11,MOP,6002,120000,세탁용품 구입
2025-10-11,MOP,6003,40000,소모품 구입
```
- **샘플 호출**
```bash
curl -s -H "X-Internal-Token: dev-admin-token"   -F business_date=2025-10-11 -F property_code=MOP -F dry_run=1   -F "file=@backend/_uploads/expenses_MOP_2025-10-11.csv;type=text/csv"   http://192.168.0.6:8001/api/upload/expenses | jq .
```

---

### Dataset: `bank_ledger` (Append 기본)
- **키**: `(business_date, property_code, txn_id)` `txn_id` 미존재 시 라인키 생성  
- **필드**: `account_no, direction(in/out), amount, memo`  
- **모드**: 기본 `append` (`mode=snapshot`로 강제 가능)  
- **CSV 예시**
```csv
business_date,property_code,txn_id,account_no,direction,amount,memo
2025-10-11,MOP,TXN-0001,110-2222-3333,in,450000,POS 입금
2025-10-11,MOP,,110-2222-3333,out,120000,공과금
```
- **샘플 호출**
```bash
curl -s -H "X-Internal-Token: dev-admin-token"   -F business_date=2025-10-11 -F property_code=MOP -F dry_run=1   -F "file=@backend/_uploads/bank_ledger_MOP_2025-10-11.csv;type=text/csv"   http://192.168.0.6:8001/api/upload/bank_ledger | jq .
```

---

### 업로드 성공/실패 UX (프런트 권장)
- 성공(dry_run): 합계/건수, 변경내역 요약(삽입/갱신/삭제/무변경) 표시 → “실행” 버튼 노출
- 성공(execute): `batch_id` 하이퍼링크 → `/api/merge/logs/{batch_id}` 디테일 패널로 연결
- 실패: 백엔드 `detail` 메시지 그대로 표출 + “다운로드 로그” 제공(필요시)

---

## 6) Merge 엔진 동작 규약 (요약)

| 항목 | rooms_status | sales_front | expenses | bank_ledger |
|---|---|---|---|---|
| 기본 모드 | append | snapshot | snapshot | append |
| 키 필드 | date, prop, room_no | date, prop, tag | date, prop, account_code | date, prop, txn_id* |
| 변경 판단 | `hash(payload)` | `amount` | `amount+note` | `account_no+direction+amount+memo` |
| 누락 정책 | soft_delete | soft_delete | soft_delete | ignore |
| 비고 | split_by_date=1 시 snapshot |  |  | txn_id 없으면 라인키 |

*모든 어댑터는 CSV 헤더가 일부 없어도 **폼 값으로 보강**(business_date/property_code). 금액은 콤마 제거 후 숫자 문자열 처리.*

---

## 7) Backend 엔드포인트·흐름

* `routers/upload.py` → `services/merge_service.py` → `merge_engine/engine.py`
  * 엔진: `normalize → parse → (dry_run? preview : repository.persist)`
  * repository: `MergeAuditRepository.create_batch → CanonRepository.upsert_record → finalize_batch`
* `routers/merge.py`
  * `GET /api/merge/batches` : 배치 목록 (필터/정렬/페이징)
  * `GET /api/merge/logs/{batch_id}` : 특정 배치의 변경 로그 상세

**응답 예시 (/api/merge/logs/7)**

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

## 8) QA 체크리스트 (확장)

* [ ] `/api/upload/*` 각 데이터셋 dry_run=1 → 200 + summary OK
* [ ] dry_run=0 → 200 + `batch_id` + summary OK
* [ ] `merge_batches.status= DONE`, `record_count` 반영
* [ ] `/api/merge/logs/{batch_id}` → 변경내역 정상 반환(ISO 시간 문자열)
* [ ] 동일 파일 재업로드 → `noop` 증가 또는 불변
* [ ] CSV 헤더 일부 미제공 시 폼 값으로 보강되는지 확인
* [ ] 금액 필드 콤마 제거/공백 처리 확인
* [ ] 오류 행 메시지 `Invalid row: ...` 가독성 확인

---

## 9) 배포/운영 정보

* 개발 서버 : `http://192.168.0.6:8001`
* 운영 서버 : `http://127.0.0.1:8000`
* 로그 : `/volume1/web/hotel-system/logs/uvicorn.log`
* 업로드 캐시/테스트: `/volume1/web/hotel-system/backend/_uploads/`

**파일 보관 규칙**

```
/_volume1/web/hotel-system/backend/_uploads/
 ├─ rooms_status/MOP/2025-10-11/...
 ├─ sales_front/MOP/2025-10-11/...
 ├─ bank_ledger/MOP/2025-10-11/...
 └─ expenses/MOP/2025-10-11/...
```
* 파일명 패턴: `{dataset}_{property_code}_{YYYY-MM-DD}_{seq}.csv`

---

## 10) 프런트 개발 유의사항 (상세)

1) **multipart만 허용**: `Content-Type: multipart/form-data` (브라우저는 자동 설정).  
2) **토큰 헤더**: 개발 `X-Internal-Token: dev-admin-token` (운영은 실제 토큰/세션).  
3) **에러 처리**: `!res.ok` 시 `res.json().detail` 우선 노출.  
4) **재업로드 UX**: 같은 일자/호텔/키 조합은 idempotent. 실행 후 합계/차이 재표시.  
5) **시간 포맷**: ISO-8601 문자열(프런트에서 `new Date()` 파싱 가능).  
6) **파일 인코딩**: UTF-8 권장, BOM 허용하나 제거됨. CR/LF 혼용도 흡수.  
7) **금액 필드**: 쉼표 포함 허용, 내부에서 제거 후 병합.  
8) **`bank_ledger` 전용**: `txn_id`가 없으면 라인키 생성되므로 중복 업로드에 주의(가능하면 txn_id 제공).  
9) **레거시 호환**: `pay_settlement`로 호출해도 `bank_ledger`로 라우팅됨(서버 어댑터 alias).  
10) **로그 뷰**: 실행 후 받은 `batch_id`로 `/api/merge/logs/{id}`를 폴링하거나 클릭 이동.  

---

## 11) 샘플 코드 스니펫

**프런트 (Fetch)**
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

**서버 확인 (Python REPL)**
```python
from app.merge_engine import ADAPTERS, get_adapter
print("datasets:", sorted(ADAPTERS.keys()))
print("sales_front adapter:", type(get_adapter("sales_front")).__name__)
print("expenses adapter:", type(get_adapter("expenses")).__name__)
print("bank_ledger adapter:", type(get_adapter("bank_ledger")).__name__)
```

---

## 12) Phase 2 확장 체크리스트

- [ ] FNB 어댑터(fnb_tenders, fnb_items) 설계/구현
- [ ] rooms_status의 Canon/History 확장 검토(필요시)
- [ ] merge_engine.audit 구현 및 대시보드 노출
- [ ] `/api/merge/batches` 프런트 목록/필터 UI
- [ ] 업로드 히스토리/재업로드 UX 개선(파일명/사이즈 노출)

---

## 13) 장애 대응 / 트러블슈팅

* **`ResponseValidationError: created_at should be string`**  
  → 라우터에서 ISO 문자열로 변환하여 반환(수정됨).
* **`NOT NULL constraint failed: merge_batches.business_date`**  
  → 폼에서 business_date 누락. 업로드 폼 검증 추가.
* **`SQLite Date type only accepts Python date objects`**  
  → 저장 전 필드 변환 필요. (엔진/리포지토리에서 처리)
* **BOM/개행 문제**  
  → 엔진이 정규화 처리. CSV는 UTF-8 권장.
* **중복 txn** (`bank_ledger`)  
  → txn_id 제공 권장. 미제공 시 라인키로 병합되어 재업로드 중복 가능.

---

### 결론

본 문서는 **백엔드 구조의 SSOT** 입니다.  
프런트/백엔드/운영 전 과정에서 본 문서를 기준으로 개발·배포·QA를 수행하고, 변경 발생 시 **즉시 갱신**합니다.
