# Phase 4 QA 체크리스트（교정판）

## 업로드(sales_front)
- [ ] 드라이런 정상 CSV → 200, inserted=0, errors=[]
- [ ] 드라이런 오류 CSV → 200, inserted=0, errors>0(행번호/메시지)
- [ ] 실제 업로드 정상 → inserted=N
- [ ] 재업로드 중복 정책 기대값(스펙) 일치

## Export (sales-tags CSV)
- [ ] 기간 지정 → 200 & Content-Type:text/csv
- [ ] 파일명/헤더 검증

## Reports JSON
- [ ] date_from/to 없음 → 200 []
- [ ] date_from/to 지정 → 200 array

## 페이징（완화）
- [ ] /api/ota/channels → 200 & type=="array"  （서버 페이징 N/A）

## 감사로그
- [ ] 업로드 성공/실패 후 /api/audit/logs 기록 존재
- [ ] commissions 변경 로그 기록 존재
- [ ] 필터(action/target/date range) 동작

## 회귀
- [ ] /api/openapi.json=200
- [ ] /api/me 무토큰=401 / 토큰=200
- [ ] /api/closing/calendar → "items" 존재
- [ ] Reports/sales-tags 빈/정상 200
- [ ] RBAC(ADMIN=200 / USER=403)
