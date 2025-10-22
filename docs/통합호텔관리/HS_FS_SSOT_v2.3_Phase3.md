# Hotel System FullStack SSOT v2.3 (Phase 3 — 2025‑10‑12)

> **문서 목적 (SSOT)**  
> 본 문서는 호텔 시스템의 **권한/로그인, 업로드·병합 엔진, 프런트 연동 규격**을 포괄하는 단일 진실 원본(Single Source of Truth)입니다.  
> 기존 원안(Phase 1/2) 내용을 **생략 없이 유지**하고, 이번 **Phase 3에서 변경·추가된 사항**을 명확히 병기합니다.

---
## 버전 & 변경 이력

- **v2.3 (2025‑10‑12, Phase 3 업데이트)** — 본 문서
  - `core/settings_merge.py` 정식 도입 및 **앱 기동 시 로드**(main.py에서 초기화)
  - 업로드 엔진 확정: **파일 보관 없음**, **캐논/해시 기반 저장**(payload_json) 정책 확정
  - **FNB 어댑터 완성**: `fnb_items`, `fnb_tenders` 정상 작동 (스냅샷형)
  - `/api/upload/*` 흐름 고도화: form 값 보강, 숫자 컬럼 정규화, idempotent upsert
  - 감사/로그 일원화: `merge_batches`, `merge_changelog` 기준
  - 프런트 연동 스펙 재정의: **UploadBoard** 미리보기/실행 UX, 로그 조회, 실패 메시지 규격
- v2.2 (2025‑10‑12) — 권한/역할·HR 통합 밑그림 반영 (원문 유지)
- v2.1 (2025‑10‑11) — MergeEngine Phase 2 안정화 (rooms/sales/expenses/bank)
- v2.0 (2025‑10‑10) — 초기 SSOT 합본

> **주의**: Phase 3에서 **파일 시스템 저장을 하지 않음**(설계 변경). CSV 원본은 캐시/테스트 경로만 사용하며, 영속화는 **DB의 Canon 테이블(payload_json) + 해시(key_hash, record_hash)** 로 관리합니다.

---
# Part 0. Role & View Map (원문 유지, 일부 보강)

### 역할 계층 (Role Hierarchy)
| 역할             | 설명                                                     |
| ---------------- | ---------------------------------------------------------|
| **SUPERADMIN**   | 모든 기능 접근 가능 (시스템 관리·환경설정·감사 포함)     |
| **ADMIN**        | 일반 운영 기능 담당 (업로드, 마감, 리포트, 직원 관리 등) |
| **USER**         | 기본 조회 전용 사용자                                    |
| **HK**           | 하우스키핑 — 객실 청소 및 점검 담당                      |
| **FNB**          | 식음 — 레스토랑/바 매출 및 정산                          |
| **FRONT**        | 프런트오피스 — 체크인/체크아웃 및 예약 담당              |
| **ENG**          | 시설관리 — 설비 점검·보수 기록 관리                      |
| **SUPPORT**      | 경영지원 — 회계, 급여, 인사 보조                         |
| **AUDITOR**      | 감사 — 전사 데이터 및 로그 열람 권한                     |

### 접근 구조 (핵심 화면)
| 모듈        | 경로              | 권한                 | 비고                                  |
| ------------| ----------------- | -------------------- | ------------------------------------- |
| 대시보드    | `/dashboard`      | ALL                  | KPI · 현황 · 링크 허브                |
| 일마감      | `/admin/closing`  | ADMIN↑               | 캘린더 + 일자별 작업                  |
| 업로드      | `/admin/upload`   | ADMIN↑               | Dataset별 파일 업로드                 |
| 하우스키핑  | `/hk`             | HK↑                  | 객실 상태·청소 현황                   |
| 시설관리    | `/eng`            | ENG↑                 | 설비 점검·수리 이력                   |
| FNB 매출    | `/fnb`            | FNB↑                 | 매장 매출·정산 관리                   |
| 리포트      | `/reports`        | ADMIN↑               | 매출·지출·정산 통계                   |
| 사용자 관리 | `/admin/users`    | SUPERADMIN           | 계정·역할 관리                        |
| HR 관리     | `/admin/hr`       | ADMIN↑               | 직원·계약·인사기록 통합 관리          |
| 권한 관리   | `/admin/roles`    | SUPERADMIN           | 역할별 접근 설정 (RoleAccess 화면)    |
| 키워드      | `/admin/keywords` | ADMIN↑               | 영업분석 태그 관리                    |
| OTA         | `/ota`            | ADMIN↑               | 채널·커미션 설정                      |
| 설정        | `/settings`       | SUPERADMIN           | 시스템 환경·변수 정의                 |
| 로그        | `/audit`          | SUPERADMIN · AUDITOR | 변경이력 및 감사 로그                 |
| 공지/문서   | `/docs-admin`     | ADMIN↑               | 공지 · 서식 · 문서 관리               |
| 로그인      | `/login`          | public               | 내부 토큰 발급                        |
| 404         | `*`               | public               | NotFound 화면                         |

**보강**  
- `/api/users/roles/access/effective` : Role→ViewMap 동적 매핑 반환. Router `meta.roles`와 동기화.
- 로그인/권한은 `X-Internal-Token` 기반. **개발 토큰**: `dev-admin-token`.

---
# Part I. Backend SSOT (원문 + Phase 3 반영)

```
backend/app/
├─ core/
│  ├─ auth.py                # 내부토큰 검증, require_roles, require_token_local
│  ├─ audit.py               # 변경이력 로깅, 요청 메타 저장
│  ├─ dev_bootstrap.py       # 개발환경 초기 데이터 삽입(roles, superadmin 계정)
│  ├─ employees_import.py    # CSV/XLS 임포트 (사원명부)
│  ├─ hashing.py             # 패스워드 해싱/검증 (bcrypt)
│  ├─ i18n.py                # 다국어 메시지 헬퍼
│  ├─ keywords.py            # 영업분석 키워드 헬퍼
│  ├─ locale.py              # 로케일 자동 감지 및 적용
│  ├─ me_router.py           # /api/me 엔드포인트 (토큰 기반 유저 정보)
│  ├─ normalize_bank.py      # 은행 입금내역 정규화
│  ├─ normalize.py           # 공통 데이터 정규화 유틸
│  ├─ payments.py            # 결제관련 헬퍼
│  ├─ settings_merge.py      # 🆕 병합 엔진 전역 설정/정책/로깅 (Phase 3)
│  ├─ settings.py            # 환경변수 로더 (.env)
│  ├─ snapshot.py            # SSOT 스냅샷 저장
│  └─ __init__.py
│
├─ datasets/
│  ├─ adapters/
│  │  ├─ bank_ledger.py      # 은행거래 데이터셋 (append 기본)
│  │  ├─ base.py             # 공통 어댑터 클래스
│  │  ├─ expenses.py         # 지출내역 데이터셋 (snapshot)
│  │  ├─ fnb_items.py        # 🆕 FNB 품목 데이터셋 (snapshot, 작동 확인)
│  │  ├─ fnb_tenders.py      # 🆕 FNB 결제수단 데이터셋 (snapshot, 작동 확인)
│  │  ├─ rooms_status.py     # 객실상태 데이터셋 (append 기본)
│  │  ├─ sales_front.py      # 프런트 매출 데이터셋 (snapshot)
│  │  └─ __init__.py         # ADAPTERS 레지스트리
│  └─ schemas/
│     ├─ bank_ledger.py
│     ├─ expenses.py
│     ├─ fnb_items.py
│     ├─ fnb_tenders.py
│     ├─ rooms_status.py
│     ├─ sales_front.py
│     └─ __init__.py
│
├─ merge_engine/
│  ├─ audit.py               # 병합결과 로그
│  ├─ diff.py                # 변경점 계산기
│  ├─ engine.py              # normalize → parse → (dry_run? preview : persist)
│  ├─ planner.py             # DryRun 계획/요약
│  ├─ policies.py            # 누락/중복 정책
│  ├─ repository.py          # Canon/History CRUD, merge_batches/changelog
│  └─ __init__.py            # get_adapter()
│
├─ models/                   # (원문: model/ 로 표기된 곳은 실제 디렉터리명 models/ 사용)
│  ├─ audit.py               # merge_batches, merge_changelog
│  ├─ bank.py
│  ├─ base.py                # Declarative Base
│  ├─ board.py
│  ├─ canon.py               # rooms/fnb 등 Canon/History
│  ├─ closing.py
│  ├─ employee.py
│  ├─ mixins.py
│  ├─ ota.py
│  ├─ role.py
│  ├─ user.py
│  └─ __init__.py
│
├─ routers/
│  ├─ audit.py               # /api/audit
│  ├─ closing.py
│  ├─ debug.py
│  ├─ employees.py
│  ├─ keywords.py
│  ├─ menu.py
│  ├─ merge.py               # /api/merge/batches, /api/merge/logs/{id}
│  ├─ ota.py
│  ├─ reports.py
│  ├─ reports_bank.py
│  ├─ reports_sales.py
│  ├─ upload.py              # /api/upload/{dataset}
│  ├─ users.py
│  └─ health.py
│
├─ schemas/
│  ├─ merge.py
│  ├─ closing.py
│  ├─ board.py
│  ├─ reports.py
│  ├─ users.py
│  ├─ auth.py
│  └─ __init__.py
│
├─ services/
│  ├─ merge_service.py       # router → engine bridge
│  ├─ upload_service.py      # 업로드 form 정규화/분기
│  └─ __init__.py
│
└─ main.py                   # FastAPI 진입점 (settings_merge 초기화 포함)
```

### Phase 3 핵심 변경점 (백엔드)

1) **settings_merge** (신규)  
   - 전역 기본값 (예: `merge_mode=snapshot`, `missing_policy=soft_delete`, `audit_enabled=True` 등) + 데이터셋별 오버라이드  
   - 파일 로거 경로: `/volume1/web/hotel-system/logs/merge_engine.log`  
   - **앱 기동 시 초기화**: `app/main.py` 에서 `from app.core import settings_merge; settings_merge.setup_merge_logger(); settings_merge.show_policies()`

2) **저장 방식 확정: 파일 미보관 → Canon(payload_json) 저장**  
   - 업로드된 CSV는 **파일시스템에 영속 저장하지 않음** (설계 수정).  
   - 각 레코드는 Canon 테이블에 **payload_json + key_hash + record_hash** 로 저장.  
   - 예: `fnb_items_canon` 스키마
     ```sql
     CREATE TABLE fnb_items_canon (
       id INTEGER PRIMARY KEY,
       key_hash VARCHAR(64) NOT NULL UNIQUE,
       record_hash VARCHAR(64) NOT NULL,
       valid_on DATE NOT NULL,
       payload_json TEXT NOT NULL,
       last_batch_id INTEGER REFERENCES merge_batches(id) ON DELETE SET NULL,
       updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
     );
     ```
   - **key 선택**: 어댑터 정의에 따라 `(business_date, property_code, item_code)` 등으로 key_hash 생성.  
   - **idempotent upsert**: 같은 key_hash면 update, 아니면 insert. 변경 없음은 noop.

3) **FNB 어댑터 완성**  
   - `datasets/adapters/fnb_items.py` (snapshot): 컬럼 정규화, 숫자 쉼표 제거, form 값 보강, Pydantic v2 스키마 검증.  
   - `datasets/adapters/fnb_tenders.py` (snapshot): 결제수단 기준 스냅샷 병합.  
   - 엔진 로그에서 **정책/모드가 2회 출력**될 수 있으나 기능상 문제 없음(uvicorn reload 두 프로세스 로그).

4) **업로드 엔드포인트 고도화**  
   - `POST /api/upload/{dataset}` (multipart/form-data)  
   - 필드: `business_date`, `property_code`, `dry_run(0/1)`, `mode(optional)`, `source_kind(optional)`, `file(csv)`  
   - **dry_run=1**: 미리보기 요약, **dry_run=0**: DB 반영 + `batch_id` 반환  
   - **정규화 규칙**: 헤더 누락 시 form 값 보강, 금액 쉼표 제거, 공백/개행/인코딩 관용

5) **감사/로그 표준화**  
   - `merge_batches` / `merge_changelog` 테이블로 실행 이력 관리  
   - `/api/merge/logs/{batch_id}` 응답은 **ISO8601 문자열**로 시간 반환 (Pydantic v2 호환)

---
## Part I‑A. 업로드·병합 엔진 스펙 (데이터셋별)

| 항목          | rooms_status          | sales_front           | expenses              | fnb_items              | fnb_tenders           | bank_ledger           |
|--------------|-----------------------|-----------------------|-----------------------|------------------------|-----------------------|----------------------|
| 기본 모드     | append                 | snapshot              | snapshot              | snapshot               | snapshot              | append               |
| 키 필드      | date, prop, room_no    | date, prop, tag       | date, prop, account   | date, prop, item_code  | date, prop, tender    | date, prop, txn_id*  |
| 변경 판단     | hash(payload)          | amount                | amount+note           | category+qty+amount    | amount                | acct+dir+amount+memo |
| 누락 정책     | soft_delete            | soft_delete           | soft_delete           | soft_delete            | soft_delete           | ignore               |
| 비고          | split_by_date=1→snapshot | -                   | -                     | 숫자 쉼표 제거, form 보강 | -                   | txn_id 없으면 라인키 |

**응답 스키마**  
- Dry-run: `MergeDryRunResp { ok, dataset, property_code, business_date, summary{inserted,updated,deleted,noop}, details{...} }`  
- Execute:  `MergeExecResp   { ok, batch_id, dataset, property_code, business_date, summary{...}, completed_at }`

**샘플 cURL**  
```bash
# fnb_items 실행 반영
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F property_code=MOP \
  -F business_date=2025-10-12 \
  -F dry_run=0 \
  -F "file=@backend/_uploads/fnb_items_test.csv;type=text/csv" \
  http://192.168.0.6:8001/api/upload/fnb_items | jq .

# 실행 결과 확인
curl -s -H "X-Internal-Token: dev-admin-token" \
  http://192.168.0.6:8001/api/merge/logs/{$batch_id} | jq .
```

**DB 확인 예시**  
```sql
-- Canon 행 확인 (payload_json 기반)
SELECT id, key_hash, substr(payload_json,1,120) AS payload
FROM fnb_items_canon
ORDER BY id DESC
LIMIT 5;
```

---
# Part II. Frontend Integration SSOT (원문 + Phase 3 보강)

```
frontend/admin/src/
├─ router/
│   ├─ index.ts
│   └─ menu.ts                 # Role→ViewMap 동기화
├─ services/
│   ├─ http.ts                 # fetch 래퍼 (Axios 금지)
│   ├─ upload.ts               # /api/upload/* 호출 (폼 전송)
│   ├─ reports.ts / bank.ts …  # 기타 API
├─ stores/
│   ├─ auth.ts                 # X-Internal-Token 보관
│   └─ menu.ts / kpi.ts        # 메뉴/지표 상태
└─ views/
    ├─ Admin/UploadBoard.vue   # 업로드 UX (미리보기→실행)
    ├─ Reports/*               # 리포트 화면
    ├─ Admin/RoleAccess.vue    # 권한 맵
    └─ Admin/HR/*              # HR 통합 모듈 (원문 유지)
```

### UploadBoard.vue (권장 UX)

1) CSV 선택 → `dry_run=1` 호출 → 표/요약 표시(삽입/갱신/삭제/무변경)  
2) 확인 후 “실행” → `dry_run=0` 호출 → `batch_id` 링크 표시  
3) 배치 상세 패널: `/api/merge/logs/{batch_id}` 응답을 표로 렌더  
4) 장애 시 `res.json().detail` 그대로 노출 + “로그 다운로드” 버튼(선택)

**서비스 코드 예시**
```ts
export async function upload(
  dataset: string,
  file: File,
  opts: {
    business_date: string;
    property_code?: string;
    dry_run?: 0 | 1;
    mode?: 'append' | 'snapshot';
    source_kind?: 'daily' | 'weekly' | 'monthly';
  }
) {
  const form = new FormData();
  form.append("business_date", opts.business_date);
  form.append("property_code", opts.property_code ?? "MOP");
  form.append("dry_run", String(opts.dry_run ?? 1));
  if (opts.mode) form.append("mode", opts.mode);
  form.append("source_kind", opts.source_kind ?? "daily");
  form.append("file", file, file.name);

  const res = await fetch(`/api/upload/${dataset}`, {
    method: "POST",
    headers: { "X-Internal-Token": localStorage.getItem("ADMIN_TOKEN") ?? "dev-admin-token" },
    body: form,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Upload failed");
  return data;
}
```

---
# Part III. 운영/QA 체크리스트 (보강)

- [ ] `/api/upload/*` 각 데이터셋 `dry_run=1` → 200 + summary OK  
- [ ] `dry_run=0` → 200 + `batch_id` OK, `merge_batches.status=DONE`  
- [ ] `/api/merge/logs/{batch_id}` → 변경내역 정상 (ISO8601 문자열)  
- [ ] 동일 파일 재업로드 → `noop` 증가 또는 불변 (idempotent)  
- [ ] CSV 헤더 일부 미제공 시 폼 값 보강 확인  
- [ ] 금액 필드 쉼표 제거/공백 처리 확인  
- [ ] 오류 행 메시지 `Invalid row: ...` 가독성 확인  
- [ ] Synology NAS 권한: `_uploads` 테스트 디렉터리 접근 가능(캐시 용도)  
- [ ] `.env` 환경: `APP_DB_URL`, `INTERNAL_API_TOKEN`, `ADMIN_TOKEN` 준비

---
# Part IV. 트러블슈팅 (현장 기록 반영)

- **업로드 후 DB에 반영 안 보임**  
  - `dry_run` 강제 보정 확인(`services/merge_service.py`), `dry_run=0`로 실행했는지 확인  
  - `merge_engine/repository.py`의 `commit()` 정상 호출 여부 확인  
  - `get_adapter(dataset)`이 FNB용 어댑터 반환하는지 로그 확인

- **fnb_items 컬럼 질의 오류 (no such column: business_date)**  
  - Canon 스키마는 컬럼형이 아닌 **payload_json** 저장 방식. JSON 내부에서 조회 필요  
  - 예: `substr(payload_json,1,120)`로 내용 샘플 확인

- **엔진 정책 로그가 2회 찍힘**  
  - uvicorn reload 구조상 초기화가 2번 호출될 수 있음(정상)

- **권한/토큰 오류**  
  - 개발 환경: `X-Internal-Token: dev-admin-token` 헤더 필수  
  - 운영 환경: 실제 토큰 발급/검증 로직 적용

---
# Part V. API 맵 (요약)

| API                        | 화면/목적         | 인증  | 파라미터                    |
|--------------------------- |------------------ |------ |---------------------------- |
| `/api/me`                  | 로그인 상태       | Token | -                           |
| `/api/menu`                | 메뉴 동기화       | Token | roles[]                     |
| `/api/upload/{dataset}`    | 업로드/병합       | Token | file, business_date, dry_run|
| `/api/merge/batches`       | 배치 목록         | Token | filter, page                |
| `/api/merge/logs/{id}`     | 배치 상세 로그    | Token | -                           |
| `/api/reports/*`           | 리포트 조회       | Token | 기간/필터                   |
| `/api/users/*`             | 사용자/권한       | Token | -                           |

---
# Part VI. 결론

- **파일 미보관·해시 기반 Canon 저장**으로 설계를 단순화하고, 재업로드 시 idempotent 보장.  
- Phase 3에서 **FNB 어댑터 완성 + settings_merge 전역화 + 프런트 UploadBoard UX**까지 기준 확정.  
- 본 문서를 **SSOT**로 유지하며, 코드/DB/화면 변경 시 즉시 갱신합니다.
