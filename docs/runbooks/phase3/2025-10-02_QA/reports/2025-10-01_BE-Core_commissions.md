# 📢 [PM-Hub] Phase 3 BE-Core 진행 결과 보고

## 1) 처리 내용
- **POST /api/ota/commissions**  
  - 정상 생성 → `201 Created` 확인  
  - `rate` 입력 0~100%, 저장은 0~1. 응답은 % 단위 반환  
- **기간 겹침 제어**  
  - 겹치는 유효기간 요청 시 `409 Conflict` 정상 동작  
- **GET /api/ota/commissions**  
  - `channel/date_from/date_to` 필터 정상 적용, **배열([])** 반환 확인  
- **PUT /api/ota/commissions/{id}**  
  - 부분 수정 성공(`200 OK`) + 규칙 재검증 정상  
- **DB 제약 보완**  
  - `effective_date NOT NULL` 충족 위해 **valid_from 동기화** 규칙 확정  

## 2) 변경 원칙 (BE 확정)
- **READ**: projection 우선(JOIN + 명시 컬럼) → Out 매핑  
- **WRITE**: ORM 객체 + 호환 컬럼 동기화 (effective_date=valid_from)  
- **스키마 분리**: Create/Update vs Out  
- **rate 규칙**: 입력 % → 저장 0~1 → 응답 %  

## 3) QA DoD 체크
- OpenAPI에 POST/PUT 노출  
- POST 201 → % 단위 rate 반환  
- 기간 겹침 409  
- GET 교차 기간 필터 정상  
- PUT 후 규칙 재검증 통과  
- DB 저장 rate=0~1, effective_date 동기화  

## 4) 증빙
- **생성**: `evidence/comm_post_ok.json`  
- **겹침**: `evidence/comm_post_overlap.status`  
- **조회**: `evidence/comm_get_range.json`  
- **수정**: `evidence/comm_put_ok.json`  

경로:  
`docs/runbooks/phase3/2025-10-01_BE-Core/evidence/`

---

✅ 결과: BE-Core Phase 3 commissions CRUD 정상 동작, 규칙 확정.  
👉 다음 단계: Reports/sales-tags 집계 로직 구현.  
