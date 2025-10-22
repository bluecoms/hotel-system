# Hotel System 백엔드 구조 & FE 연동 플레이북 (2025-10-11)

> 본 파일은 **`structure_backend_2025-10-11.md` SSOT의 FE 실무 가이드 확장판**입니다.  
> 프런트 개발자가 즉시 개발/검증/운영 배포까지 할 수 있도록 **계약, 에러, 예시, 검증 체크**를 모두 담았습니다.

---

## 0. 요약 (무엇을 어떻게 쓰나?)

- 업로드 API 하나로 모든 데이터셋을 처리: `POST /api/upload/{dataset}`
- 현재 **가동 데이터셋**: `rooms_status` (Phase 1).  
  추후: `sales_front`, `fnb_sales`, `expenses`, `bank_ledger` (Phase 2+)
- 워크플로우: `dry_run=1`로 미리보기 → 사용자 확인 → `dry_run=0`으로 확정 반영.
- 성공 시 **배치 기록**(`merge_batches`)과 **변경 이력**(`rooms_status_history`)이 남음.

---

## 1. 요청 계약 (모든 dataset 공통)

### 1.1 Multipart Form

| 필드            | 타입       | 설명                                     | 기본값 |
|----------------|------------|------------------------------------------|--------|
| business_date  | string     | `YYYY-MM-DD`                             | (없음) |
| property_code  | string     | 호텔 코드 (예: `MOP`)                     | MOP    |
| dry_run        | string/int | `1`=미리보기, `0`=실행                    | 1      |
| split_by_date  | string/int | `1`=여러 날짜가 파일에 있어도 일자별 처리 | 0/1    |
| source_kind    | string     | `daily|weekly|monthly`                    | daily  |
| file           | file       | CSV(MIME `text/csv`)                      | (필수) |

### 1.2 URL

```
POST /api/upload/{dataset}
- dataset ∈ { rooms_status, sales_front, fnb_sales, expenses, bank_ledger }
```

---

## 2. 응답 계약

### 2.1 Dry-run (`dry_run=1`)

```json
{
  "ok": true,
  "dry_run": true,
  "dataset": "rooms_status",
  "mode": "append",
  "counts": { "rows": 3 },
  "preview": [
    {
      "key_tuple": ["2025-10-11", "MOP", "101"],
      "key_hash": "hex...",
      "record_hash": "hex...",
      "payload": { "...": "정규화된 컬럼들" }
    }
  ]
}
```

### 2.2 Execute (`dry_run=0`)

```json
{
  "ok": true,
  "dry_run": false,
  "dataset": "rooms_status",
  "mode": "append",
  "batch_id": 2,
  "result": { "inserted": 0, "upserted": 0, "noop": 3 }
}
```

### 2.3 오류 공통

HTTP 400/500 예시:

```json
{ "detail": "merge-engine error: parse error: <원인>" }
```

> FE 표준: `detail` 키 그대로 사용자 알림 (토스트/다이얼로그).

---

## 3. 화면 UX 가이드

1. **업로드 폼**: 필수값 검증(날짜/호텔코드/파일). 미기입 시 버튼 비활성화.
2. **미리보기 단계**: `dry_run=1` 호출 → 결과의 `counts.rows` 표시, 3건 이하 샘플 표 렌더.
3. **확정 업로드**: 사용자 확인 후 `dry_run=0` 호출 → `batch_id`/`result` 표시.
4. **결과 페이지**: `noop`이면 “이미 반영됨” 안내, `upserted/inserted` 수치 강조.

---

## 4. 프런트 엔드 유틸 (의사코드)

```ts
async function uploadDataset(dataset, form) {
  const fd = new FormData();
  for (const [k, v] of Object.entries(form)) fd.append(k, v);
  const res = await fetch(`/api/upload/${dataset}`, { method: "POST", body: fd, headers: { "X-Internal-Token": token } });
  const json = await res.json();
  if (!res.ok || json.ok === false) throw new Error(json.detail || "Upload failed");
  return json;
}
```

- 1차 호출(dry_run=1) → 2차 호출(dry_run=0) 시 **동일한 business_date/property_code** 유지.
- 실패 시 `json.detail`을 사용자에게 그대로 출력.

---

## 5. 파일명/보관 규칙

- `{dataset}_{property_code}_{YYYY-MM-DD}_{seq}.csv`
- 경로: `/volume1/web/hotel-system/backend/_uploads/{dataset}/{property_code}/{YYYY-MM-DD}/...`

FE는 파일명까지 고정할 필요는 없지만, **운영 편의를 위해 위 패턴**을 권고합니다.

---

## 6. 운영/검증 체크리스트 (FE 관점)

- [ ] Dry-run 200 OK / preview 노출.
- [ ] Execute 200 OK / `batch_id` + `result` 노출.
- [ ] 동일 파일 재업로드 시 결과 불변(또는 `noop` 증가) 확인.
- [ ] 실패 케이스에서 `detail`이 사용자에게 명확히 전달되는지 확인.

---

## 7. 백엔드 상호 참조 (리마인드)

- `routers/upload.py` → `services/merge_service.py` → `merge_engine/engine.py` → `merge_engine/repository.py`
- 로그 키워드:
  - `[MERGE_SERVICE] start ...`
  - `[MERGE_ENGINE] Applied dataset=...`
  - `[MERGE_SERVICE] done ok=...`

---

## 8. 데이터셋별 참고 (Rooms Status)

- 현재는 `rooms_status`만 가동. 스키마 핵심 필드: `business_date`, `property_code`, `room_no`, `hk_note`, `is_dirty` 등.
- 키 구성: `(business_date, property_code, room_no)` → `key_hash`
- 레코드 비교: `payload_json` 정렬 JSON 해시 → `record_hash`

---

## 9. 에러 시나리오 & 대응

| 상황 | 서버 메세지 예 | FE 처리 |
|-----|---------------|---------|
| CSV 파싱 실패 | `parse error: ...` | 업로드 취소 + 상세 안내 |
| 날짜 누락 | `normalize error: ...` 또는 400 | 폼 검증 강화 |
| MergeBatch 생성 실패 | `persist error: ...` | 재시도 버튼 |
| DB 제약(필수 키 NULL) | `(sqlite3.IntegrityError) NOT NULL ...` | 필드 매핑 검증 |

---

## 10. 보안/권한

- 내부 토큰 헤더: `X-Internal-Token: dev-admin-token` (운영에서는 다른 키)
- CORS/쿠키 정책은 기존 백엔드 설정 준수.

---

## 11. 향후 확장(Phase 2/3)

- 스냅샷 모드(`mode=snapshot`)에서 **누락 정책**(`missing_policy=ignore|soft_delete|hard_delete`).
- `/api/merge/batches`, `/api/merge/logs` 조회 라우터 공개.
- `sales_front`, `fnb_sales` 업로드 지원 어댑터 추가.

---

## 12. 부록: 실전 cURL

```bash
# Dry-run
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-10-11 -F property_code=MOP -F dry_run=1 \
  -F "file=@backend/_uploads/rooms_status_MOP_2025-10-11_1.csv;type=text/csv" \
  http://127.0.0.1:8000/api/upload/rooms_status | jq .

# Execute
curl -s -H "X-Internal-Token: dev-admin-token" \
  -F business_date=2025-10-11 -F property_code=MOP -F dry_run=0 \
  -F "file=@backend/_uploads/rooms_status_MOP_2025-10-11_1.csv;type=text/csv" \
  http://127.0.0.1:8000/api/upload/rooms_status | jq .
```
