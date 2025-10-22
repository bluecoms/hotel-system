# SSOT 통합 머지엔진 설계서 (Rooms/Sales/FNB/Expenses/Bank 공통) — 최종안

> **목표**
>
> * 데이터 업로드(일/주/월 단위 스냅샷 포함)를 하나의 엔진으로 **정규화 → 키생성 → 중복검사 → 업서트 → 이력화**까지 일관 처리
> * **SSOT(Single Source of Truth)**: 캐논(Canonical) 저장층이 유일한 진실 원천
> * 데이터셋별 차이는 **어댑터(Adapter)**로만 분리, 나머지는 공통 엔진
> * 재업로드/중복에 **idempotent**(동일 입력이면 결과 변화 없음)
> * 스냅샷 업로드 시 **누락 레코드 정책**(ignore / soft_delete / hard_delete) 적용
> * **역할/업무 플로우**를 명확히 구분(프런트, 하우스키핑, 부대업장, 경영지원, 총지배인/대표)

---

## 0. 용어/원칙 정리 (핵심 합의)

* **rooms_status = 예약내역(동일 원본)**
  예약(Reservations)이라는 별도 개념을 **사용하지 않으며**, 모든 숙박/체크인/체크아웃/상태는 `rooms_status`로 일원화한다. 기존 `upload/reservations` 엔드포인트는 **rooms_status 정규화 경로**로 이미 구현되어 있으며, 문서/주석/화면에서도 일관되게 `rooms_status`로 표기한다.

* **Outlets vs. FNB**
  부대업장은 **아웃렛(Outlet)**으로 통일: 예) `LOUNGE`, `RESTAURANT`, `POOLSIDE`.
  FNB 자료는 `fnb_sales`(결제수단/상품)로 업로드하되 **`outlet_code`**로 식별한다.

* **Multi Accounts**
  은행/통장 데이터는 `account_code`(예: `NH-XXXX`)로 식별. 계좌 수 N개를 지원하며 정산/요약 시 계좌별 합산이 가능하다.

---

## 1. 전체 아키텍처

```
사용자(웹/CLI)
   │
   ├─ POST /api/upload/{dataset}
   │     (rooms_status, sales_front, fnb_sales(pay/items), expenses, bank_ledger)
   │     Form: business_date, property_code, dry_run, split_by_date, source_kind, file
   │
   └─[routers/board.py]──────────────────────────────────────────┐
        │                                                       │
        └─ services/merge_service.py ─► merge_engine/engine.py ─┼─ normalize(어댑터)
                                                                ├─ planner/diff/policies (드라이런/계획)
                                                                └─ repository (Canon/History/Batch 저장)
```

* **정규화 Normalization**: 기존 `app/core/normalize.py` 및 `normalize_bank.py` 재사용
* **어댑터 Adapter**: 데이터셋별 키 구성·스키마 검증·머지 모드 결정
* **엔진 Engine**: 공통 로직(드라이런/실행/머지/감사)
* **SSOT**: Canon 테이블이 최신 상태, History 테이블이 변경 이력
* **파일 보관**: 업로드 원본은 기존 `upload_sessions`/`uploaded_files` 경로/메타를 유지

---

## 2.Hotel System 백엔드 폴더 구조 (2025-10-11 기준 최신 SSOT 반영판)
backend/app/
├─ core/
│  ├─ auth.py
│  ├─ locale.py
│  ├─ i18n.py
│  ├─ settings.py
│  ├─ hashing.py                 # ✅ 존재 (make_key_hash, make_record_hash)
│  └─ settings_merge.py          # ⚙️ 예정 (MERGE_DEFAULTS, 정책 상수)
│
├─ datasets/
│  ├─ adapters/
│  │  ├─ base.py                 # ✅ 존재: DatasetAdapter, CanonRecord 베이스
│  │  ├─ rooms_status.py         # ✅ 존재: RoomsStatusAdapter
│  │  ├─ sales_front.py          # ⚙️ 예정
│  │  ├─ fnb_tenders.py          # ⚙️ 예정
│  │  ├─ fnb_items.py            # ⚙️ 예정
│  │  ├─ expenses.py             # ⚙️ 예정
│  │  └─ bank_ledger.py          # ⚙️ 예정
│  └─ schemas/
│     ├─ rooms_status.py         # ⚙️ 예정 (현재 adapter 내부 schema 사용 중)
│     ├─ sales_front.py          # ⚙️ 예정
│     ├─ fnb_tenders.py          # ⚙️ 예정
│     ├─ fnb_items.py            # ⚙️ 예정
│     ├─ expenses.py             # ⚙️ 예정
│     └─ bank_ledger.py          # ⚙️ 예정
│
├─ merge_engine/
│  ├─ engine.py                  # ✅ 존재: normalize → parse → preview 파이프라인
│  ├─ planner.py                 # ⚙️ 예정: 드라이런 계획 및 결과 요약
│  ├─ diff.py                    # ⚙️ 예정: Canon 대비 변경분 계산
│  ├─ policies.py                # ⚙️ 예정: 중복/누락 정책 로직
│  ├─ repository.py              # ⚙️ 예정: Canon/History CRUD
│  └─ audit.py                   # ⚙️ 예정: merge_batches, changelog 쓰기 헬퍼
│
├─ models/
│  ├─ __init__.py
│  ├─ closing.py
│  ├─ bank.py
│  ├─ user.py
│  ├─ role.py
│  ├─ employee.py
│  ├─ canon.py                   # ⚙️ 예정: *_canon/history 공통 베이스
│  └─ audit.py                   # ⚙️ 예정: merge_batches, merge_changelog ORM
│
├─ routers/
│  ├─ __init__.py
│  ├─ upload.py                  # ✅ 수정완료: merge_service 호출
│  ├─ closing.py
│  ├─ bank.py
│  ├─ reports_sales.py
│  ├─ reports_bank.py
│  ├─ board.py
│  └─ merge.py                   # ⚙️ 예정: /api/merge/logs, /api/merge/batches
│
├─ services/
│  ├─ __init__.py
│  └─ merge_service.py           # ✅ 존재: router → merge_engine bridge
│
├─ schemas/
│  ├─ closing.py
│  ├─ board.py
│  ├─ reports.py
│  └─ merge.py                   # ⚙️ 예정: MergeDryRunResp, MergeExecResp 등
│
├─ db/
│  ├─ base.py                    # ✅ Base 선언
│  ├─ session.py                 # ✅ get_db
│  └─ base_class.py              # ✅ DeclarativeBase
│
├─ main.py                       # ✅ 라우터 include(upload 등)
└─ __init__.py

상태 요약
모듈	상태	설명
core.hashing	✅	이미 사용 중 (make_key_hash, make_record_hash)
merge_engine.engine	✅	Dry-run 정상 동작 확인
services.merge_service	✅	upload 라우터 연결 완료
models.audit.py	⚙️ 예정	Alembic 기준 테이블 ORM 필요
routers.merge.py	⚙️ 예정	/api/merge/logs API 예정
schemas.merge.py	⚙️ 예정	dry_run / execute 응답 스키마
나머지 merge_engine.*	⚙️ 예정	Phase 2: diff/repository/policy 확장 시 생성
정리 메모 (버전 관리용)

> **파일 저장 경로 통일**
>
> * 모든 업로드 원본 저장 루트: **`/volume1/web/hotel-system/backend/_uploads`**
> * `bank.py`에 존재하던 `/uploads` 사용분은 마이그레이션 스크립트로 이동

---

## 3. 데이터 흐름과 규칙

### 3.1 업로드 케이스

* **일 데이터(append)**: 당일/특정일 데이터 추가 또는 일부 변경
* **주/월 스냅샷(snapshot)**: 기간 전체의 “정답 세트”로 간주 → 기존 누락 레코드 정책 적용

### 3.2 키/해시

* `key_hash = sha256("|".join(key_tuple))`
* `record_hash = sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False))`

### 3.3 중복/변경/누락 판단

* **NOOP**: 키 동일 + 레코드 해시 동일
* **UPSERT(갱신/신규)**: 키 동일 + 레코드 해시 변경 or 기존에 없음
* **누락**(스냅샷 전용): 기존 Canon에 있으나 새로운 스냅샷에 없는 키 → `soft_delete/hard_delete/ignore`

---

## 4. DB 스키마(요약; 신규 + 기존 유지)

### 4.1 업로드 메타(기존 유지)

* `upload_sessions` / `uploaded_files` (파일 백업 및 FE 히스토리 패널)

### 4.2 머지 배치 & 감사 (신규)

```sql
CREATE TABLE merge_batches (
  id BIGSERIAL PRIMARY KEY,
  dataset TEXT NOT NULL,
  property_code TEXT NOT NULL,
  mode TEXT NOT NULL,                  -- append | snapshot
  missing_policy TEXT NOT NULL,        -- ignore | soft_delete | hard_delete
  source_kind TEXT NOT NULL,           -- daily | weekly | monthly | full
  session_id BIGINT,                   -- upload_sessions.id
  version_no INT,
  created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE merge_changelog (
  id BIGSERIAL PRIMARY KEY,
  batch_id BIGINT NOT NULL REFERENCES merge_batches(id),
  action TEXT NOT NULL,                -- UPSERT | NOOP | SOFT_DELETE | HARD_DELETE
  key_hash TEXT NOT NULL,
  reason TEXT NULL,                    -- duplicate | content_changed | missing_in_snapshot ...
  old_hash TEXT NULL,
  new_hash TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT now()
);
```

### 4.3 Canon & History(데이터셋별 공통 패턴)

```sql
-- 예: rooms_status
CREATE TABLE rooms_status_canon (
  id BIGSERIAL PRIMARY KEY,
  key_hash TEXT UNIQUE NOT NULL,
  record_hash TEXT NOT NULL,
  valid_on DATE NOT NULL,              -- business_date
  payload_json JSONB NOT NULL,
  last_batch_id BIGINT REFERENCES merge_batches(id),
  updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE rooms_status_history (
  id BIGSERIAL PRIMARY KEY,
  key_hash TEXT NOT NULL,
  record_hash TEXT NOT NULL,
  valid_on DATE NOT NULL,
  payload_json JSONB NOT NULL,
  source_batch_id BIGINT REFERENCES merge_batches(id),
  created_at TIMESTAMP NOT NULL DEFAULT now()
);
```

> 다른 데이터셋도 동일 네이밍 규칙 적용(`<dataset>_canon`, `<dataset>_history`).

---

## 5. 어댑터 계약 (`datasets/adapters/base.py`)

```python
from typing import Iterable, Dict, Any, Tuple
from pydantic import BaseModel

class CanonRecord(BaseModel):
    business_date: str
    property_code: str
    payload: Dict[str, Any]
    key_tuple: Tuple[Any, ...]

class DatasetAdapter:
    dataset: str
    schema_model: BaseModel
    key_fields: Tuple[str, ...]
    default_missing_policy: str = "soft_delete"

    def normalize(self, raw_csv_text: str, fallback_business_date: str, property_code: str) -> str: ...
    def parse(self, canon_csv_text: str) -> Iterable[CanonRecord]: ...
    def merge_mode(self, form: Dict[str, Any]) -> str: ...  # 'append' | 'snapshot'
```

### 5.1 rooms_status 어댑터(핵심 예시)

* **키**: `(business_date, property_code, room_no)`
* **스키마**:

```python
# datasets/schemas/rooms_status.py
from pydantic import BaseModel
class RoomsStatusCanon(BaseModel):
    business_date: str
    property_code: str
    room_no: str
    status_code: str = ""
    is_dirty: str = ""
    hk_note: str = ""
```

* **구현 요지**:

  * `normalize()` → `core.normalize.normalize_rooms_status_to_canon` 재사용
  * `parse()` → DictReader로 행 순회, Pydantic 검증, `key_tuple` 구성
  * `merge_mode()` → `source_kind in (weekly, monthly, full)`이면 `snapshot`, 아니면 `append`

---

## 6. 머지 엔진

### 6.1 파이프라인(요약)

1. **정규화**: Adapter.normalize(raw_csv, form.business_date, form.property_code)
2. **파싱**: Adapter.parse(canon_csv) → `CanonRecord[]`
3. **해시**: key_hash/record_hash (core/hashing.py)
4. **모드 결정**: Adapter.merge_mode(form) → `append` or `snapshot`
5. **드라이런**: Canon과 비교해 **NOOP/UPSERT/DELETE 후보 수** 산출 + 날짜 분포/행수 요약
6. **실행**: `merge_batches` 생성 → append/snapshot 규칙에 따라 Canon/History 반영 + `merge_changelog` 기록

### 6.2 정책(defaults) — `settings_merge.py`

```python
MERGE_DEFAULTS = {
  "missing_policy": {
    "rooms_status": "soft_delete",
    "sales_front": "soft_delete",
    "fnb_tenders": "soft_delete",
    "fnb_items": "soft_delete",
    "expenses": "ignore",
    "bank_ledger": "ignore",
  }
}
```

---

## 7. API 계약 (라우터)

### 7.1 업로드 (공통)

`POST /api/upload/{dataset}`

**Form 필드**

* `business_date` (YYYY-MM-DD)
* `property_code` (기본 MOP)
* `dry_run` (0/1, 기본 1)
* `split_by_date` (0/1, rooms_status/sales_front/reservations 기본 1)
* `source_kind` (`daily|weekly|monthly|full`, 기본 daily)
* `file` (multipart csv)
* (옵션) `outlet_code` (FNB), `account_code` (Bank)

**드라이런 응답**

```json
{
  "ok": true,
  "dry_run": true,
  "business_date": "2025-09-01",
  "property_code": "MOP",
  "counts": { "rows": 1234 },
  "split_preview": [ {"business_date": "2025-09-01", "rows": 100} ],
  "plan": { "mode": "snapshot", "upsert_candidates": 120, "noop_candidates": 34, "delete_candidates": 2 }
}
```

**실행 응답**

```json
{
  "ok": true,
  "dry_run": false,
  "batch_id": 4815,
  "counts": { "upserted": 120, "deleted": 2, "noop": 34 },
  "mode": "snapshot",
  "saved_days": 3
}
```

> **호환성**: 기존 `/api/upload/canon`, `/api/upload/file`, `/api/upload/versions` 유지(파일 백업/다운로드 UI). SSOT 조회는 Canon 기준 API로 단계적 전환.

---

## 8. 프런트엔드 포인트

* 데이터셋 드롭다운: `rooms_status`, `sales_front`, `fnb_sales(pay/items)`, `expenses`, `bank_ledger`
* 업로드 기본 `split_by_date=1` (기간 CSV 자동 분할)
* **드라이런 보고서**: split 분포 + 예정 변경 수(UPSERT/DELETE/NOOP) 표기
* **이력 보기**: 파일 이력(현행) + **Merge 이력 탭**(배치/변경/삭제건수)

---

## 9. 업무 프로세스 × 역할 (확정)

### 9.1 프런트(Front Desk)

* **매일 21~22시**: 당일 **rooms_status(=예약내역)** 업로드.
* 업로드 후 **키워드 분류**로 조식 인원 추출(메모 기반 규칙/키워드 테이블).
* 조식 예상 인원은 **부대업장 팀**에 공유(대시보드 연동) — *확정(Confirm)* 플로우 제공(아래 9.3).

### 9.2 하우스키핑(AM 기준)

* **매일 08:00 이전**: 전일 **rooms_status** 확정본을 기준으로 **청소 유닛 계산** 및 배분.
* **유닛 규칙(초기값)**:

  * `숙박(체크아웃) = 1.0 유닛`
  * `재실(연박) = 0.3 유닛`
  * `층 이동 = 0.2 유닛`
  * `클레임으로 비계획 청소 = 0.2 유닛`
* 팀장 페이지: 인원 수에 따른 **절대 유닛 수** 기준 배분, 초과분은 **이월/추가배정** 결정.
* **키워드/OTA 설정 페이지(어드민)**: 유닛 산정에 쓰이는 상태코드/메모 키워드/채널별 가중치 설정.

### 9.3 부대업장(Outlets/FNB)

* **조식 현황 대시보드**: 프런트 업로드에서 생성된 조식 인원 확인 및 **당일 오전 확정 버튼**.
* **전일 매출 업로드(상품별/결제수단별)**: 통상 전일 퇴근 전에 업로드, 늦어도 당일 **12:00 이전**.
* 팀장 확정 시 해당 일자 아웃렛 데이터는 **업로드 완료** 상태 처리.

### 9.4 경영지원(회계/자금)

* **은행 입출금 업로드(pay_settlement/expenses)**: **당일 12:00 이전**.
* 주 5일 근무에 따른 **휴일 예외**: 휴일은 건너뛰고 영업일 시작일에 일괄 업로드 가능.
* 미업로드 일자는 **waive(패스) 처리** 기능 제공(일마감 중 은행 파트만 보류 가능).

### 9.5 마감(Closing)

* **슈퍼어드민/어드민**: 한 페이지에서 **업로드 현황/드라이런/확정/잠금**까지 수행 가능(현행 유지).
* 권한 분리 후에는 각 역할 페이지에 **해당 기능만 노출**(슈퍼어드민 화면은 유지).
* 최종 마감: 총지배인(ADMIN)/대표(SUPERADMIN)이 **CLOSE** 실행.

  * 상태 예: `OPEN → SUBMITTED(역할 확정) → CLOSED → LOCKED` (확장 가능).

---

## 10. 리포트/정산 포인트

* **Sales(Front)**: `sales_front` 태그/키워드 기반 **room_only/package/other** 요약(현행 `apply_keywords_and_summarize` 유지, Canon 전환 예정).
* **FNB**: `outlet_code`로 필터링/합산. 아웃렛 단위 대시보드 제공.
* **Bank**: `account_code`별 IN/OUT/NET, **전체 합계** 및 **잔액(last_balance)** 표시(현행 API 유지, 점차 Canon/History 또는 bank_txns 참조 일원화).
* **정산(일마감)**: 계좌별 잔액 합계 + FNB 매출 + 객실 매출(Front) 등으로 Net 계산(회계 정책에 따라 산식 고정).

---

## 11. 마이그레이션/개발 순서

1. **models 추가**: `canon.py`, `audit.py` + Alembic migration
2. **core/hashing.py**: `make_key_hash`, `make_record_hash`
3. **schemas/**: Pydantic 모델 작성 (rooms_status부터)
4. **adapters/base.py** + `adapters/rooms_status.py` 구현
5. **merge_engine/**: `engine/planner/diff/policies/repository/audit` 구현
6. **services/merge_service.py`**: 라우터 호출부
7. **routers/board.py**: `rooms_status`부터 엔진 경로로 스위치
8. **FE**: 드라이런 응답 구조/이력 탭 반영
9. **데이터 루트 통일** + 이전 파일 이동 스크립트
10. **reports_bank.py** 라우트 중복 정리(`/api/reports/bank-ledger` 단일화)

---

## 12. 운영/성능

* **배치 단위 Tx**: 1 업로드 = 1 배치, 커밋 단위 명확
* **인덱스**: `*_canon(key_hash UNIQUE)`, `*_history(key_hash)`, `merge_changelog(batch_id)`
* **대용량**: 정규화·파싱 스트리밍(필요 시) + COPY 고려
* **보관 정책**: History 장기, File 백업 90/180일 정책화
* **모니터링**: 배치별 counts/시간/에러 대시보드

---

## 13. 코드 스니펫(핵심)

### 13.1 hashing.py

```python
import hashlib, json
from typing import Tuple, Dict, Any

def make_key_hash(key_tuple: Tuple[Any, ...]) -> str:
    s = "|".join("" if v is None else str(v) for v in key_tuple)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def make_record_hash(payload: Dict[str, Any]) -> str:
    s = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()
```

### 13.2 merge_engine/engine.py(요지)

```python
def run_merge(adapter, form, file_bytes) -> dict:
    canon_csv = adapter.normalize(file_bytes.decode(...), form["business_date"], form["property_code"])
    records = list(adapter.parse(canon_csv))
    for rec in records:
        rec.key_hash = make_key_hash(rec.key_tuple)
        rec.record_hash = make_record_hash(rec.payload)

    mode = adapter.merge_mode(form)
    missing_policy = resolve_policy(adapter.dataset)

    if str(form.get("dry_run", 1)) == "1":
        plan = planner.plan(records, mode, missing_policy)
        return {"ok": True, "dry_run": True, **plan.preview()}

    batch_id = repository.create_batch(adapter.dataset, mode, missing_policy, form)
    result = diff.apply(batch_id, records, mode, missing_policy)
    return {"ok": True, "dry_run": False, "batch_id": batch_id, **result}
```

---

## 14. 백워드 호환 & 이관

* 기존 **파일 버전 저장** 경로는 유지(감사용/원본백업)
* SSOT 조회/통계/리포트는 **Canon 테이블 기준**으로 단계적 전환
* 초기에는 **rooms_status**부터 본 엔진 경로로 스위칭 → 안정화 → sales_front/FNB/expenses/bank 순차 도입

---

## 15. QA/시나리오

* **일자 혼합 업로드**: 행별 `business_date`로 자동 분배(분할 저장/머지).
* **append**: 키 신규/변경만 반영(동일 입력은 NOOP).
* **snapshot**: 입력이 정답 세트. 미포함 키는 정책대로 삭제(soft/hard/ignore).
* **재업로드**: idempotent — 동일 입력이면 Canon 변화 없음.

---

## 16. 역할 기반 접근/페이지 구성 (요약)

* **프런트**: rooms_status 업로드, 조식 추출/공유, 당일 조식 확정(확인 의미; CLOSE와 별개)
* **하우스키핑**: 유닛 계산/배분 페이지, 이월/추가배정, 상태 보정(클레임 청소 0.2 유닛)
* **부대업장**: 조식 대시보드, 전일 FNB 매출 업로드 및 확정(`outlet_code`)
* **경영지원**: 은행 입출금 업로드(pay_settlement/expenses), 휴일 waive 처리
* **관리자(ADMIN/SUPERADMIN)**: 업로드 현황/머지 배치/닫기/잠금, 권한 관리

---

### 결론

* 본 설계로 **하나의 엔진**에서 5개 데이터셋(객실상태/객실매출/FNB/지출/입금)을 동일 방식으로 처리하며,
* **일 단위 운영 + 주/월 스냅샷 보정**이 자연스럽게 수렴한다.
* 어댑터만 다루면 되므로 **유지보수/확장 용이**, 중복 개발을 방지하며 **SSOT 원칙**을 준수한다.


## Update Log — 2025-10-09 (Upload Bridge Phase 0.5)

1) upload.py
   - /api/upload/rooms_status 정상 동작.
   - /api/upload/sales_front, fnb_sales, bank_ledger 동일 패턴 유지.
   - 로깅 추가: [UPLOAD DEBUG] entered upload_rooms_status()

2) upload_apply.py
   - rooms_status, sales_front, fnb 각 데이터셋별 apply 함수 정리.
   - normalize_*_to_canon 사용.
   - commit 시점 명확화 (rollback 없음).
   - Canon 테이블 미사용, 기존 rooms_status/sales_front 테이블 직접 반영.

3) /api/upload/apply/rooms_status
   - _load_raw() 로드 후 normalize → delete+insert 수행.
   - upload_apply 브릿지 로직을 사용 중 (SSOT 엔진 전 단계).

4) Versions / Canon / Health
   - /api/upload/versions 정상 반환.
   - /api/upload/canon CSV 다운로드 정상.
   - /api/upload/ping 헬스 체크 OK.

5) 폴더 구조
   backend/app/
     routers/upload.py
     services/upload_service.py
     services/upload_apply.py
     core/normalize.py

6) 다음 단계 (Phase 1 예정)
   - datasets/adapters/*
   - merge_engine/*
   - Alembic: *_canon, *_history
   - merge_service.py
   - board.py → merge_service 호출로 전환

---

## Attention Notes (AI confusion record)

1) upload_apply vs SSOT merge_engine
   - 현재 upload_apply.py는 최종 엔진이 아님.
   - SSOT 설계서의 merge_engine/adapter 구조는 다음 단계에 도입 예정.
   - 즉, 지금은 “Phase 0.5: 기존 테이블 직접 반영 단계”.

2) apply_rooms_status
   - upload.py 내 apply 엔드포인트와 upload_apply.py 내 동일 이름 함수가 혼동 가능.
   - 라우터에서 서비스 함수 호출할 때 import alias로 _apply_rooms_status 로 사용 중.

3) logging 누락 문제
   - uvicorn.log가 아닌 app_debug.log에 기록될 수 있음.
   - logging.basicConfig 레벨과 핸들러 확인 필요.

4) openapi.json
   - /api/upload/debug_rooms_status 엔드포인트는 디버그용으로만 유지.
   - 정식 배포 시 제거 필요.

5) Canon 관련 404
   - /api/upload/canon, /versions가 빈 리스트를 반환하는 이유는
     upload_sessions/uploaded_files 메타는 존재하지만 Canon 테이블이 아직 없기 때문.
   - 정상 현상임 (Phase 0.5에서는 OK).

6) Phase naming
   - Phase 0.5 = 기존 upload_apply 안정화.
   - Phase 1 = SSOT merge_engine 도입.
   - Phase 2 = Canon 기반 Reports 전환.
---

## Environment Note — 2025-10-09 (Dev/Prod, Logging, Monitoring)

1) 서버 구분
   - 개발 서버: http://192.168.0.6:5173  (프론트 dev, 백엔드 포트 8001)
   - 운영 서버: http://127.0.0.1:8000  (동일 NAS, 테스트용 의미만 있음)
   - 두 서버는 동일 장비(Synology NAS) 내에서 동시 기동 중.

2) 로그 관리
   - 현재 주요 로그 파일 경로:
     /volume1/web/hotel-system/logs/
       ├─ uvicorn.log
       └─ uvicorn.foreground.log
   - 기존 app_debug.log 파일은 삭제 예정 (중복 기록 방지 목적).
   - uvicorn.foreground.log 는 실시간 콘솔 출력과 동일 내용.

3) 샘플 데이터
   - 현재 NAS 내부에는 테스트용 CSV, 샘플 파일 존재하지 않음.
   - 필요 시 원본 데이터를 업로드해야 함.
   - 기본 업로드 대상 폴더는:
     /volume1/web/hotel-system/backend/_uploads
   - 샘플을 제공할 때는 해당 경로 아래에 직접 배치.

4) 개발 환경
   - 개발 시 Windows PowerShell에서 터미널 4개를 동시에 띄워 사용 중.
   - 상단 좌: 백엔드 서버 로그 모니터링 (uvicorn foreground)
   - 상단 우: Vite 프론트엔드 dev 서버 (포트 5173)
   - 하단 좌: 명령 실행 및 테스트용 셸 (curl 등)
   - 하단 우: 실시간 디버깅 로그 확인 창 (multipart/middleware 로그 확인)

5) 기타 메모
   - multipart.multipart DEBUG 로그는 파일 업로드 스트림 로그이며 오류 아님.
   - 운영 서버(8000)는 프록시 라우팅 확인용만으로 유지.
   - 로그 모니터링 상태 정상.

---

## Update Log — 2025-10-09 (Uploads Folder Structure Confirmed)

1) 업로드 루트
   - 절대 경로: /volume1/web/hotel-system/backend/_uploads
   - 역할: 모든 업로드 원본 및 테스트 데이터의 SSOT 저장소

2) 데이터셋별 하위 폴더
   /_uploads/
     ├─ sales_front/
     ├─ rooms_status/
     ├─ fnb_sales/
     ├─ bank_ledger/
     ├─ expenses/            (생성 예정, pay_settlement와 동일 레벨)
     └─ _debug/              (임시 테스트용, 자동 생성 가능)

3) property_code별 구조
   - 각 데이터셋 폴더 내부는 property_code(예: MOP) 단위로 구분됨
     예시:
       /_uploads/sales_front/MOP/
       /_uploads/rooms_status/MOP/
       /_uploads/fnb_sales/MOP/

4) 날짜별 구조
   - property_code 하위에는 날짜(YYYY-MM-DD) 폴더 단위로 저장
     예시:
       /_uploads/sales_front/MOP/2025-09-23/
       /_uploads/sales_front/MOP/2025-09-24/
       /_uploads/sales_front/MOP/2025-10-08/

5) 파일 저장 규칙
   - 각 날짜 폴더에는 CSV 파일 1~N개 존재 가능
   - 파일명 예시:
       sales_front_MOP_2025-09-27_1.csv
       rooms_status_MOP_2025-09-26_1.csv
   - 파일명 패턴: {dataset}_{property_code}_{YYYY-MM-DD}_{seq}.csv

6) 특이 케이스
   - pay_settlement, expenses 데이터는 구조 동일하지만 스키마 필드가 다를 수 있음.
   - CSV 내용은 canonical 스키마 기준 정합성 검증 필요 (추후 adapter 적용 예정).

7) 활용 규칙
   - 샘플/테스트 데이터를 넣을 때는 해당 데이터셋 → property_code → 날짜 폴더에 직접 저장.
   - 예:
     ```
     /volume1/web/hotel-system/backend/_uploads/expenses/MOP/2025-10-09/sample.csv
     ```
   - `_debug` 폴더는 임시 테스트 시 자동 생성 가능, Git ignore 권장.

---

## Update Log — 2025-10-09 (Phase 0.5 → Phase 1 Transition)

### 현행 구현 완료 (Phase 0.5)

| 구분                    | 상태      | 설명                                                                     |
| --------------------- | ------- | ---------------------------------------------------------------------- |
| **upload.py**         | V 정상    | `/api/upload/rooms_status` 정상 동작, sales_front·fnb·bank 동일 구조           |
| **upload_apply.py**   | V 브릿지   | Canon 미사용, 기존 테이블 직접 반영(`delete+insert`)                               |
| **upload_service.py** | V 헬퍼    | `_store_file`, `_get_or_create_session`, `_next_version` 모두 정상         |
| **logging**           | ️? 확인   | `[UPLOAD DEBUG] entered upload_rooms_status()` 콘솔/uvicorn.log 출력 확인 완료 |
| **폴더 구조**             | V 확정    | `_uploads/{dataset}/{property_code}/{YYYY-MM-DD}/v{n}` 패턴 정상           |
| **프런트 연결 준비**         | V 사전 완료 | FE 호출 포인트/엔드포인트 확인(프록시 5173 → 8001)                                    |
| **테스트**               | V 성공    | curl 테스트 및 log 200 OK, 파일 저장 확인 완료                                     |

---

## Next Step — Phase 1 (SSOT Merge Engine 도입)

| 단계                        | 주요 목표                                                             | 대상 파일/폴더                                | 비고                                               |
| ------------------------- | ----------------------------------------------------------------- | --------------------------------------- | ------------------------------------------------ |
| **1. Alembic 마이그레이션 추가**  | `_canon`, `_history`, `merge_batches`, `merge_changelog` 테이블 생성   | `backend/alembic/versions/ssot_init.py` | `alembic revision -m "ssot_init" --autogenerate` |
| **2. Dataset Adapter 확장** | `datasets/adapters/{sales_front,fnb,expenses,bank_ledger}.py` 작성  | 재사용: rooms_status 어댑터 구조                | 키/스키마 필드만 변경                                     |
| **3. Merge Engine 본체 구축** | `merge_engine/{engine,planner,diff,repository,policies,audit}.py` | 현재 `engine.py` 기준으로 확장                  | diff/plan/repo 로직 추가                             |
| **4. 서비스 브리지 교체**         | `services/merge_service.py` 신규 → upload.py가 이 경로 호출               | 기존 `_apply_rooms_status` 교체 예정          | 동일 응답 구조 유지                                      |
| **5. Canon 모델/스키마 추가**    | `models/canon.py`, `schemas/merge.py`                             | 각 dataset별 Canon/History ORM + Schema   | Pydantic v2 `from_attributes=True`               |
| **6. Router 스위치**         | `/api/upload/{dataset}` → merge_service 경로로 전환                    | `routers/board.py` 수정                   | rooms_status부터 전환 후 단계 확장                        |
| **7. QA 및 프런트 연동**        | 드라이런 결과 → FE 히스토리 탭 표시                                            | `/api/upload/{dataset}?dry_run=1`       | counts/plan.preview 표시                           |

---

##  진행 시 유의사항

* **기존 테이블**(`rooms_status`, `sales_front`)은 Phase 1 종료 전까지 유지 (마이그레이션 안정화 후 폐기).
* **모든 신규 Canon 테이블은 `key_hash UNIQUE` 인덱스 필수.**
* **드라이런 응답**(`preview`)은 JSON 직렬화 안전한 데이터만 포함(key_tuple, payload).
* **phase2 보고서 전환 시점에 기존 Reports 라우트(canon 기반)로 연결 예정.**
* **테스트용 CSV는 반드시 `_uploads` 내 올바른 property/date 경로에 직접 배치.**

---

Incident Memo — Alembic + SQLite 오토젠 이슈
증상

alembic upgrade head 중 sqlite OperationalError near "ALTER" 발생.

오토젠 리비전에 DROP / ALTER COLUMN 등이 대거 포함되어 데이터 손실 위험 존재.

원인

--autogenerate 남용

모델 변경 추적 과정에서 Alembic이 기존 테이블(rooms_status, sales_front, fnb_*, upload_files 등)을 삭제/형변경 대상으로 오판.

SQLite DDL 제약

SQLite는 대부분의 ALTER COLUMN을 지원하지 않음. 오토젠이 만든 DDL이 그대로 실패.

env.py 기본설정

안전장치(드랍 차단, 필드 변경 차단) 없이 비교 설정 그대로 사용.

해결

문제 리비전(dc6ab0638941)을 수동으로 교체:

파괴적 변경 제거, CREATE TABLE IF NOT EXISTS 방식으로 추가만 수행.

결과적으로 merge_*, rooms_status_* Canon/History만 안전하게 생성.

이후 적용: alembic upgrade head 정상.

재발 방지 체크리스트
1) 오토젠 가드

원칙: 운영/공용 DB에서 --autogenerate로 나온 스크립트를 그대로 적용하지 않는다.

오토젠 생성 후 필수 수동 리뷰:

op.drop_table, op.drop_index, op.alter_column, op.create_unique_constraint 등 파괴적/제약 변경이 있으면 전면 수정.

리비전 파일 헤더에 태그: # SQLite-safe, NO DROP/ALTER 명시.

2) env.py 안전 설정 예시

드랍/변경 후보 필터링: (불필요 변경 차단)

# alembic/env.py
from alembic.autogenerate import comparators

def include_object(object, name, type_, reflected, compare_to):
    # 테이블 드랍/생성: 반드시 수동 관리
    if type_ == "table":
        return True  # 생성은 허용하되 DROP은 리비전에서 금지 원칙
    return True

def process_revision_directives(context, revision, directives):
    # 자동으로 대형 변경이 묶이는 것을 한번 더 경고/검증할 수 있는 훅
    script = directives[0]
    if hasattr(script, "upgrade_ops"):
        ddl = str(script.upgrade_ops)
        forbidden = ("drop_table", "alter_column")
        if any(k in ddl for k in forbidden):
            raise RuntimeError("Unsafe DDL detected in autogenerate. Review required.")


SQLite 배치 모드(나중에 정말 ALTER가 필요할 때만):

context.configure(
    connection=connection,
    target_metadata=target_metadata,
    render_as_batch=True,   # SQLite ALTER 우회(테이블 재작성)
)

3) “추가만” 템플릿 운용

새 테이블/인덱스는 op.execute("CREATE TABLE IF NOT EXISTS ..."),
op.execute("CREATE INDEX IF NOT EXISTS ...") 패턴으로 통일.

기존 컬럼 변경 필요 시:

SQLite는 컬럼 변경이 어려우므로 새 테이블 생성 → 데이터 마이그레이션 → 스왑 전략 사용(별도 리비전에서).

4) CI 사전 검증

PR마다 임시 SQLite로 마이그레이션 풀 체인 테스트:

rm -f tmp.db
sqlite3 tmp.db "VACUUM;"
alembic upgrade base
alembic upgrade head   # 실패 시 CI 차단

5) 운영 수칙

운영 DB에선 백업 후 적용:

cp hotel.db hotel.db.bak.$(date +%F-%H%M)
alembic upgrade head


마이그레이션 실패 시 즉시 롤백:

mv hotel.db.bak.* hotel.db   # 방금 백업으로 복구

이번 변경 요지(요약)

리비전 dc6ab0638941: DROP/ALTER 제거, IF NOT EXISTS 기반 생성만 수행하도록 수정.

생성 대상: merge_batches(이미 있으면 skip), merge_changelog(+index), rooms_status_canon(+index), rooms_s

 현재 실제 샘플 경로 구조 (확정)
/volume1/web/hotel-system/backend/_uploads/
 ├─ sales_front/
 │   └─ MOP/2025-10-08/...
 ├─ rooms_status/
 │   └─ MOP/2025-10-08/...
 ├─ fnb_sales/
 │   └─ MOP/2025-10-08/...
 ├─ expenses/
 │   └─ ...
 ├─ pay_settlement/
 │   └─ ...
 └─ (CSV 루트 샘플들 sales_front_MOP_2025-09-27_1.csv 등)

 테스트용 표준 파일 지정 (이미 존재하는 샘플을 그대로 사용)

예시로 rooms_status는 아래 경로를 사용해야 해:

/volume1/web/hotel-system/backend/_uploads/rooms_status_MOP_2025-09-23_1.csv

 정확한 테스트 명령 (지금 환경 기준)
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F property_code=MOP \
  -F business_date=2025-09-23 \
  -F dry_run=0 \
  -F "file=@backend/_uploads/rooms_status_MOP_2025-09-23_1.csv;type=text/csv" \
  "http://127.0.0.1:8000/api/upload/rooms_status" | jq .


 정리해서 설계서/메모에 추가할 문장:

모든 테스트 및 샘플 CSV는 /backend/_uploads/ 구조를 그대로 사용한다.
이 폴더가 운영·개발 겸용 업로드 캐시이자 테스트용 샘플 저장소 역할을 한다.
data_samples 폴더는 생성하지 않으며, 테스트 명령 시 file=@backend/_uploads/... 경로를 직접 지정한다.
예: rooms_status_MOP_2025-09-23_1.csv

 요약 메모 기록 (캔버스용)

/api/upload/rooms_status 응답 200 OK but 본문 없음 → return JSONResponse(content=...) 누락.

FastAPI 로그 200 OK만 찍히고 multipart 디버그만 반복됨.

curl: (26) → 파일 핸들러 조기 종료.

해결: upload.py 내 return run_merge → return JSONResponse(content=run_merge(...)) 로 수정.

메모(재발 방지)

dc6ab0638941_ssot_init.py에서 레거시 DROP이 들어갔습니다. SQLite는 ALTER COLUMN도 미흡해서 오류도 섞여 나옵니다.

다음 리비전에서: 레거시 DROP 제거(또는 주석), SQLite 호환만 남기기.

또는 운영/개발 분기: prod는 DROP 금지, dev만 DROP 허용.

(메모) 재발 방지

ssot_init 리비전에서 레거시 DROP 금지(다음 리비전에 DROP 제거/주석).

/api/upload/apply/rooms_status는 레거시 테이블 사용 중 ⇒ Phase1에서 canon 반영으로 교체.

# FNB Upload 적용 실패 원인 분석

- **에러:** RuntimeError: no uploaded fnb_sales file for 2025-09-23 MOP part=items  
- **원인:** upload_sessions/upload_files에 fnb_sales(items) 파일 기록 없음  
- **대책:**  
  1. `/api/upload/fnb_sales` 먼저 호출 후 apply 수행  
  2. 파일 2개(`file_pay`, `file_items`) 모두 업로드해야 함  
  3. 업로드 정상 시 upload_files.part_key(pay, items) 2건 생성 확인  

- **검증 SQL**
  ```sql
  SELECT * FROM upload_sessions WHERE dataset='fnb_sales';
  SELECT * FROM upload_files WHERE session_id IN (
    SELECT id FROM upload_sessions WHERE dataset='fnb_sales'
  );

7.x 호출 가이드 (Phase 0.5 기준)

인증: 모든 엔드포인트에 X-Internal-Token: dev-admin-token 헤더 필요
베이스 URL 예시: http://192.168.0.6:8001 (개발), http://127.0.0.1:8000 (로컬)
참고: 운영 보안을 위해 /openapi.json은 비활성화되어 404일 수 있음(정상)

A. 업로드 공통 (드라이런 → 실행)
1) Rooms Status (= 예약내역)

드라이런

curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-09-23 \
  -F property_code=MOP \
  -F dry_run=1 \
  -F split_by_date=1 \
  -F source_kind=daily \
  -F "file=@backend/_uploads/rooms_status_MOP_2025-09-23_1.csv;type=text/csv" \
  "http://192.168.0.6:8001/api/upload/rooms_status" | jq .

실행

curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-09-23 \
  -F property_code=MOP \
  -F dry_run=0 \
  -F split_by_date=1 \
  -F source_kind=daily \
  -F "file=@backend/_uploads/rooms_status_MOP_2025-09-23_1.csv;type=text/csv" \
  "http://192.168.0.6:8001/api/upload/rooms_status" | jq .

2) Sales Front
# 드라이런
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-09-23 -F property_code=MOP \
  -F dry_run=1 -F split_by_date=0 \
  -F "file=@backend/_uploads/sales_front_MOP_2025-09-23_1.csv;type=text/csv" \
  "http://192.168.0.6:8001/api/upload/sales_front" | jq .

# 실행
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-09-23 -F property_code=MOP \
  -F dry_run=0 -F split_by_date=0 \
  -F "file=@backend/_uploads/sales_front_MOP_2025-09-23_1.csv;type=text/csv" \
  "http://192.168.0.6:8001/api/upload/sales_front" | jq .

3) FNB Sales (결제/상품 2파일 업로드)
# 드라이런
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-09-23 -F property_code=MOP \
  -F dry_run=1 \
  -F "file_pay=@backend/_uploads/fnb_sales_MOP_2025-09-23_pay.csv;type=text/csv" \
  -F "file_items=@backend/_uploads/fnb_sales_MOP_2025-09-23_items.csv;type=text/csv" \
  "http://192.168.0.6:8001/api/upload/fnb_sales" | jq .

# 실행
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-09-23 -F property_code=MOP \
  -F dry_run=0 \
  -F "file_pay=@backend/_uploads/fnb_sales_MOP_2025-09-23_pay.csv;type=text/csv" \
  -F "file_items=@backend/_uploads/fnb_sales_MOP_2025-09-23_items.csv;type=text/csv" \
  "http://192.168.0.6:8001/api/upload/fnb_sales" | jq .

4) Bank Ledger
# 드라이런
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-09-23 -F property_code=MOP \
  -F account_code=NH-UNKNOWN -F dry_run=1 \
  -F "file=@backend/_uploads/bank_ledger_MOP_2025-09-23.csv;type=text/csv" \
  "http://192.168.0.6:8001/api/upload/bank_ledger" | jq .

# 실행
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-09-23 -F property_code=MOP \
  -F account_code=NH-UNKNOWN -F dry_run=0 \
  -F "file=@backend/_uploads/bank_ledger_MOP_2025-09-23.csv;type=text/csv" \
  "http://192.168.0.6:8001/api/upload/bank_ledger" | jq .

B. 레거시 적용(Bridge) — Phase 0.5

SSOT 머지엔진 정착 전, 기존 테이블에 직접 반영하는 “apply” 경로

# Sales Front 적용
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-09-23 -F property_code=MOP \
  "http://192.168.0.6:8001/api/upload/apply/sales_front" | jq .

# Rooms Status 적용
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-09-23 -F property_code=MOP \
  "http://192.168.0.6:8001/api/upload/apply/rooms_status" | jq .

# FNB 적용 (part=tenders | items)
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-09-23 -F property_code=MOP -F part=tenders \
  "http://192.168.0.6:8001/api/upload/apply/fnb" | jq .

curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-09-23 -F property_code=MOP -F part=items \
  "http://192.168.0.6:8001/api/upload/apply/fnb" | jq .


주의(FNB): apply 전에 반드시 /api/upload/fnb_sales로 file_pay와 file_items 두 파일 모두 업로드돼 있어야 함.

C. 파일 이력/다운로드 (board 라우터)

버전 목록 조회

curl -s -H "X-Internal-Token: dev-admin-token" \
  "http://192.168.0.6:8001/api/download/versions?dataset=rooms_status&business_date=2025-09-23&property_code=MOP" | jq .


최신 파일 다운로드

curl -i -H "X-Internal-Token: dev-admin-token" \
  "http://192.168.0.6:8001/api/download/file?dataset=rooms_status&business_date=2025-09-23&property_code=MOP"


특정 버전 다운로드 (예: 2)

curl -i -H "X-Internal-Token: dev-admin-token" \
  "http://192.168.0.6:8001/api/download/file?dataset=rooms_status&business_date=2025-09-23&property_code=MOP&version_no=2"


파일 존재/경로 매칭 실패 시 404(not-found 또는 file-missing)가 반환됨.

D. 파일 보관 디렉터리 규칙

루트: /volume1/web/hotel-system/backend/_uploads

경로: /_uploads/{dataset}/{property_code}/{YYYY-MM-DD}/v{n}/...

예:
/volume1/web/hotel-system/backend/_uploads/rooms_status/MOP/2025-09-23/v2/rooms_status_MOP_2025-09-23_1.csv

테스트 시 권장 입력 경로(샘플 파일 직지정)

@backend/_uploads/rooms_status_MOP_2025-09-23_1.csv (rooms_status)

동일 규칙으로 sales_front / fnb / bank_ledger도 준비

E. 빠른 점검 체크리스트

업로드는 200인데 적용이 안 된다 → apply/* 호출 누락 여부 확인 (Phase 0.5 한정)

FNB 에러 no uploaded fnb_sales file … part=items → fnb_sales 업로드에서 두 파일(pay/items) 모두 필요

/openapi.json 404 → 정상(보안/설정상 비공개). 개별 엔드포인트 200이 핵심

다운로드 404 → DB 메타엔 존재하나 실제 파일 경로가 사라졌는지 확인
(DB: upload_sessions/uploaded_files, 디스크: _uploads/...)

F. (참고) 검증 SQL 스니펫
-- 세션 존재 여부
SELECT * FROM upload_sessions
 WHERE dataset='rooms_status' AND business_date='2025-09-23' AND property_code='MOP';

-- 파일 메타
SELECT id, session_id, version_no, part_key, filename, stored_path, created_at
  FROM uploaded_files
 WHERE session_id IN (
   SELECT id FROM upload_sessions
    WHERE dataset='rooms_status' AND business_date='2025-09-23' AND property_code='MOP'
 )
 ORDER BY version_no DESC, id DESC;

4) 현재 단계(Phase 0.5) 메모

bank_ledger는 업로드→정규화→원본보관까지 동작.

별도의 /apply/bank_ledger는 아직 없음(보고/집계는 현행 reports_bank 경로가 담당).

필요하면 다음 작업으로 apply_bank_ledger(또는 Canon 전환) 추가하면 됨.

7.x 호출 가이드 (Phase 0.5 기준) — 운영 메모

인증/접속

모든 엔드포인트: X-Internal-Token: dev-admin-token 필요

베이스 URL: 개발 http://192.168.0.6:8001, 로컬 http://127.0.0.1:8000

보안상 /openapi.json은 비활성화(404 정상). 각 API 응답 200 여부로 점검

파일 이력/다운로드 라우터

다운로드 계열은 board.py가 제공: /api/download/…

업로드 메타(세션/파일)는 계속 upload_sessions / uploaded_files 사용

A) 업로드 공통(드라이런→실행)

Rooms Status (= 예약내역)

# 드라이런
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-09-23 -F property_code=MOP \
  -F dry_run=1 -F split_by_date=1 -F source_kind=daily \
  -F "file=@backend/_uploads/rooms_status_MOP_2025-09-23_1.csv;type=text/csv" \
  "http://192.168.0.6:8001/api/upload/rooms_status" | jq .

# 실행
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-09-23 -F property_code=MOP \
  -F dry_run=0 -F split_by_date=1 -F source_kind=daily \
  -F "file=@backend/_uploads/rooms_status_MOP_2025-09-23_1.csv;type=text/csv" \
  "http://192.168.0.6:8001/api/upload/rooms_status" | jq .


Sales Front

# 드라이런
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-09-23 -F property_code=MOP -F dry_run=1 -F split_by_date=0 \
  -F "file=@backend/_uploads/sales_front_MOP_2025-09-23_1.csv;type=text/csv" \
  "http://192.168.0.6:8001/api/upload/sales_front" | jq .

# 실행
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-09-23 -F property_code=MOP -F dry_run=0 -F split_by_date=0 \
  -F "file=@backend/_uploads/sales_front_MOP_2025-09-23_1.csv;type=text/csv" \
  "http://192.168.0.6:8001/api/upload/sales_front" | jq .


FNB Sales (결제/상품 2파일)

# 드라이런
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-09-23 -F property_code=MOP -F dry_run=1 \
  -F "file_pay=@backend/_uploads/fnb_sales_MOP_2025-09-23_pay.csv;type=text/csv" \
  -F "file_items=@backend/_uploads/fnb_sales_MOP_2025-09-23_items.csv;type=text/csv" \
  "http://192.168.0.6:8001/api/upload/fnb_sales" | jq .

# 실행
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-09-23 -F property_code=MOP -F dry_run=0 \
  -F "file_pay=@backend/_uploads/fnb_sales_MOP_2025-09-23_pay.csv;type=text/csv" \
  -F "file_items=@backend/_uploads/fnb_sales_MOP_2025-09-23_items.csv;type=text/csv" \
  "http://192.168.0.6:8001/api/upload/fnb_sales" | jq .


Bank Ledger

# 드라이런
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-09-23 -F property_code=MOP -F account_code=NH-UNKNOWN -F dry_run=1 \
  -F "file=@backend/_uploads/bank_ledger_MOP_2025-09-23.csv;type=text/csv" \
  "http://192.168.0.6:8001/api/upload/bank_ledger" | jq .

# 실행
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-09-23 -F property_code=MOP -F account_code=NH-UNKNOWN -F dry_run=0 \
  -F "file=@backend/_uploads/bank_ledger_MOP_2025-09-23.csv;type=text/csv" \
  "http://192.168.0.6:8001/api/upload/bank_ledger" | jq .

B) 레거시 반영(Bridge) — apply 경로

SSOT 본엔진 도입 전까지 일시 사용(rooms/sales/fnb만 존재)

# Sales Front 적용
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-09-23 -F property_code=MOP \
  "http://192.168.0.6:8001/api/upload/apply/sales_front" | jq .

# Rooms Status 적용
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-09-23 -F property_code=MOP \
  "http://192.168.0.6:8001/api/upload/apply/rooms_status" | jq .

# FNB 적용 (part=tenders | items)
for part in tenders items; do
  curl -s -H "X-Internal-Token: dev-admin-token" \
    -F business_date=2025-09-23 -F property_code=MOP -F part=$part \
    "http://192.168.0.6:8001/api/upload/apply/fnb" | jq .
done


⚠️ FNB는 apply 전에 반드시 /api/upload/fnb_sales로 file_pay/file_items 둘 다 업로드되어 있어야 함.

C) 파일 이력/다운로드 (board 라우터)
# 버전 목록
curl -s -H "X-Internal-Token: dev-admin-token" \
  "http://192.168.0.6:8001/api/download/versions?dataset=rooms_status&business_date=2025-09-23&property_code=MOP" | jq .

# 최신 파일
curl -i -H "X-Internal-Token: dev-admin-token" \
  "http://192.168.0.6:8001/api/download/file?dataset=rooms_status&business_date=2025-09-23&property_code=MOP"

# 특정 버전
curl -i -H "X-Internal-Token: dev-admin-token" \
  "http://192.168.0.6:8001/api/download/file?dataset=rooms_status&business_date=2025-09-23&property_code=MOP&version_no=2"


404시: DB메타는 있으나 실파일 경로 불일치(file-missing) 또는 세션/레코드 없음(not-found) 가능.

D) 파일 보관 규칙

루트: /volume1/web/hotel-system/backend/_uploads

경로 규칙: /_uploads/{dataset}/{property_code}/{YYYY-MM-DD}/v{n}/...

테스트 시 샘플 직접 지정 권장:

예) @backend/_uploads/rooms_status_MOP_2025-09-23_1.csv

E) 빠른 점검 체크리스트

업로드는 200인데 반영 X → apply 호출 누락(Phase 0.5 한정)

FNB 에러 no uploaded ... items → pay/items 파일 둘 다 업로드 필요

/openapi.json 404 → 정상(비공개 설정)

다운로드 404 → 경로/파일 존재 확인(DB vs 디스크)

F) 검증 SQL 스니펫
-- 세션 존재
SELECT * FROM upload_sessions
 WHERE dataset='rooms_status' AND business_date='2025-09-23' AND property_code='MOP';

-- 파일 메타
SELECT id, session_id, version_no, part_key, filename, stored_path, created_at
  FROM uploaded_files
 WHERE session_id IN (
   SELECT id FROM upload_sessions
    WHERE dataset='rooms_status' AND business_date='2025-09-23' AND property_code='MOP'
 )
 ORDER BY version_no DESC, id DESC;

G) 주의 및 회고(재발 방지)

/api/upload/rooms_status에서 본문 누락 사례 → 반환 시 JSON 본문 보장(예: JSONResponse(content=...)) 확인

Alembic(SQLite) DROP/ALTER 금지 원칙. 신규는 CREATE … IF NOT EXISTS로만.
운영 반영 전 DB 백업 필수: cp hotel.db hotel.db.bak.$(date +%F-%H%M)


