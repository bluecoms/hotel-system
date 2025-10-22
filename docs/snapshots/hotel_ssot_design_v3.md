# 🏨 호텔 SSOT 통합 설계안 v3 (은행·객실·예약·FNB·OTA 수수료·키워드·HK 자동화)

> 목표: **모든 원본을 수용(append-only) → 정규화 → 교차검증 → 일/주 스냅샷 → 실매출(Net)·운영지표 산출**  
> 범위: **객실매출(정산내역), 예약/룸상태, 은행 입·출금, FNB(부대업장) 매출(결제수단/상품)** + **OTA 수수료/결제수단 표준화/키워드 분류/조식집계/HK(하우스키핑) 자동 배정**

---

## 0. 핵심 원칙 (SSOT)
- **Append-only + Versioning**: 기존 레코드 불변, 최신 포인터는 `*_canon`, 전체 이력은 `*_history` 보관.
- **Merge 모드**: 일자료=append, 주/월 스냅샷=snapshot(+soft_delete)로 누락/중복 정리.
- **Cross-check**: 객실 매출(sales_front) ↔ 예약/룸상태(rooms_status) ↔ 은행(bank_txns) 정합 검증.
- **표준화 레이어**: 결제수단(`canon_pay_method`), OTA 수수료(`ota_commissions`), 키워드(`keywords`) 적용.
- **멀티 아키텍처**: **N개의 부대업장(Outlets)**, **N개의 은행계좌**를 1개 SSOT로 통합.

---

## 1. 데이터셋 요약 (업로드 5종 + FNB)
| Dataset | 업로드 엔드포인트 | 원본 예시 | 목적(요약) |
|---|---|---|---|
| **pay_settlement (입금)** | `/api/upload/pay_settlement` | `20250916입금.xls` | 은행 입금(IN) 적재 → 정산 검증·입금 매칭 |
| **expenses (출금)** | `/api/upload/expenses` | `20250916출금.xls` | 은행 출금(OUT) 적재 → 비용/지급 관리 |
| **sales_front (객실 정산내역)** | `/api/upload/sales_front` | `VCLOUD_정산내역_*.csv` | 객실 매출(일자·결제수단·채널별) 확정치 |
| **rooms_status (예약/룸상태)** | `/api/upload/rooms_status` | `예약내역_*.csv` | 객실별 예약/입퇴실/메모(키워드) |
| **fnb_tenders (부대업장-결제수단별)** | `/api/upload/fnb_tenders` | POS “결제수단별 매출” | 아웃렛별 결제수단 집계 |
| **fnb_items (부대업장-상품별)** | `/api/upload/fnb_items` | POS “상품별 매출현황” | 상품별 수량/실매출(재고/기획 활용) |

> **은행·FNB는 다수 개체(N개)**를 전제로 함: `account_code`, `outlet_code` 필수.

---

## 2. 컬럼 매핑 (실제 원본 기준)

### 2.1 은행 입/출금 (`app/core/normalize_bank.py` 사용)
- **허용 포맷**: `.xls/.xlsx/.csv/.html` 자동 판별 → CSV 변환
- **추출 필드(CANON_FIELDS)**  
  `date,time,direction,amount,balance,desc,counterparty,memo,raw_ref`
- **스크린샷 헤더 매핑 예**  
  - 거래일자 → `date` (YYYY-MM-DD 표준화)  
  - 입금금액(원)/출금금액(원) → `amount` + `direction(IN/OUT)` 결정  
  - 거래 후 잔액(원) → `balance`  
  - 거래내용/거래기록사항 → `desc` / `counterparty`  
  - 거래시간 → `time` ; 이체메모 → `memo` ; 번호 → `raw_ref`

### 2.2 객실 정산내역 (`sales_front`)
- **주요 컬럼 예**: `business_date, property_code, room_no, room_type, channel, pay_method, amount, memo`  
- **결제수단 표준화**: `canon_pay_method(name)` → `CASH|CARD|NAVER_PAY|KAKAO_PAY|...`  
- **키워드 태깅**: `keywords.py` 로 `tags` 파생 (예: `["RO","BF3","IN2","W"]`)  
- **교차키**: `(property_code, room_no, check_in, check_out)` or `reservation_id` 로 **rooms_status**와 매칭.

### 2.3 예약/룸상태 (`rooms_status` = “어제 예약내역 → 오늘 아침 HK”)
- **주요 컬럼(스크린샷 기준)**: `예약타입, 배정객실, 예약자, 예약번호, 입실일시, 퇴실일시, 예약자명, 메모, 결제금액, OTA예약, 객실타입, 특수기간, 예약일시, 연락처`  
- **핵심 파생**:  
  - `stay_type`: 숙박/재실 구분  
  - `needs_cleaning`: 퇴실(어제→오늘) 기준 HK 필요 여부  
  - `keywords`: 메모에서 패키지/인원(BF3, IN2 등) 추출 → 조식/부대시설 준비에 사용

### 2.4 FNB (부대업장 POS)
- **결제수단별집계 (fnb_tenders)**: `business_date, property_code, outlet_code, pay_method, amount`  
  - 스크린샷: “결제수단별 매출(현금/신용카드)” → `canon_pay_method`로 표준화
- **상품별집계 (fnb_items)**: `business_date, property_code, outlet_code, item_code, item_name, qty, net_sales`  
  - 스크린샷: “상품코드, 상품명, 수량, 실매출” → 그대로 매핑
- **다중 아웃렛**: `outlet_code`로 식별 (예: LOUNGE, RESTAURANT, POOLSIDE 등)

---

## 3. 키워드/메모 기반 분류 (`app/core/keywords.py`)
- **목표**: `sales_front`·`rooms_status`에서 **상품/패키지/조식/속성** 자동 판별.  
- **규칙 예**  
  - 매출 분류: `"패키"|"package" → package`, `"룸|숙박|room" → room_only`, 그 외 `other`  
  - 패키지 코드: `RO, BF(조식 N인: BF3 → 3인), IN, W/L/P/RS/Z/AL, POA/CL/VCC, C/O, Kos1`  
- **출력**: `{"rooms":{"room_only":..., "package":..., "other":...}, "front":{...}, "fb":{...}}`  
- **스냅샷**: `/api/reports/daily-summary` 에 저장/노출 (daily_snapshot).

---

## 4. OTA 수수료 반영 (Net Sales 산출)
- **구성**: `ota_channels(code,name)` + `ota_commissions(channel_id, valid_from, valid_to, rate)`  
- **계산**: `gross = amount` → `commission = gross * rate` → `net = gross - commission`  
- **적용 위치**: `sales_front`(채널/결제경로가 OTA인 경우), `fnb_tenders`(카드수수료 등 정책 선택 적용)  
- **기간 중복 방지**: `/api/ota/commissions` 는 유효기간 중복 체크(`_has_overlap`).  
- **리포트**: **채널별 Gross/Net**, **결제수단별 Net** 비교 제공.

> 카드 가맹점 수수료가 별도라면 `card_fee_rate`(글로벌/아웃렛별) 정책 테이블 추가 가능: `fin_fees(fee_type, target, valid_from, valid_to, rate)`.

---

## 5. HK(하우스키핑) 자동 배정 & 조식 집계
- **HK 대상 산출**: `rooms_status`에서 **퇴실 예정/완료** 건 → `needs_cleaning=true` 합계.  
- **조식 집계(매일 21:00)**: 메모 키워드 BFN(BF3 등) 합계를 **익일 인원수**로 계산 → `/api/reports/breakfast-plan?date=YYYY-MM-DD`.  
- **부대업장 알림**: 패키지 코드(W/L/P/RS/Z/AL) 포함 예약 건을 **부서별 큐**로 푸시(예: 수영장, 라운지, 키오스크).

---

## 6. 스키마 요약 (핵심 컬럼만)
### 6.1 공통
- 모든 테이블 공통: `id, property_code, business_date, version_no, session_id, created_at`
- 최신/이력: `<dataset>_canon` / `<dataset>_history`
- 감사: `merge_batches`, `merge_changelog`

### 6.2 은행 (`bank_txns`)
`property_code, account_code, business_date, txn_date, txn_time, direction(IN/OUT), amount, balance, desc, counterparty, memo, raw_ref, dataset(pay_settlement|expenses), session_id, version_no, created_at`

### 6.3 객실 정산 (`sales_front`)
`business_date, property_code, room_no, room_type, channel, pay_method, amount, memo, tags(JSON/text)`

### 6.4 예약/룸상태 (`rooms_status`)
`reservation_id, room_no, check_in, check_out, guest_name, channel, memo, stay_type, needs_cleaning(bool), keywords(JSON)`

### 6.5 FNB 결제수단 (`fnb_tenders`)
`business_date, property_code, outlet_code, pay_method, amount`

### 6.6 FNB 상품별 (`fnb_items`)
`business_date, property_code, outlet_code, item_code, item_name, qty, net_sales`

### 6.7 OTA
`ota_channels(code,name,status), ota_commissions(channel_id,valid_from,valid_to,rate,note), ota_orders(channel,order_code,guest_name,check_in,check_out,amount,status)`

---

## 7. API 요약
- **은행**: `/api/upload/pay_settlement`, `/api/upload/expenses`, `/api/bank/summary`
- **객실/예약**: `/api/upload/sales_front`, `/api/upload/rooms_status`
- **FNB**: `/api/upload/fnb_tenders`, `/api/upload/fnb_items`
- **OTA**: `/api/ota/channels`, `/api/ota/commissions`, `/api/ota/orders`
- **리포트**:  
  - `/api/reports/daily-summary?date&property_code` (매출 분류 스냅샷: rooms/front/fb + Net)  
  - `/api/reports/breakfast-plan?date&property_code` (익일 조식 인원)  
  - `/api/reports/hk-targets?date&property_code` (HK 청소 객실수)  
  - `/api/reports/ota-net?date_from&date_to&channel` (Gross/Net by OTA)

---

## 8. 머지/검증 시나리오
1) 업로드(dry_run) → **중복/변경/누락** 플랜 확인 → 확정.  
2) `sales_front ↔ rooms_status` 금액/예약 매칭(불일치 시 changelog 기록).  
3) `pay_settlement`(입금)과 OTA Net의 **정산 매칭**(가급적 금액/일자/채널 기준).  
4) FNB는 **outlet_code** 단위 집계 후 **카드/현금 수수료 정책** 선택 적용 → Net 산출.

---

## 9. 멀티 Outlets/Accounts 운영
- **은행 계좌 N개**: `account_code` 로 분리 저장/조회.  
- **부대업장 N개**: `outlet_code` 로 분리 업로드/조회.  
- 리포트는 `property_code` + 선택적 `account_code/outlet_code` 필터.

---

## 10. DoD (완료 기준)
- 동일 파일 2회 업로드: 1회차 insert, 2회차 dry_run=중복(변화 없음).  
- 키워드 분류 테스트: BF/IN/패키지/룸온리 샘플 20건 통과.  
- `daily-summary`에 Gross/Net·조식·HK 수 산출.  
- OTA 수수료 기간중복 방지 및 Net 계산 검증(샘플 10건).  
- 아웃렛/계좌 다중 업로드 후 합산 리포트 정상.

---

## 11. 운영/자동화
- 21:00 배치: **익일 조식 인원** 생성 및 부서 통보.  
- 06:10 배치: **전일 정산** 스냅샷 확정(은행/객실/FNB 교차검증).  
- Web: Raw 미리보기 + 업로드 이력(세션/버전) 확인 화면.

---

## 12. 참고 모듈
- `app/core/normalize_bank.py` — 은행 입출금 정규화
- `app/routers/bank.py` — 입금/출금 업로드 & 요약
- `app/core/payments.py` — 결제수단 표준화
- `app/core/keywords.py` — 메모/태그 키워드 분류·스냅샷
- `app/routers/ota.py` — 채널/수수료/주문 관리

---

### 한 줄 요약
> **여러 은행·부대업장·OTA·결제수단을 한 데 모아, 키워드/수수료를 반영한 “실매출+운영지표”를 매일 자동 생성하는 SSOT.**
