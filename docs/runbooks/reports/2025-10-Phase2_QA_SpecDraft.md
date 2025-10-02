# QA 스펙 정의 — Phase 2
작성일: 2025-10-01

---

## 0) 요약
- 범위: OTA 모듈, Reports 모듈, 사이드바/메뉴
- DoR: 테스트 시나리오 초안 작성
- DoD: smoke + regression 케이스 추가 후 PASS

---

## 1) OTA 모듈 테스트
### 1-1) 채널 CRUD
- [ ] 채널 생성 → 응답 200, ID 반환
- [ ] 생성된 채널 조회 → 필드 값 검증
- [ ] 채널 수정 → 응답 200, 변경 내용 반영
- [ ] 채널 이력 조회 → 이전 버전 기록 존재 확인

### 1-2) 커미션 조회
- [ ] API 호출 응답 200
- [ ] 커미션 값/정책 필드 검증

---

## 2) Reports 모듈 테스트
### 2-1) /api/reports/sales-tags
- [ ] 정상 요청(date_from/to 지정) → 200
- [ ] 범위 파라미터 누락 → 빈 배열 반환
- [ ] 데이터 존재 시 태그별 합산 값 = DB 기준치와 일치

---

## 3) 사이드바/메뉴 테스트
- [ ] /api/menu 응답에 OTA/Reports 항목 존재
- [ ] FE 사이드바 렌더링 시 OTA/Reports 표시
- [ ] 미개발 항목은 WIP 라벨로 표시됨

---

## 4) 증빙 수집
- curl 명령어 + JSON 응답
- 스크린샷(사이드바/메뉴)
- 로그/상태코드

저장 경로:  
`/docs/runbooks/phase2/{DATE}_QA/`

---

## 5) 결론 요약 템플릿
```markdown
# Phase 2 QA 결론 ({{DATE}})
- OTA 모듈: ☐ Pass / ☐ Fail
- Reports 모듈: ☐ Pass / ☐ Fail
- 사이드바/메뉴: ☐ Pass / ☐ Fail
- 종합: ☐ PASS / ☐ FAIL
```
