# 📢 [PM-Hub] Reports/sales-tags 오류 원인 & 해결 보고

## 1) 문제 상황
- `/api/reports/sales-tags` 호출 시 항상 `[]` 응답 발생.  

**원인 분석:**  
- FastAPI/SQLAlchemy는 `hotel.db`(절대경로: `sqlite://///volume1/web/hotel-system/backend/hotel.db`)를 바라보고 있었음.  
- 초기 시드 데이터는 `app.db`에 잘못 삽입 → API 조회 시 데이터가 비어 있었음.  

---

## 2) 조치 내용
1. `hotel.db`에 직접 테이블 생성:
   ```sql
   CREATE TABLE IF NOT EXISTS sales_front (
     business_date TEXT,
     tag TEXT,
     amount INTEGER
   );
   ```
2. 기존 데이터 삭제 후 3건 삽입:
   - (2025-10-01, ROOM_ONLY, 120000)  
   - (2025-10-01, BREAKFAST, 45000)  
   - (2025-10-02, ROOM_ONLY, 80000)  
3. 확인: `sales_front count = 3` → 정상 반영.  

---

## 3) 최종 검증 결과
- **파라미터 없음**
  ```http
  GET /api/reports/sales-tags → 200 []
  ```
- **기간 지정**
  ```http
  GET /api/reports/sales-tags?date_from=2025-10-01&date_to=2025-10-31
  → 200 OK
  [
    {"tag":"ROOM_ONLY","sales_amount":200000,"count":2},
    {"tag":"BREAKFAST","sales_amount":45000,"count":1}
  ]
  ```
- 스펙 준수:  
  - 정렬: `sales_amount DESC`, tie 시 `tag ASC`  
  - 빈 데이터도 `200/[]` 반환  

---

✅ **결론:**  
- Reports/sales-tags API 정상화 완료.  
- **BE-Core Phase 3** 집계 구현 DoD 충족.  
- 다음 단계: FE/QA 연동 및 회귀 테스트 진행.  
