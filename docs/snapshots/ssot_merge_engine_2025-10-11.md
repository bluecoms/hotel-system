아래 내용을 **그대로** `docs/runbooks/structure_backend_2025-10-11.md` 로 저장하세요. (생략 없음)

---

# Hotel System 백엔드 폴더 구조 (2025-10-11 기준 최신 SSOT 반영판)

> **문서 목적 (SSOT)**
>
> 이 문서는 백엔드 폴더 구조의 **단일 진실 원본(Single Source of Truth)** 입니다.
> 모든 설계/개발/리팩터링/QA 문서는 본 구조를 기준으로 작성·검증합니다.
> “⚙️ 예정” 항목이 구현되면 반드시 본 문서를 **즉시 갱신**합니다.

* 문서 버전: `2025-10-11` (Phase 1 finalized)
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
│  ├─ engine.py                  # ✅ 존재: normalize → parse → preview/execute 파이프라인
│  ├─ planner.py                 # ⚙️ 예정: 드라이런 계획 및 결과 요약
│  ├─ diff.py                    # ⚙️ 예정: Canon 대비 변경분 계산
│  ├─ policies.py                # ⚙️ 예정: 중복/누락 정책 로직
│  ├─ repository.py              # ✅ 존재: Canon/History CRUD, MergeBatch/ChangeLog 기록
│  └─ audit.py                   # ⚙️ 예정: merge_batches, changelog API/도우미
│
├─ models/
│  ├─ __init__.py
│  ├─ closing.py
│  ├─ bank.py
│  ├─ user.py
│  ├─ role.py
│  ├─ employee.py
│  ├─ canon.py                   # ✅ 존재: rooms_status_canon, rooms_status_history
│  └─ audit.py                   # ✅ 존재: merge_batches, merge_changelog ORM
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
```

---

## 2) 상태 요약 (Phase 1 기준)

| 모듈/경로                                      | 상태 | 설명                                                 |
| ------------------------------------------ | -- | -------------------------------------------------- |
| `core.hashing`                             | ✅  | 이미 사용 중 (`make_key_hash`, `make_record_hash`)      |
| `merge_engine.engine`                      | ✅  | Dry-run/Execute 정상 동작, Canon/History 반영(Phase 1)   |
| `merge_engine.repository`                  | ✅  | Canon/History CRUD + MergeBatch/ChangeLog 기록 Layer |
| `services.merge_service`                   | ✅  | Router → Engine 브리지, 예외/로그 처리                      |
| `models.audit.py`                          | ✅  | Alembic 반영 ORM: `merge_batches`, `merge_changelog` |
| `models.canon.py`                          | ✅  | `rooms_status_canon`, `rooms_status_history`       |
| `routers.merge.py`                         | ⚙️ | 예정: 배치/로그 조회 API (`/api/merge/...`)                |
| `schemas.merge.py`                         | ⚙️ | 예정: DryRun/Execute 응답 스키마                          |
| `datasets.schemas/*`                       | ⚙️ | 예정: dataset별 Pydantic schema 모듈화                   |
| `merge_engine.diff/policies/planner/audit` | ⚙️ | 예정: Phase 2 확장 (삭제/누락/정책/리포트)                      |

> **원칙:** “⚙️ 예정” 이 구현되면 표를 **즉시 갱신**하고, 구조 트리의 해당 파일도 ✅로 전환합니다.

---

## 3) 변경 관리 원칙

* **문서 위치(SSOT)**: `docs/runbooks/structure_backend_YYYY-MM-DD.md`

  * 본 문서는 덮어쓰지 않고 **날짜 버전으로 누적**합니다.
  * 최신판을 참조 링크로 프로젝트 README/CONTRIBUTING에 연결합니다.
* **갱신 트리거**

  1. Alembic 마이그레이션 추가/변경 (테이블/인덱스/제약 포함)
  2. 새 모듈/파일 생성 (예: `merge_engine.diff`)
  3. 라우터/서비스 추가 또는 API 계약 변경
  4. Phase 전환 (0.5 → 1, 1 → 2 등)
* **코드 주석 버전 헤더**

  ```python
  # version: 2025-10-11 Phase 1 finalized
  ```
* **폴더 계층** 변경 금지

  * 기존 계층 하위에만 파일 추가
  * 계층 이동/이름 변경은 RFC(승인 문서)로 별도 합의 후 진행

---

## 4) 운영 점검/스냅샷 절차

```bash
# 1) 구조 스냅샷 저장
cd /volume1/web/hotel-system/backend/app
tree -L 3 > ../../../docs/runbooks/snapshots/backend_tree_$(date +%F).txt

# 2) 최신 SSOT 문서와 차이 비교
diff -u \
  docs/runbooks/structure_backend_2025-10-11.md \
  docs/runbooks/snapshots/backend_tree_$(date +%F).txt | less
```

* 차이가 발견되면, **이 문서(SSOT)** 를 우선 갱신하고 커밋 메시지에 `SSOT:structure updated`를 포함합니다.

---

## 5) 프런트엔드 연동 주의사항 (요약)

* 업로드 엔드포인트(공통): `POST /api/upload/{dataset}`

  * `rooms_status`, `sales_front`, `fnb_sales`, `expenses`, `bank_ledger` 등

* 공통 form 필드:

  | 필드              | 의미                   | 비고       |
  | --------------- | -------------------- | -------- |
  | `business_date` | YYYY-MM-DD           | 필수       |
  | `property_code` | 예: MOP               | 기본 MOP   |
  | `dry_run`       | 0/1                  | 기본 1     |
  | `split_by_date` | 0/1                  | 옵션       |
  | `source_kind`   | daily/weekly/monthly | 기본 daily |
  | `file`          | CSV (multipart)      | 필수       |

* **프런트 검증 포인트**

  1. 필수 필드 누락 시 업로드 버튼 비활성화
  2. `dry_run=1` 호출로 미리보기 제공 (rows/preview)
  3. `dry_run=0` 성공 시 `batch_id`, `result`(inserted/upserted/noop) 표출
  4. 실패 시 `detail` 메시지 그대로 토스트/모달 출력 (서버표준 에러 키: `detail`)

* **중복 업로드**

  * 동일 파일 재업로드 시 결과(idempotent) 유지
  * 스냅샷 정책은 어댑터/엔진 정책에 따름(Phase 2에서 `missing_policy` 확장)

---

## 6) DB/마이그레이션 주의사항 (SQLite)

* **DROP/ALTER 최소화**: SQLite 제약상 `batch_alter_table` 시 임시 테이블 생성으로 부작용 발생 가능
  → “NOT NULL 제약” 추가 시 **DEFAULT** 또는 데이터 백필(UPDATE) 절차 선행.
* **운영 전 백업 필수**

  ```bash
  sqlite3 /path/hotel.db ".backup '/path/hotel_pre_fix_$(date +%F).db'"
  alembic upgrade head
  ```
* **롤백**

  ```bash
  # 실패 시
  mv /path/hotel_pre_fix_*.db /path/hotel.db
  ```
* **FK 명 없는 drop_constraint 금지**

  * Alembic가 생성한 `drop_constraint(None, type_='foreignkey')` 구문은 **에러 유발**
    → 반드시 주석 처리 또는 명시적 이름 사용
* **테이블 구조(현행) 핵심**

  * `merge_batches(id, dataset, property_code, business_date, file_name, record_count, dry_run, status, mode, missing_policy, source_kind, session_id, version_no, created_at, completed_at, notes)`
  * `merge_changelog(id, batch_id, dataset, property_code, business_date, key_hash, record_hash, action, payload, created_at)`
  * `rooms_status_canon(id, key_hash, record_hash, valid_on, payload_json, last_batch_id, updated_at)`
  * `rooms_status_history(id, key_hash, record_hash, valid_on, payload_json, source_batch_id, created_at)`

> Alembic 자동 생성 후, **SQLite에 부적합한 DROP/ALTER/constraint 조작**은 반드시 수동 편집으로 제거/치환.

---

## 7) Backend 엔드포인트·흐름 상호 참조

* `routers/upload.py` → `services/merge_service.py` → `merge_engine/engine.py`

  * 엔진: `normalize → parse → (dry_run? preview : repository.persist)`
  * repository: `MergeAuditRepository.create_batch → CanonRepository.upsert_record → finalize_batch`
* 공통 로그 라인 (uvicorn.log):

  * 시작: `[MERGE_SERVICE] start dataset=... dry_run=... bytes=...`
  * 엔진 완료: `[MERGE_ENGINE] Applied dataset=..., rows=..., upserted=...`
  * 서비스 완료: `[MERGE_SERVICE] done ok=... dry_run=... rows=...`

---

## 8) QA 체크리스트

* [ ] `/api/upload/rooms_status` dry_run=1 호출 시 200 + preview 응답
* [ ] dry_run=0 호출 시 200 + `batch_id` + `result`(inserted/upserted/noop) 출력
* [ ] `rooms_status_canon`, `rooms_status_history`에 레코드 반영 확인
* [ ] `merge_batches.status = DONE` 및 `record_count`/`notes` 갱신 확인
* [ ] 동일 파일 재업로드 시 NOOP 집계 증가(또는 결과 불변) 확인
* [ ] 에러 케이스: 어댑터 normalize/parse 실패 시 `detail` 에러 반환 확인
* [ ] Alembic upgrade head 수행 시 무중단/무손실 보장 (사전 백업)

---

## 9) 배포/운영 정보

* 개발 서버 : `http://192.168.0.6:8001`
* 운영 서버 : `http://127.0.0.1:8000`
* 로그 : `/volume1/web/hotel-system/logs/uvicorn.log`
* 업로드 캐시/테스트: `/volume1/web/hotel-system/backend/_uploads/`

**파일 보관 규칙**

```
/_volume1/web/hotel-system/backend/_uploads/
 ├─ rooms_status/MOP/2025-09-23/...
 ├─ sales_front/MOP/2025-09-23/...
 ├─ fnb_sales/MOP/2025-09-23/...
 ├─ bank_ledger/MOP/2025-09-23/...
 └─ expenses/MOP/2025-09-23/...
```

* 파일명 패턴: `{dataset}_{property_code}_{YYYY-MM-DD}_{seq}.csv`

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

## 11) 부록 — 프런트 샘플 호출

```bash
# 드라이런
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-10-07 \
  -F property_code=MOP \
  -F dry_run=1 \
  -F "file=@backend/_uploads/rooms_status_MOP_2025-10-07_1.csv;type=text/csv" \
  http://127.0.0.1:8000/api/upload/rooms_status | jq .

# 실행
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-10-07 \
  -F property_code=MOP \
  -F dry_run=0 \
  -F "file=@backend/_uploads/rooms_status_MOP_2025-10-07_1.csv;type=text/csv" \
  http://127.0.0.1:8000/api/upload/rooms_status | jq .
```

---

### 결론

본 문서는 **백엔드 구조의 SSOT** 입니다.
개발/배포/QA 전 과정에서 본 문서와 실제 트리의 일치가 보장되도록 주기적으로 스냅샷과 diff를 수행하고, 변경이 생기면 **즉시 갱신**합니다.
