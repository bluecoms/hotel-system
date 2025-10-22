# 📢 [PM-Hub] Phase 4 — 중간 결과/정책 합의 요청 (업로드·Export·회귀) — 2025-10-02

## 1) 요약
- **BE 수정 반영 후 전체 스모크 재검증 = PASS**
- 업로드 1차 성공(본문 `null`) / 동일 파일 재업로드 409 정책 정상
- Export CSV 헤더 `tag,count,amount` 확인
- `closing/calendar` 는 **항상 `"items"` 키 보장**
- QA 판정 규칙(스크립트) **완화 기준** 반영 필요 → 아래 합의 요청

---

## 2) 상세 결과

### 업로드 (POST `/api/upload/sales_front`)
- 1차 업로드: **200 OK, 본문 `null`** → 성공 처리로 보임 ✅  
- 2차 업로드(동일 파일): **409 CONFLICT** → 중복 정책 정상 ✅  
- **dry_run=1**: 정상/오류 케이스 모두 **200 OK**, 응답 스키마 기대대로 동작 ✅

### CSV Export (GET `/api/reports/sales-tags/export`)
- **Status**: 200 OK  
- **Content-Type**: `text/csv`  
- **첫 줄 헤더**: `tag,count,amount` → **정상** ✅

### Reports/sales-tags JSON (GET `/api/reports/sales-tags`)
- 파라미터 없음: **200 & `[]`** ✅  
- 기간 지정: **200 & array** ✅

### closing/calendar
- **`has("items") == true`** (빈 달에도 `"items"` 키 보장) ✅

### 페이징 완화 (channels)
- 현재 서버 **페이징 미적용** → **200 & type==array** 확인만 **PASS** ✅

### 감사로그(audit)
- 업로드 관련 로그 조회: **200 & array** ✅

---

## 3) DB 상태 (참고)
- `(business_date, tag)` 유니크 충돌 유발 데이터는 **삭제 완료**  
- 서로 교차된 다른 페어(예: `2025-10-01/BREAKFAST`, `2025-10-02/ROOM_ONLY`)는 **존치**  
  → 현 CSV와 **충돌 없음**, 유니크 제약과 **무관**

---

## 4) QA 판정 규칙 업데이트(합의 요청)
아래 기준으로 **QA 스모크 판정 로직**을 완화/명문화합니다.

- **UP_OK (실제 업로드 성공):**  
  아래 중 **하나라도** 만족하면 PASS  
  1) HTTP **200/201** (본문이 `null`이어도 허용)  
  2) 응답 JSON에 **`inserted >= 1`**

- **REUPLOAD_OK (중복 업로드):**  
  같은 파일 재업로드 시 **HTTP 409** → PASS

- **EXPORT_OK (CSV Export):**  
  GET 기준 **200**, `Content-Type`에 **`text/csv`** 포함, 파일 1행 헤더가 **`tag,count,amount`**

> ※ 선택 개선안(권장): 업로드 **성공 시 응답 통일**  
> 성공 응답을 `{"inserted": N, "errors": []}` 형태로 표준화하면 FE/QA 판정이 더 명확해집니다.

---

## 5) 회귀·정책 체크 (지속 유지)
- `/api/openapi.json` → **200**
- `/api/me` → **무토큰 401 / 토큰 200**
- `/api/closing/calendar` → **항상 `"items"` 키 존재**
- Reports/sales-tags → **빈=200[] / 정상=200 array**
- RBAC(ADMIN=200 / USER=403) → **PASS**

---

## 6) 증빙 경로
```
/docs/runbooks/phase4/2025-10-02_QA/
 ├─ evidence/
 │   ├─ json/  (upload_dry_ok.json, upload_real.json, rst_empty.json, rst_ok.json, audit_upload.json, ch.json, …)
 │   ├─ curl/  (각 응답 헤더 .hdr)
 │   └─ files/ (sales_front_ok.csv, sales_front_err.csv, sales_tags_2025-10-02.csv, export_headers.txt)
 └─ reports/
     └─ Phase4_Smoke.md
```

---

## 7) 결론 / 요청 사항
- **결론:** BE 수정 반영 후 **Phase 4 스모크 PASS**  
- **합의 요청:** 위 **QA 판정 규칙 업데이트**를 공식 기준으로 채택해 주세요.  
- **다음 단계:**  
  - BE: 업로드 성공 응답 포맷 표준화(선택) 검토  
  - QA/FE: 표준화 여부에 맞춰 판정/핸들러 반영  
  - 지속 회귀: Export/업로드/Reports/closing/RBAC 주기 점검

---

### PM-Hub용 한 줄 요약(복붙)
```
QA: Phase 4 Smoke PASS — 업로드(200/null 허용, 재업로드 409), Export CSV 헤더 tag,count,amount, closing/items 보장. 
QA 판정 규칙 완화(200/201 또는 inserted>=1, 재업로드=409 PASS) 적용 제안. 
증빙: /docs/runbooks/phase4/2025-10-02_QA/
```
