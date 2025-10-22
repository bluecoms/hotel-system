# 📊 Phase 5 — UI 통합 QA 보고서 (2025-10-04)

## 요약
- ✅ Pass: SalesTags API 분리값 확인, Closing JSON에 status 필드 존재
- ❗Needs FE 확인: Closing 색상/팝업, SalesTags 값 대시보드 반영(화면 캡처 필요)
- ❌ Fail: KPI 배지 필드 누락(backend 응답 필드 확인 필요), OTA API 파싱 실패, HK 스켈레톤 API 필드 누락, 삭제된 경로 리디렉션 미동작

---

## 1) KPI 배지 (Upload N/6)
- **요청:** `GET /api/reports/dashboard-kpi`
- **기대:** 응답 JSON에 업로드 카운트 필드(예: `sales_front_count`) 포함 → 배지 N/6 계산 근거
- **결과:** **FAIL** — `sales_front_count` 키 미검출
- **증빙:** `./docs/runbooks/phase5/2025-10-04_QA/evidence/json/kpi.json`, 헤더 `.../curl/kpi.hdr`
- **메모:** BE 응답 스키마 확인 필요(필드명/네임스페이스)

## 2) SalesTags (룸온리/패키지 분리)
- **요청:** `GET /api/reports/sales-tags?date_from=2025-10-01&date_to=2025-10-04`
- **결과(API):** **PASS** — 추출 예시
  ```json
  { "tag": "ROOM_ONLY", "amount": 210000 }
  { "tag": "BREAKFAST", "amount": 80000 }
  { "tag": "ROOM", "amount": 30000 }
  ```
- **대시보드 반영(화면):** **PENDING** — 화면 합계/분리 반영 스냅샷 요구
- **증빙:** `.../json/sales_tags.json`, 추출 `.../reports/sales_tags_extract.txt`

## 3) Closing 캘린더
- **요청:** `GET /api/closing/calendar?month=2025-10`
- **결과(JSON):** **PASS** — `status` 필드 존재 확인
- **색상/팝업:** **PENDING** — UI 확인 필요 (“업로드로 가기” 동작 캡처)
- **증빙:** `.../json/closing.json`, 헤더 `.../curl/closing.hdr`

## 4) OTA (Ota.vue: Sales/Aliases/Fees, Net 계산)
- **요청:** `GET /api/ota/commissions`
- **결과:** **FAIL(파싱 오류)** — `jq: Cannot index object with number`
  - 원인 추정: 응답 루트 스키마가 배열이 아닌 객체/페이지네이션 형식 또는 숫자 단독 반환
  - 조치: 스키마 확인 후 파서 수정(`.[0]` → `.items[0]` 등) 또는 BE 응답 표준화
- **증빙:** `.../json/ota_sales.json`, 헤더 `.../curl/ota_sales.hdr`

## 5) HK 스켈레톤
- **요청:** `GET /api/hk/status`
- **결과:** **FAIL** — `rooms_total` 키 미검출(더미 0 허용 범위 내)
- **조치 제안:** 최소 스켈레톤 필드(`rooms_total`, `dirty_count`, `clean_count`) 보장
- **증빙:** `.../json/hk.json`, 헤더 `.../curl/hk.hdr`

## 6) 삭제된 경로 리디렉션
- **요청:** `HEAD /admin/old-upload`
- **결과:** **FAIL** — 리디렉션 또는 타겟 문자열 미검출
- **조치 제안:** FE 라우터에 리다이렉트 규칙 또는 서버 리라이트 규칙 적용 → Ota.vue/Board.vue

---

## 결론
- **최종 판정:** **PARTIAL FAIL**  
- BE/FE 조치 후 재검증 필요 항목:
  1) KPI 배지 근거 필드 스키마 확정(예: `sales_front_count` 등)  
  2) OTA 응답 스키마 및 파서 동기화(.items vs array)  
  3) HK 스켈레톤 최소 필드 보장  
  4) 삭제된 경로 리디렉션 규칙 적용  
  5) Closing 색상/팝업, SalesTags 대시보드 반영은 스크린샷 증빙

## 증빙 경로
```
./docs/runbooks/phase5/2025-10-04_QA/
 ├─ evidence/
 │   ├─ json/ (kpi.json, sales_tags.json, closing.json, ota_sales.json, hk.json)
 │   └─ curl/ (kpi.hdr, sales_tags.hdr, closing.hdr, ota_sales.hdr, hk.hdr)
 └─ reports/ (본 문서)
```
