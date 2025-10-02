# 📄 FE-Core Handoff Report — Reports / Sales Tags (2025-10-02)

## 1) 페이지/파일
- 대상 파일: `src/views/Reports/SalesTags.vue` (제공한 수정본 적용)
- Vuetify `v-data-table` + 합계 카드 + 스낵바 포함

---

## 2) API 계약
- 엔드포인트: `GET /api/reports/sales-tags`
- 쿼리 파라미터
  - `date_from`: YYYY-MM-DD (선택)
  - `date_to`: YYYY-MM-DD (선택)
- 응답 (배열, 래핑 없음 기본)
  ```json
  [
    { "tag": "ROOM_ONLY", "sales_amount": 200000, "count": 2 },
    { "tag": "BREAKFAST", "sales_amount": 45000, "count": 1 }
  ]
  ```
- 주의: BE는 `sales_amount`로 내려줌 → FE는 `amount = x.amount ?? x.sales_amount` 로 흡수
- 파라미터 미지정 시: `200 + []` (빈 배열)

---

## 3) UI 동작 요약
- 기간 입력 후 **조회** 클릭 시 API 호출
- 날짜 역전 (`date_from > date_to`) → API 호출 안 함 + 스낵바: “기간이 역전되었습니다.”
- 로딩 시 `v-progress-linear` 표시
- 데이터 없으면 `v-alert`: “표시할 데이터가 없습니다 (빈 데이터 OK)”
- 합계 카드 & 테이블 하단에서 건수/금액 합계 표시
- 금액/건수는 한국어 숫자 포맷(3자리 콤마)

---

## 4) 에러 처리
- **400/422**: 서버 detail 사용, 없으면 “요청 값이 올바르지 않습니다.”
- **그 외**: “Sales Tags를 불러오지 못했습니다.”
- 에러 시: 테이블 = 빈 배열, 합계 = 0

---

## 5) 형식/타입
- Row 타입: `{ tag: string; count: number; amount: number }`
- 합계 타입: `{ count: number; amount: number }`
- 합계 계산: 클라이언트에서 `reduce` (정수 변환 + NaN 방어 포함)

---

## 6) 라우팅/프록시
- Vite 프록시: `/api` → BE (`:8000`)
- FE 요청 경로: `/reports/sales-tags` (http 모듈에서 `/api` 프리픽스 자동)
- 로컬 확인: Network 탭에서 `/api/reports/sales-tags?...` 호출 여부 검증

---

## 7) 스모크 테스트 방법
- **빈 파라미터**
  - 기대: `[]`, 화면은 “데이터 없음”, 합계=0
- **유효 기간**
  - BE 시드 있음 → 테이블에 태그/건수/금액 노출, 합계 일치
- **날짜 역전**
  - from=2025-10-31, to=2025-10-01 → 스낵바, 호출 없음(Network에 X)
- **회귀(필드명)**
  - BE가 `sales_amount`만 내려도 금액 표시/합계 정상

샘플 cURL:
```bash
curl -H "X-Internal-Token: $TOK"   "$BASE/api/reports/sales-tags?date_from=2025-10-01&date_to=2025-10-31"
```

---

## 결론
- FE-Core Reports/SalesTags 페이지는 **빈 배열, 정상 데이터, 에러 상황** 모두 처리 완료
- API 계약/프록시 경로/에러 처리/합계 계산 **DoD 충족**
- PM/QA는 이 핸드오프 문서를 기준으로 테스트/인수 가능
