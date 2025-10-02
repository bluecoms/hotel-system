#  FE-Core 전달 요약 — Phase 4 (2025-10-02)

## 1) 업로드 화면 (Sales Upload)
- **경로/파일**: `src/views/Upload/SalesFront.vue` (신규)  
- **라우트**: `/admin/upload/sales-front`  
  `meta: { requiresAuth: true, roles: ['ADMIN'] }`  

**기능**
- CSV 업로드 폼 + `dry_run` 토글
- `POST /api/upload/sales_front`
- 결과 요약: `received / inserted / errors.length`
- 실패행 테이블: `row, message`
- 드라이런 성공 시 `"적용"` 버튼 → `dry_run=0` 재전송 후 성공 토스트

**에러 처리**
- 400/422 → 서버 `detail` 우선
- 그 외 → “업로드에 실패했습니다.”

**다운스트림**
- `http.ts` 사용 (토큰/Debug-Role 자동 헤더)
- CSV 헤더: `business_date,tag,amount`

---

## 2) Reports Export (SalesTags.vue 확장)
- **대상**: `src/views/Reports/SalesTags.vue`  
- **버튼**: “Export CSV”  
- 호출: `GET /api/reports/sales-tags/export?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD`  
- `http.getBlob()` → 파일 저장  
- 파일명: `sales-tags_YYYYMMDD-YYYYMMDD.csv`  
- 에러 시: “내보내기에 실패했습니다.”  
- 날짜 역전 시: 스낵바 안내 후 요청 중단

---

## 3) 목록 페이징/성능
- **대상**: `src/views/OTA/Commission.vue`, `src/views/OTA/OTAList.vue`  
- 요청 파라미터: `limit`, `offset`  
- UI: Vuetify `v-data-table` 페이지네이션 (기본 10/페이지)  
- 로딩바/스낵바 유지  
- 삭제 버튼: BE 미구현 → 비활성(툴팁 안내)  
- **주의**: `http.delete` 사용 (`http.del` 아님)

---

## 4) 감사로그 뷰
- **경로/파일**: `src/views/Audit/Logs.vue` (신규)  
- **라우트**: `/admin/audit/logs`  
  `meta: { requiresAuth: true, roles: ['ADMIN','SUPERADMIN'] }`  
- API: `GET /api/audit/logs?limit=50&offset=0`  
- 컬럼: `ts, actor, action, target, meta_json`  
- 정렬: 최신(ts desc)  
- 에러 시: “로그를 불러올 수 없습니다.”

---

## 5) 라우팅/가드/메뉴
- 라우트 메타:  
  - `/admin/ota/*`, `/admin/reports/*`, `/admin/upload/*` → `roles: ['ADMIN']`  
  - `/admin/audit/*` → `roles: ['ADMIN','SUPERADMIN']`  
- 가드:  
  - 무토큰 → `/login`  
  - 권한 미충족 → `/403` or 스낵바 `"권한이 없습니다."`  
- 사이드바: `/api/menu` 응답 기반, roles 불일치 항목 숨김  
  - BE가 ADMIN 전용으로 OTA/Reports/Audit/Upload 제공

---

## 6) 검증 시나리오 (스크린샷 필수)
- **업로드**: 드라이런 성공, 적용 성공  
  - `docs/runbooks/phase4/<DATE>_FE/screens/upload_*.png`
- **Export**: CSV 다운로드 성공(파일명 규칙)  
  - `sales_tags_export.png`
- **페이징**: 페이지 이동 동작  
  - `commission_paging.png`
- **감사로그**: 최근 10건 표시  
  - `audit_logs_list.png`

---

## 7) 빠른 수동 테스트 (curl)
```bash
# 업로드(dry-run)
curl -s -H "X-Internal-Token: $TOK" \
  -F dry_run=1 -F file=@samples/sales_front.csv \
  "$BASE/api/upload/sales_front" | jq .

# 업로드(실행)
curl -s -H "X-Internal-Token: $TOK" \
  -F dry_run=0 -F file=@samples/sales_front.csv \
  "$BASE/api/upload/sales_front" | jq .

# Export CSV
curl -s -H "X-Internal-Token: $TOK" \
  "$BASE/api/reports/sales-tags/export?date_from=2025-10-01&date_to=2025-10-31" -o out.csv

# 감사로그
curl -s -H "X-Internal-Token: $TOK" \
  "$BASE/api/audit/logs?limit=10" | jq .
