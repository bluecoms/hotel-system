# 📄 BE-Core 스펙 정의 초안 — Phase 3 (2025-10)

## 0) 범위 요약
- OTA: 커미션 CRUD 확장 + 시드 데이터
- Reports: sales-tags 집계 로직 구현
- 메뉴/권한: Role 기반 제어 강화

---

## 1) OTA 모듈 확장

### API 스펙
- `POST /api/ota/commissions`  
  - 입력: `{ channel_id, rate, type, effective_date }`  
  - 검증: `rate ∈ [0,1]`, `effective_date` 중복 정책 TBD  
  - 출력: 생성된 commission

- `PUT /api/ota/commissions/{id}`  
  - 입력: `{ rate?, type?, effective_date? }`  
  - 출력: 갱신된 commission

### DB / Alembic
- **ota_commissions** 테이블 확장:  
  - `rate` (float, 0~1)  
  - `type` (str, nullable=False, default="BASE")  
  - `effective_date` (date)  
- Alembic revision: `phase3_ota_commissions_extend`  
- 마이그레이션 시 기존 데이터 보존 + `type="BASE"` 기본값 주입

### 샘플 시드
- OTA 채널 1개 (Booking.com)  
- 커미션 2개 (2025-09-01: 12%, 2025-10-01: 10%)

---

## 2) Reports 모듈 고도화

### API 스펙
- `GET /api/reports/sales-tags`  
- 입력: `date_from`, `date_to` (YYYY-MM-DD)  
- 출력 예시:
  ```json
  [
    { "tag": "ROOM_ONLY", "sales_amount": 1234000, "count": 52 },
    { "tag": "BREAKFAST", "sales_amount": 456000, "count": 20 }
  ]
  ```
- 구현: 업로드 데이터 집계 기반 (sales_front + fac_sales)

---

## 3) 메뉴/권한 강화
- OTA/Reports 메뉴 항목 → `roles=["ADMIN"]`  
- navigation.py에서 권한 제약 반영  
- QA는 비ADMIN 계정으로 접근 차단 검증 예정

---

## 4) DoR
- 커미션 API 스펙/SQL 정의 확정  
- Alembic revision 설계안 리뷰  
- sales-tags 집계 로직 아키텍처 초안

---

## 5) DoD
- Alembic `upgrade head` 성공  
- `POST/PUT /api/ota/commissions` curl PASS  
- `GET /api/reports/sales-tags` 기간 지정 집계 정상 동작  
- 메뉴/권한 제약 FE/QA 검증 통과  

---

## 📌 한 줄 요약
```
BE-Core Phase 3 초안: OTA commissions CRUD+시드, Reports/sales-tags 집계, 메뉴 roles=ADMIN — DoR=스펙+SQL+revision 설계, DoD=alembic head+curl PASS
```
