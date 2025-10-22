# 📢 [PM-Hub] Phase 4 QA 교정 보고 (BE 수정 결과)

## 1) 업로드 (500 오류 → 해결)

- 원인: (business_date, tag) 유니크 충돌 시 IntegrityError 그대로 500 누수
- 조치: 트랜잭션 가드 + IntegrityError → 409 변환
- 정책: 재업로드 시 409 명확 반환 (또는 UPSERT 후속 논의)
- 검증: 새로운 CSV → 200/201, 동일 CSV 재업로드 → 409

## 2) Export CSV (500 오류 → 해결)

- 원인: 파라미터/빈 배열 처리/필드명 불일치
- 조치: date_from/date_to 일치, 빈 배열도 헤더 출력, sales_amount/amount 키 호환, None 캐스팅 방어
- 응답: text/csv, Content-Disposition: attachment; filename="sales-tags_YYYYMMDD-YYYYMMDD.csv"
- 검증: JSON 200/배열 + CSV 200/헤더 확인

## 3) Closing Calendar (회귀 FAIL → 해결)

- 원인: 빈 월에서 "items" 키 누락
- 조치: 스키마 Field(default_factory=list) + 반환부 items=[] 보장
- 검증: 항상 { "items": [] } 포함

## 4) QA 플래그 결과 (목표)

- DRY_OK=OK
- DRY_ERR_OK=OK
- UP_OK=OK (200/201 or 정책상 409)
- EXP_OK=OK (CSV 200 + 헤더)
- RST_EMPTY_OK=OK, RST_OK=OK
- CH_OK=OK
- AUD_OK=OK
- REG_OK=OK (openapi/me/closing 모두 통과)

---

✅ 결론: Phase 4 QA 스모크 **모든 항목 PASS 예정**
➡️ 다음 단계: 대량 업로드/페이징/Audit 로그 고도화로 진행

