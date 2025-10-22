# 📢 [PM-Hub] Phase 4 패치 적용/검증 보고 (BE-Core)

## 1) 적용 사항

### 공통
- Accept-Language 처리: `app/core/locale.py:set_lang` → `request.state.lang`에 ko|en 저장
- 메시지 맵: `app/core/i18n.py` 추가 → 짧은 한국어/영문 키 제공
- 라우터 공통 의존성에 `Depends(set_lang)` 적용: /api/upload, /api/ota, /api/reports, /api/menu, /api/audit, /api/users
- 에러 포맷: 모든 오류 응답을 `{"detail":"…"}` 로 통일

대표 매핑:
- 400: CSV 필요/헤더 오류 → "CSV 파일이 필요합니다.", "CSV 헤더가 올바르지 않습니다."
- 409: 중복/기간 겹침 → "중복 데이터입니다."
- 422: 기간 역전/검증 실패 → "기간이 올바르지 않습니다.", "입력값이 올바르지 않습니다."
- 404: 대상 없음 → "대상이 없습니다."
- 403: 권한 없음 → "권한이 없습니다."

### 업로드 (/api/upload/sales_front)
- i18n 적용 및 응답 포맷 통일
- 성공 시 null 반환 (스펙 유지)
- 감사로그(meta)에 { "lang": ko|en, "dry_run": false } 기록

### OTA (/api/ota/*)
- 채널/커미션 라우트에 i18n 적용
- 기간 역전 → 422, 중복 → 409, 대상 없음 → 404
- 감사로그(meta)에 lang 포함

### Reports Export (/api/reports/sales-tags/export)
- 파일명 영문 고정: `sales-tags_YYYYMMDD-YYYYMMDD.csv`
- Content-Type: text/csv; charset=utf-8
- Content-Disposition: attachment; filename="..."
- 날짜 검증 및 역전 → 422
- GET만 허용 (HEAD → 405)

### 감사로그/메뉴/유저
- /api/audit/logs: meta_json 파싱해 meta로 반환
- /api/menu: ADMIN → OTA/Reports 항목 포함, USER → 제외
- /api/users: 스켈레톤 구현 (인증 보장 + 언어 컨텍스트 설정)

### DB 제약
- sales_front: (business_date, tag) UNIQUE (ux_sales_front_date_tag)

---

## 2) 검증 결과 (실측)

### Export 헤더/파일명
```
HTTP/1.1 200 OK
content-type: text/csv; charset=utf-8
content-disposition: attachment; filename="sales-tags_20251001-20251031.csv"
```

### Upload (중복 시나리오)
- 1차 업로드 → 200
- 2차 업로드 → 409
- 응답: {"detail":"중복 데이터입니다."}

### OTA (검증 케이스)
- 422 (기간 역전) → {"detail":"기간이 올바르지 않습니다."}
- 404 (대상 없음) → {"detail":"대상이 없습니다."}

### 메뉴/감사로그/유저
- /api/menu → ADMIN에만 OTA/Reports 항목 포함
- /api/audit/logs → meta 파싱 정상, lang 포함
- /api/users → {"items":[]} 반환

---

## 3) FE 연동 포인트
- 에러 처리: 항상 `detail` 문자열 사용
- 업로드: 409 시 “중복 업로드” 안내
- Export: 파일명 영문 고정 (rename 불필요)
- i18n: Accept-Language=ko-KR 시 한글 메시지 제공
- 권한: 403 시 “권한이 없습니다” 표출

---

## 4) 남은 과제
- 업로드 성공 응답을 {inserted, errors} 구조로 통일 (향후)
- Reports 금액 컬럼 네이밍 통일 (amount vs sales_amount)
- 감사로그(meta) 스키마 가이드 문서화

---

## 5) 증빙/산출물 경로
- docs/runbooks/phase4/<DATE>_QA/evidence/{json,curl,files}
- docs/runbooks/phase4/<DATE>_QA/reports/Phase4_Smoke.md
- docs/runbooks/phase4/<DATE>_BE/evidence/
