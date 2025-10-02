# QA 스펙 정의 — Phase 3
작성일: 2025-10-01

---

## 0) 요약
- 범위: OTA 커미션 CRUD 확장, Reports/sales-tags 집계, 메뉴/권한 제어
- DoR: 커미션 CRUD·sales-tags 집계 케이스 정의
- DoD: 모든 테스트 케이스 PASS (Phase1·Phase2 회귀 포함)

---

## 1) OTA 모듈 테스트
### 1-1) 커미션 CRUD
- [ ] 생성 → 200, ID 반환
- [ ] 조회 → 생성 값과 일치
- [ ] 수정 → 변경 내용 반영
- [ ] 수정 후 조회 → 최신 값 확인
- [ ] 중복 effective_date 생성 → 400/409 에러 기대

### 1-2) 유효성 검증
- [ ] rate 범위 0.0~1.0 벗어나면 400
- [ ] effective_date 중복 시 400/409

---

## 2) Reports 모듈 테스트
### 2-1) /api/reports/sales-tags
- [ ] 정상 요청(date_from/to 지정) → 200 + 합산 값 검증
- [ ] 파라미터 누락 → 빈 배열
- [ ] 데이터 없음 → 빈 배열
- [ ] 대량 기간(>1년) → 200, 성능/응답시간 기록

---

## 3) 메뉴/권한 테스트
- [ ] /api/menu 응답에 Reports/OTA 항목 roles=ADMIN
- [ ] FE에서 ADMIN 사용자 → 메뉴/페이지 표시
- [ ] FE에서 비ADMIN 사용자 → 메뉴 미표시 or 접근 차단
- [ ] 비ADMIN이 직접 URL 접근 시 → 403

---

## 4) 회귀 유지
- [ ] /api/openapi.json → 200
- [ ] /api/me (무토큰) → 401
- [ ] /api/me (토큰) → 200
- [ ] /api/closing/calendar → items 키 존재
- [ ] OTA 채널 CRUD/중복 케이스
- [ ] Reports/sales-tags 누락 케이스

---

## 5) 증빙 수집
- curl 명령어 + JSON 응답 저장
- 헤더/코드 로그 저장
- FE 스크린샷 저장 (메뉴/권한)
- 저장 경로:  
  `/docs/runbooks/phase3/{DATE}_QA/`

---

## 6) 결론 템플릿
```markdown
# Phase 3 QA 결론 ({DATE})
- OTA 커미션 CRUD: ☐ Pass / ☐ Fail
- Reports/sales-tags 집계: ☐ Pass / ☐ Fail
- 메뉴/권한: ☐ Pass / ☐ Fail
- 회귀: ☐ Pass / ☐ Fail
- 종합: ☐ PASS / ☐ FAIL
```
