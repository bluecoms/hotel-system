# 💰 은행 입출금 데이터셋 (Bank Ledger)

## 1. 개요
호텔의 **입금(수입)** 과 **출금(지출)** 내역을 은행 통장 파일(XLS/XLSX/CSV)로 업로드하여  
**정산 검증, 회계 이력, 잔액 추적**을 수행한다.  
업로드된 파일은 자동으로 정규화되어 `bank_txns` 테이블에 저장된다.

---

## 2. 파일 형태 (원본 예시)
- 파일명 예시  
  - `20250916입금.xls`  
  - `20250916출금.xls`

- 은행 웹사이트(농협 등)에서 내려받은 **입출금거래내역조회 결과표** 형식

| 거래일자 | 출금금액(원) | 입금금액(원) | 거래 후 잔액(원) | 거래내용 | 거래기록사항 | 거래점 | 거래시간 | 이체메모 |
|-----------|---------------|---------------|------------------|-----------|---------------|---------|-----------|-----------|

---

## 3. 정규화 로직
1. 파일은 `.xls`, `.xlsx`, `.csv`, `.html` 모두 지원  
   → `normalize_bank_csv()`가 자동 판별 후 CSV로 변환.
2. 컬럼명 자동 감지  
   - 날짜: `거래일자`, `일자`, `date`  
   - 금액: `출금금액`, `입금금액`, `WITHDRAW`, `DEPOSIT`  
   - 잔액: `거래 후 잔액`, `BALANCE`  
   - 거래내용/비고: `적요`, `내용`, `거래처`, `메모`, `이체메모` 등
3. 금액에 “₩, 원, 콤마” 등이 있어도 정규화 가능  
4. 합계·잔액·공백행(`합계`, `총계`, `이월`) 자동 스킵  
5. 결과 필드(`CANON_FIELDS`)  
   ```csv
   date,time,direction,amount,balance,desc,counterparty,memo,raw_ref
   ```

---

## 4. 업로드 엔드포인트

| 유형 | 엔드포인트 | direction | dataset | 설명 |
|------|-------------|------------|----------|------|
| **입금(수입)** | `/api/upload/pay_settlement` | IN | pay_settlement | 은행 입금 내역 업로드 |
| **출금(지출)** | `/api/upload/expenses` | OUT | expenses | 출금·지출 내역 업로드 |

- 공통적으로 `bank_txns` 테이블에 저장  
- 업로드 이력은 `UploadSession`, `UploadedFile` 로 관리  
- `dry_run=1`일 경우 DB 반영 없이 미리보기만 수행

---

## 5. 데이터 저장 스키마

### `bank_txns` (핵심)
| 필드 | 설명 |
|------|------|
| property_code | 호텔 코드 (예: MOP) |
| account_code | 계좌 식별자 |
| business_date | 업로드 기준일 |
| txn_date | 거래일자 |
| txn_time | 거래시간 |
| direction | IN(입금) / OUT(출금) |
| amount | 금액 |
| balance | 거래 후 잔액 |
| desc | 거래내용 |
| counterparty | 거래처 / 상대계좌 |
| memo | 메모 / 비고 |
| raw_ref | 거래번호 등 식별자 |
| dataset | pay_settlement / expenses |
| session_id | 업로드 세션 ID |
| version_no | 버전 |
| created_at | 생성시각 |

---

## 6. 요약
- 은행 통장 엑셀을 그대로 업로드 가능  
- 자동으로 입금/출금 구분 및 표준 필드 변환  
- `/api/upload/pay_settlement` 와 `/api/upload/expenses` 를 통해  
  `bank_txns` 테이블에 정규화 저장 후, `/api/bank/summary` 로 잔액 및 합계 조회 가능.
