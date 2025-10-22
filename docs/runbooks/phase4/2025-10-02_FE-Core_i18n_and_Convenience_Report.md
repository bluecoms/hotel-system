# 📄 FE-Core — i18n & 편의기능 적용 보고 (2025-10-02)

## 1) i18n 도입
- 추가: `src/i18n/messages.ko.json`, `src/i18n/index.ts`
- 등록: `main.ts` 에 `app.use(i18n)`
- 효과: **기본 라벨/메시지 한국어화** 일괄 적용

---

## 2) 공통 유틸 / 컴포넌트
- `src/utils/format.ts` → **KRW 통화 / 날짜(YYYY-MM-DD)** 포맷 유틸
- `src/ui/components/StateBlock.vue` → **로딩 / 빈 / 에러** 상태 공통 처리 컴포넌트

---

## 3) 주요 화면 패치
### SalesTags.vue
- 기간 필터(오늘/이번 달/지난 달) + 역전 방지
- 합계 계산(건수/금액) + **CSV 내보내기(Export)**
- `StateBlock` 적용으로 로딩/빈/에러 표준화

### Commission.vue
- **CRUD 다이얼로그** + 검증(기간 역전/중복/범위 0~100)
- 프리체크: 동일 채널 기간 겹침 사전 차단
- 에러 토스트(detail 우선)

### OTAList.vue
- 채널 목록 READ
- `StateBlock` 적용 (빈/로딩/에러 공통 메시지)

---

## 4) http.ts 정리
- **fetch 기반 통합** (axios 미사용)
- 공통 헤더: `X-Internal-Token` (+ 옵션 `Accept-Language: ko-KR`)
- 에러 핸들링 **표준화** (status/detail 우선 노출)
- 제공: `get / post / put / delete / getBlob`

---

## 5) DoD 확인
- [x] UI 텍스트 한국어화 적용
- [x] SalesTags: 빠른 기간 칩 동작 / KRW 포맷 / Export 버튼
- [x] Commission: CRUD + 검증(역전/중복/범위)
- [x] StateBlock: SalesTags / Commission / OTAList 반영
- [x] HTTP 표준화(get/post/put/delete/getBlob)

---

## 6) 증빙(스크린샷 경로)
```
docs/runbooks/phase4/<DATE>_FE/screens/
  ├─ sales_tags_empty.png
  ├─ sales_tags_withdata.png
  ├─ commission_form_ko.png
  └─ 403_snackbar_ko.png
```
