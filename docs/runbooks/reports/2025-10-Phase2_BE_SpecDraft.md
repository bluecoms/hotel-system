# BE-Core 스펙 정의 초안 — Phase 2 (2025-10)

## 0) 범위 요약
- **OTA 모듈**: 채널/커미션 관리
- **Reports 모듈**: 매출 태그 집계 API
- **사이드바/메뉴**: OTA/Reports 라우트 반영 (roles: ADMIN)

**공통 전제**
- 인증: `X-Internal-Token` (DEV: `dev-admin-token`)
- 권한: ADMIN 이상
- 응답 포맷: `application/json`
- 시간/날짜: `UTC`, `YYYY-MM-DD` (date), `YYYY-MM-DDTHH:mm:ssZ`(datetime)

---

## 1) OTA 모듈

### 1.1 DB 스키마 (초안)
#### `ota_channels`
| 필드 | 타입 | 제약 |
|---|---|---|
| id | PK, int, autoincrement | |
| code | varchar(20) | **UNIQUE**, NOT NULL |
| name | varchar(100) | NOT NULL |
| created_at | datetime | default=now |

인덱스: `uq_ota_channel_code (code)`

#### `ota_commissions`
| 필드 | 타입 | 제약 |
|---|---|---|
| id | PK, int, autoincrement | |
| channel_id | FK → ota_channels.id | NOT NULL, ON DELETE CASCADE |
| rate | numeric(5,4) | 0.0000 ~ 1.0000, NOT NULL |
| effective_date | date | NOT NULL |
| created_at | datetime | default=now |

제약/인덱스:
- **유니크**: `(channel_id, effective_date)`
- 조회 최적화: `idx_commissions_channel_date (channel_id, effective_date desc)`

### 1.2 Alembic
- 단일 head 유지
- revision id: `phase2_ota_init`
- upgrade: 위 2개 테이블 생성 + 제약/인덱스 반영
- downgrade: 테이블 드롭
- (선택) seed: `ota_channels`에 기본 채널 0~N개 삽입 옵션

### 1.3 API 스펙

#### GET `/api/ota/channels`
- 권한: ADMIN+
- 응답:
```json
[
  { "id": 1, "code": "BKG", "name": "Booking.com", "created_at": "2025-10-01T00:00:00Z" }
]

POST /api/ota/channels

권한: ADMIN+

요청:

{ "code": "BKG", "name": "Booking.com" }


응답(201):

{ "id": 1, "code": "BKG", "name": "Booking.com", "created_at": "2025-10-01T00:00:00Z" }


오류:

400: code 중복, 형식 오류

401/403: 인증/권한 실패

GET /api/ota/channels/{id}/history

권한: ADMIN+

쿼리(옵션): date_from, date_to

응답:

{
  "channel_id": 1,
  "code": "BKG",
  "name": "Booking.com",
  "commissions": [
    { "effective_date": "2025-09-01", "rate": 0.1500, "created_at": "2025-09-01T12:00:00Z" }
  ]
}

GET /api/ota/commissions

권한: ADMIN+

쿼리(옵션): channel_id, date_from, date_to

응답:

[
  { "channel_id": 1, "effective_date": "2025-09-01", "rate": 0.1500 }
]


검증 규칙

rate: 0.0 ≤ rate ≤ 1.0

effective_date: 중복 불가(채널별 1일 1건)

2) Reports 모듈
2.1 API 스펙 — 매출 태그 집계
GET /api/reports/sales-tags

권한: ADMIN+

파라미터(필수):

date_from (YYYY-MM-DD)

date_to (YYYY-MM-DD)

응답:

[
  { "tag": "ROOM_ONLY", "sales_amount": 1234000, "count": 52 },
  { "tag": "BREAKFAST", "sales_amount": 456000, "count": 20 }
]

검증:

date_from ≤ date_to

범위 최대 1년 권장(쿼리 비용)

집계 정의(초안)

소스: 일자/전표 기준 매출 테이블(기존 스키마 기준)

tag 분류 규칙: 기존 정규화/키워드 테이블 기준(없으면 “UNCATEGORIZED”로 묶음)

금액 합계: sales_amount = sum(amount) (부가세 포함/제외 여부는 현행 준수)

3) 사이드바/메뉴 반영 (BE 인터페이스)

app/core/navigation.py (또는 현행 메뉴 소스)에 라우트 메타 제공

NAV = [
  # ...
  { "label": "OTA",      "to": "/ota",      "roles": ["ADMIN","SUPERADMIN"] },
  { "label": "Reports",  "to": "/reports",  "roles": ["ADMIN","SUPERADMIN"] },
]


FE는 이 메타를 읽어 메뉴를 구성(이미 권한 가드 존재)

4) DoR / DoD

DoR (Ready)

본 문서(API/DB 스펙) 리뷰/합의

키 포인트 합의:

rate 범위/정밀도, 유니크 제약

reports 집계 소스 테이블/조인 기준

응답 스키마 확정

DoD (Done)

Alembic upgrade head 성공 (phase2_ota_init)

모든 엔드포인트 curl 테스트 통과 (아래 예시)

/api/reports/sales-tags: 필수 파라미터 검증 + 정상 집계 결과 반환

권한 가드: ADMIN 이상 접근 가능, 무토큰 401

5) 검증 curl (예시)
TOK=dev-admin-token

# OTA 채널 조회
curl -s -H "X-Internal-Token: $TOK" \
  http://127.0.0.1:8000/api/ota/channels | jq .

# 신규 채널 추가
curl -s -X POST -H "X-Internal-Token: $TOK" -H "Content-Type: application/json" \
  -d '{"code":"BKG","name":"Booking.com"}' \
  http://127.0.0.1:8000/api/ota/channels | jq .

# 채널 커미션 이력
curl -s -H "X-Internal-Token: $TOK" \
  http://127.0.0.1:8000/api/ota/channels/1/history | jq .

# 커미션 전체 조회
curl -s -H "X-Internal-Token: $TOK" \
  "http://127.0.0.1:8000/api/ota/commissions?channel_id=1&date_from=2025-09-01&date_to=2025-09-30" | jq .

# 리포트 매출 태그 조회
curl -s -H "X-Internal-Token: $TOK" \
  "http://127.0.0.1:8000/api/reports/sales-tags?date_from=2025-09-01&date_to=2025-09-30" | jq .