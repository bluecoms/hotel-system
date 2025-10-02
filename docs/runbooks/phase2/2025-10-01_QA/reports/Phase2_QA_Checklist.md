# Phase 2 QA 체크리스트

## OTA 모듈
- [ ] 채널 생성 → 200 + ID 반환
- [ ] 채널 조회 → 필드 값 일치
- [ ] 채널 수정 → 응답 200 반영
- [ ] 채널 이력 조회 → 기록 확인
- [ ] 커미션 조회 → 200 + 값 검증
- [ ] 권한 없는 사용자 요청 → 403

## Reports 모듈 (/api/reports/sales-tags)
- [ ] 정상 요청(date_from/to) → 200
- [ ] 파라미터 누락 → 빈 배열
- [ ] 데이터 존재 시 태그별 합산 값 확인
- [ ] date_from > date_to → 에러 코드 확인
- [ ] 대량 요청(>1년) 성능 확인

## 메뉴/권한
- [ ] /api/menu 응답에 OTA/Reports 존재
- [ ] FE 사이드바 OTA/Reports 표시
- [ ] roles=ADMIN+만 노출
- [ ] 미개발 항목 WIP 라벨 표시

## 회귀
- [ ] /openapi.json → 200
- [ ] /api/me with token → 200
- [ ] /api/me without token → 401
- [ ] /api/closing/calendar → items 키 존재
