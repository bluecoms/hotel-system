# 🏨 Hotel System 백엔드 구조 및 데이터 업로드 SSOT (2025-10-12 최신 반영판)

> **문서 목적 (SSOT)**
>
> 본 문서는 Hotel System 백엔드의 **최신 단일 진실 원본(Single Source of Truth)** 구조 및 데이터 업로드 엔진 사양을 정리한 것입니다.  
> 프런트엔드 개발자는 이 문서를 기반으로 업로드 화면 및 로그 뷰어를 개발해야 하며,  
> BE-Core/FE-Core/QA 팀 모두 **이 문서를 기준으로 일관성 있는 동작을 검증**합니다.

* 문서 버전: `2025-10-12 (Phase 2 → Phase 3 전환 준비)`
* 적용 범위: `backend/app` 하위 전체 — 엔진/어댑터/모델/라우터/서비스/DB infra 포함
* 유지 책임: **BE-Core** (DB 변경, merge_engine 업데이트 시 반드시 문서 갱신)

---

## ✅ 1) Canonical Tree (최신 백엔드 구조)

```
backend/app/
├─ core/
│  ├─ auth.py                  # 인증/권한 (X-Internal-Token 기반)
│  ├─ locale.py, i18n.py       # 다국어 처리
│  ├─ hashing.py               # 해시 유틸 (Canon key_hash/record_hash 생성)
│  ├─ settings.py              # 환경 설정 로더
│  ├─ settings_merge.py        # ⚙️ Phase 3: 병합 정책/모드 설정 예정
│  ├─ dev_bootstrap.py         # 초기 seed 등록, ADMIN/ROLE 세팅
│  ├─ audit.py                 # core-level 로깅 유틸 (merge_engine.audit과 연동)
│  ├─ normalize.py             # CSV 파서 공통화 (UTF-8, BOM, 개행 정규화)
│  ├─ normalize_bank.py        # 입금전용 정규화기
│  ├─ employees_import.py      # 인사 데이터 import 유틸
│  ├─ payments.py              # 결제 테스트용
│  ├─ me_router.py             # `/api/me` (사용자 self 정보)
│  ├─ keywords.py              # 키워드 관리
│  ├─ snapshot.py              # 구조/데이터 스냅샷 기록기
│  └─ __init__.py
│
├─ datasets/
│  ├─ adapters/                # CSV→Canon 변환기(Adapter)
│  │  ├─ base.py               # DatasetAdapter, CanonRecord
│  │  ├─ rooms_status.py       # 객실 상태 (append)
│  │  ├─ sales_front.py        # 객실 매출 (snapshot)
│  │  ├─ expenses.py           # 지출내역 (snapshot)
│  │  ├─ bank_ledger.py        # 입출금내역 (append)
│  │  ├─ fnb_items.py          # 식음료 품목 매출 (Phase 3)
│  │  ├─ fnb_tenders.py        # 식음료 결제수단별 매출 (Phase 3)
│  │  └─ __init__.py           # ADAPTERS registry export
│  └─ schemas/
│     ├─ rooms_status.py, sales_front.py, expenses.py, bank_ledger.py, fnb_*.py
│     └─ __init__.py
│
├─ merge_engine/
│  ├─ engine.py                # normalize → parse → merge/persist
│  ├─ repository.py            # Canon/History CRUD
│  ├─ policies.py              # 중복/누락 정책 정의
│  ├─ planner.py               # dry_run 계획 수립
│  ├─ diff.py                  # 변경 비교기
│  ├─ audit.py                 # 배치 로그 (merge_batches, merge_changelog)
│  └─ __init__.py              # ADAPTERS 재-export
│
├─ services/
│  ├─ merge_service.py         # router ↔ engine bridge
│  ├─ upload_service.py        # dataset별 분기
│  └─ __init__.py
│
├─ routers/
│  ├─ upload.py                # `/api/upload/{dataset}`
│  ├─ merge.py                 # `/api/merge/batches`, `/api/merge/logs/{id}`
│  ├─ closing.py, reports*.py, users.py 등 도메인 라우터
│  └─ __init__.py
│
├─ db/
│  ├─ base_class.py, session.py, base.py, __init__.py
│
├─ models/
│  ├─ audit.py, canon.py, user.py, role.py 등 도메인 모델
│
├─ schemas/
│  ├─ merge.py, closing.py, users.py 등 응답 스키마
│
└─ main.py                     # FastAPI App Entry
```

---

## ⚙️ 2) 데이터 업로드 핵심 개념

| 항목 | 설명 |
|------|------|
| **저장 방식** | 실제 CSV 파일은 NAS `_uploads/` 폴더에 저장하지 않습니다. 대신, 모든 업로드는 **해시 기반 Canon 저장소(DB)** 에만 기록됩니다. |
| **이유** | 동일한 데이터 재업로드 시에도 **idempotent** 하게 처리해야 하며, 파일 저장은 불필요한 중복과 용량 증가를 초래하기 때문입니다. |
| **해시 구조** | `key_hash`(비즈니스 키 기반), `record_hash`(내용 기반) 두 단계로 구분되어 중복 방지 및 변경 감지에 사용됩니다. |
| **파일 검증** | `normalize` 모듈이 UTF-8, BOM, 개행, 콤마 제거 등을 통일합니다. |
| **DB 반영 흐름** | `upload.py` → `merge_service.py` → `merge_engine.engine` → `repository.persist()` |

---

## 🧩 3) 데이터셋별 규격

| Dataset | 모드 | 키 필드 | 주요 컬럼 | 정책 | |
|----------|------|----------|------------|------|--|
| `rooms_status` | append | business_date, property_code, room_no | status_code, is_dirty, hk_note | 누락시 soft_delete |
| `sales_front` | snapshot | business_date, property_code, tag | tag, amount | 누락시 soft_delete |
| `expenses` | snapshot | business_date, property_code, account_code | amount, note | 누락시 soft_delete |
| `bank_ledger` | append | business_date, property_code, txn_id | account_no, direction, amount, memo | 누락시 ignore |
| `fnb_items` | snapshot | business_date, property_code, item_code | qty, amount | 누락시 soft_delete |
| `fnb_tenders` | snapshot | business_date, property_code, tender_code | qty, amount | 누락시 soft_delete |

> 모든 CSV는 `business_date`, `property_code`가 누락되면 Form 필드 값으로 자동 보강됩니다.

---

## 📡 4) 업로드 호출 규약

**엔드포인트:**  
`POST /api/upload/{dataset}`

**헤더:**  
`X-Internal-Token: dev-admin-token`

**폼 필드:**

| 필드 | 설명 | 필수 | 기본 |
|------|------|------|------|
| business_date | YYYY-MM-DD | ✅ | - |
| property_code | 호텔 코드 | ↔️ | MOP |
| dry_run | 1=미리보기, 0=실반영 | ↔️ | 1 |
| mode | append/snapshot 강제 | ❌ | - |
| source_kind | daily/weekly/monthly | ❌ | daily |
| file | CSV 업로드 파일 | ✅ | - |

**응답:**  
- `dry_run=1`: `{ok, dataset, summary, details}`  
- `dry_run=0`: `{ok, batch_id, summary, completed_at}`

**샘플 호출:**

```bash
curl -s -H "X-Internal-Token: dev-admin-token"   -F business_date=2025-10-12 -F property_code=MOP -F dry_run=1   -F "file=@backend/_uploads/fnb_items_test.csv;type=text/csv"   http://192.168.0.6:8001/api/upload/fnb_items | jq .
```

---

## 🧠 5) 해시 기반 Canon 구조

| 컬럼 | 설명 |
|-------|------|
| `id` | PK |
| `key_hash` | 비즈니스 키 기반 SHA256 (date+prop+primary fields) |
| `record_hash` | 전체 payload 해시 |
| `valid_on` | 유효 일자 |
| `payload_json` | 원본 데이터 (JSON 직렬화) |
| `last_batch_id` | 마지막 병합 배치 ID |
| `updated_at` | 최신 업데이트 시간 |

> 동일한 `key_hash` + `record_hash` 조합은 재업로드 시 무시(`noop`) 처리됩니다.

---

## 🧾 6) 로그 및 배치 조회

**엔드포인트**  
- `/api/merge/batches`: 배치 목록 (정렬/필터)
- `/api/merge/logs/{batch_id}`: 특정 배치 로그 조회

**응답 예시:**

```json
{
  "id": 12,
  "dataset": "fnb_items",
  "property_code": "MOP",
  "business_date": "2025-10-12",
  "record_count": 1,
  "status": "DONE",
  "changes": [
    {"action": "insert", "key_hash": "hash_sample_001", "record_hash": "rec_hash_001"}
  ]
}
```

---

## 🧩 7) 프런트 개발 가이드

1. **화면 구성**  
   - CSV 파일 선택 → `dry_run=1` 업로드 → 미리보기 테이블 표시  
   - “실행” 버튼 → `dry_run=0` 호출  
   - 성공 시 `batch_id` 링크 → 로그 상세 패널(`/api/merge/logs/{id}`) 표시

2. **UX 요소**
   - `inserted / updated / deleted / noop` 별 색상 구분  
   - summary 합계, 건수 표시  
   - 실패 시 `detail` 필드의 메시지 그대로 출력  

3. **보안**
   - 모든 요청은 `X-Internal-Token` 필수  
   - 토큰 미제공 시 401 리턴  

4. **호출 예시 (fetch):**
```ts
const res = await fetch(`/api/upload/sales_front`, {
  method: "POST",
  headers: { "X-Internal-Token": token },
  body: formData,
});
```

---

## 🧱 8) Phase 3 전환 목표

| 항목 | 설명 |
|------|------|
| settings_merge.py | 엔진 전역 정책 정의 |
| merge_engine.audit 확장 | 로그 요약/리포트 기능 |
| fnb_* 어댑터 완성 | F&B 품목/결제별 업로드 |
| error format 통일 | `merge-service-error:` 접두로 일원화 |
| 프런트 로그뷰 | `/api/merge/logs/{id}` 연동 화면 |

---

## ✅ 9) QA 체크리스트

* [x] `/api/upload/*` dry_run=1 → OK  
* [x] dry_run=0 → batch_id 포함 OK  
* [x] 동일 CSV 재업로드 시 noop 처리  
* [x] merge_batches.status= DONE  
* [x] /api/merge/logs/{id} → ISO8601 시간 확인  

---

## 📦 10) 결론

이 문서는 Hotel Admin **데이터 업로드 파이프라인의 단일 기준 문서**입니다.  
- 파일 저장 대신 Canon DB를 진실 원본으로 사용합니다.  
- 모든 데이터는 해시 기반으로 중복 방지 및 추적됩니다.  
- 프런트엔드는 `/api/upload/{dataset}` 및 `/api/merge/logs/{id}`만으로 완전한 업로드/로그 기능을 구현할 수 있습니다.  

---
**저장 위치:**  
`docs/runbooks/structure_backend_2025-10-12.md`
