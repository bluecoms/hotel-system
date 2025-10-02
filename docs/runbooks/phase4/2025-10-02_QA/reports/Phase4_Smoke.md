# Phase 4 QA Smoke — 2025-10-02 (완성본)

## 업로드(sales_front)
- [x] 드라이런 정상 CSV → inserted=0, errors=[]
- [x] 드라이런 오류 CSV → inserted=0, errors>0
- [ ] 실제 업로드 → inserted>=1

## Export(sales-tags CSV)
- [ ] 기간 지정 → 200 & text/csv & 헤더 캡처 저장

## Reports/sales-tags(JSON)
- [x] 빈 파라미터 → 200 []
- [x] 정상(date_from/to) → 200 array

## 페이징(channels) — 완화
- [x] 200 & type==array (서버 페이징 N/A)

## 감사로그
- [x] 업로드 관련 로그 조회 OK

## 회귀
- [ ] openapi/me/closing & 정책 경로 PASS

## 증빙
- JSON/헤더/파일: docs/runbooks/phase4/2025-10-02_QA/evidence/{json,curl,files}
