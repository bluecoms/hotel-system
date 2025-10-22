# 🏨 Hotel System 백엔드 구조 및 업로드 엔진 SSOT (2025-10-12 Phase 3 실행형)

> **문서 목적 (SSOT)**  
> 본 문서는 Hotel System 백엔드의 업로드 및 병합 엔진의 **최신 실행형 단일 진실 원본(Single Source of Truth)** 입니다.  
> 프런트엔드 개발자는 이 문서를 기준으로 화면 흐름, API 호출, 로그 조회 기능을 개발해야 합니다.  
> BE-Core / FE-Core / QA 모두 이 문서를 기반으로 테스트 및 배포 검증을 수행합니다.

* 문서 버전: `2025-10-12 Phase 3`
* 범위: `backend/app` 전체 구조 + 데이터 업로드 파이프라인
* 유지 책임: **BE-Core** (DB/엔진 변경 시 즉시 갱신)

---

## ✅ 1) Canonical 백엔드 구조 (최신 기준)

```
backend/app/
├─ core/
│  ├─ auth.py                  # 인증/권한(X-Internal-Token 기반)
│  ├─ hashing.py               # SHA256 기반 해시(key_hash, record_hash)
│  ├─ settings.py, settings_merge.py  # 전역 정책 및 merge 옵션
│  ├─ normalize.py, normalize_bank.py  # CSV 정규화(UTF-8, BOM, CRLF, 콤마제거)
│  ├─ audit.py, snapshot.py    # 로그/스냅샷 관리
│  ├─ dev_bootstrap.py         # 초기 seed(admin/roles)
│  ├─ me_router.py, keywords.py, payments.py
│  └─ __init__.py
│
├─ datasets/
│  ├─ adapters/
│  │  ├─ base.py               # DatasetAdapter, CanonRecord
│  │  ├─ rooms_status.py       # 객실상태 (append)
│  │  ├─ sales_front.py        # 객실매출 (snapshot)
│  │  ├─ expenses.py           # 지출내역 (snapshot)
│  │  ├─ bank_ledger.py        # 입출금내역 (append)
│  │  ├─ fnb_items.py          # 식음료 품목별 매출
│  │  ├─ fnb_tenders.py        # 식음료 결제수단별 매출
│  │  └─ __init__.py           # ADAPTERS registry
│  └─ schemas/
│     ├─ rooms_status.py ... fnb_tenders.py
│     └─ __init__.py
│
├─ merge_engine/
│  ├─ engine.py                # normalize → parse → merge/persist
│  ├─ repository.py            # Canon/History CRUD
│  ├─ planner.py, diff.py, policies.py, audit.py
│  └─ __init__.py
│
├─ services/
│  ├─ merge_service.py         # router ↔ engine 연결
│  ├─ upload_service.py        # dataset별 라우팅
│  └─ __init__.py
│
├─ routers/
│  ├─ upload.py                # /api/upload/{dataset}
│  ├─ merge.py                 # /api/merge/batches, /logs/{id}
│  └─ 기타 도메인 라우터
│
├─ db/
│  ├─ base_class.py, session.py
│
├─ models/
│  ├─ canon.py, audit.py, user.py ...
│
├─ schemas/
│  ├─ merge.py, closing.py, users.py ...
│
└─ main.py                     # FastAPI Entry
```

---

## ⚙️ 2) 데이터 저장 방식 (해시 기반 Canon 구조)

### ✅ 저장 설계
| 항목 | 설명 |
|------|------|
| **파일 저장 없음** | `_uploads/` 폴더는 임시 업로드 테스트용. 실제 데이터는 DB의 Canon 테이블에 저장됩니다. |
| **해시 구조** | `key_hash`(비즈니스 키), `record_hash`(레코드 전체 내용)를 SHA256으로 계산 |
| **중복 처리** | 동일 `key_hash` + `record_hash` → `noop` 처리 (변경 없음) |
| **이력 관리** | 변경 발생 시 새 record_hash 생성, 이전 해시는 `merge_changelog`에 기록 |
| **정합성 유지** | 모든 merge는 idempotent — 동일 CSV를 다시 올려도 결과 불변 |

---

## 🔄 3) 백엔드 처리 경로 (라우터 → 엔진)

```text
[업로드 흐름]
1️⃣ routers/upload.py
     └─ dataset 매핑 (예: fnb_items → FnbItemsAdapter)
2️⃣ services/upload_service.py
     └─ merge_service.merge_execute 호출
3️⃣ services/merge_service.py
     └─ merge_engine.engine.run_merge()
4️⃣ merge_engine/engine.py
     ├─ normalize(csv)
     ├─ parse(rows)
     ├─ if dry_run → planner.preview()
     └─ else → repository.persist()
5️⃣ merge_engine/repository.py
     ├─ upsert CanonRecord (by key_hash)
     ├─ record_hash 비교
     └─ merge_batches + merge_changelog 기록
```

---

## 🧭 4) 프런트 호출 시퀀스 (Upload → DryRun → Execute → Logs)

```text
사용자
 ↓
UploadBoard.vue
 ↓ (파일 선택 + 업로드)
/api/upload/{dataset}?dry_run=1
 ↓
미리보기 테이블 표시 (insert/update/delete/noop)
 ↓
“실행” 버튼 클릭 → dry_run=0
 ↓
/api/upload/{dataset}?dry_run=0
 ↓
서버 병합 후 batch_id 반환
 ↓
/api/merge/logs/{batch_id}
 ↓
로그 패널에 변경 내역 표시
```

---

## 📡 5) 업로드 API 규격

**엔드포인트:**  
`POST /api/upload/{dataset}` (multipart/form-data)

**헤더:**  
`X-Internal-Token: dev-admin-token`

| 필드 | 설명 | 필수 | 기본 |
|------|------|------|------|
| business_date | YYYY-MM-DD | ✅ | - |
| property_code | 호텔 코드 | ↔️ | MOP |
| dry_run | 1=미리보기, 0=실반영 | ↔️ | 1 |
| mode | append/snapshot 강제 | ❌ | - |
| source_kind | daily/weekly/monthly | ❌ | daily |
| file | CSV 파일 | ✅ | - |

**응답 예시 (dry_run):**
```json
{
  "ok": true,
  "dataset": "sales_front",
  "summary": { "inserted": 2, "updated": 0, "deleted": 0, "noop": 1 },
  "details": [
    {"line": 1, "status": "insert", "tag": "ROOM_ONLY", "amount": 150000}
  ]
}
```

**응답 예시 (execute):**
```json
{
  "ok": true,
  "batch_id": 14,
  "dataset": "sales_front",
  "completed_at": "2025-10-12T07:33:02.125Z"
}
```

---

## 🧠 6) FE 호출 코드 템플릿

```ts
// src/services/upload.ts
export async function uploadDataset(dataset, file, opts) {
  const form = new FormData();
  form.append("business_date", opts.business_date);
  form.append("property_code", opts.property_code ?? "MOP");
  form.append("dry_run", String(opts.dry_run ?? 1));
  form.append("source_kind", opts.source_kind ?? "daily");
  form.append("file", file, file.name);

  const res = await fetch(`/api/upload/${dataset}`, {
    method: "POST",
    headers: { "X-Internal-Token": "dev-admin-token" },
    body: form,
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Upload failed");
  return data;
}
```

---

## 💬 7) 에러 및 로그 처리 규칙

| 케이스 | 메시지 | 처리 방법 |
|--------|---------|-----------|
| 폼 누락 | `merge-service-error: missing-field` | 필드 강조 표시 |
| CSV 파싱 오류 | `Invalid row: ...` | 해당 행 하이라이트 |
| 중복 데이터 | `noop` | 회색 처리 |
| 병합 실패 | `merge-service-error: repository-fail` | 전체 실패 알림 |
| 검증 실패 | `ResponseValidationError` | 백엔드 로그 확인 (uvicorn.log) |

---

## 🧾 8) 로그 조회 API

**GET /api/merge/logs/{batch_id}**  
반환 예시:
```json
{
  "id": 14,
  "dataset": "fnb_items",
  "property_code": "MOP",
  "record_count": 1,
  "changes": [
    {"action": "insert", "key_hash": "hash_001", "record_hash": "rec_001"}
  ]
}
```

---

## 🧱 9) QA 검증 절차

```bash
# rooms_status dry_run 테스트
curl -s -H "X-Internal-Token: dev-admin-token"   -F business_date=2025-10-12 -F property_code=MOP -F dry_run=1   -F "file=@backend/_uploads/rooms_status_test.csv;type=text/csv"   http://192.168.0.6:8001/api/upload/rooms_status | jq .

# 병합 후 로그 확인
curl -s -H "X-Internal-Token: dev-admin-token"   http://192.168.0.6:8001/api/merge/logs/14 | jq .
```

---

## 🧩 10) 프런트 개발자가 반드시 알아야 할 포인트

| 항목 | 설명 |
|------|------|
| 저장소 | 파일 저장 안 함 → Canon DB만 진실 원본 |
| 결과 기준 | batch_id 기반 로그 조회 |
| dry_run | 실제 반영 전 검증 단계 (업로드 화면 미리보기용) |
| CSV 정규화 | UTF-8, BOM 제거, 콤마·공백 정리 |
| 데이터 일관성 | 동일 데이터 재업로드 시 noop |
| 에러 메시지 | merge-service-error prefix |
| 로그 뷰 | `/api/merge/logs/{id}` 로드 → 상세 내역 표시 |

---

## 📦 11) 결론

이 문서는 **백엔드 구조 + 업로드 파이프라인 + 프런트 연동 전용 사양의 완전판**입니다.  
프런트 개발자는 이 문서의 시퀀스(Upload → DryRun → Execute → Logs)를 그대로 구현하면 됩니다.  
DB 및 Canon 구조는 BE-Core 기준으로 관리하며,  
프런트는 오직 API 응답(`ok`, `summary`, `batch_id`, `logs`) 만 사용합니다.

**저장 경로:**  
`docs/runbooks/structure_backend_2025-10-12_phase3.md`
