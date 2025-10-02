# 🟩 Phase 2 — FE-Core 스펙 정의 (Spec Draft)

## 1) OTA 모듈 (프론트)
- **뷰 파일**
  - `src/views/OTA/OTAList.vue` (목록/CRUD 스켈레톤)
  - `src/views/OTA/Commission.vue` (커미션 테이블 스켈레톤)
- **라우트**
  - `/admin/ota/*` 추가
- **UI**
  - 리스트/테이블 기본 Vuetify 컴포넌트
  - 빈 데이터 상태에서도 화면 렌더링 보장

---

## 2) Reports 모듈 (프론트)
- **뷰 파일**
  - `src/views/Reports/SalesTags.vue` (차트/테이블 스켈레톤)
- **API**
  - `/api/reports/sales-tags`
  - 호출 방식: `src/services/http.ts` (fetch 기반, axios 금지)
- **UI**
  - 차트(Chart.js) + 테이블 스켈레톤
  - 데이터 미존재 시에도 기본 UI 렌더링

---

## 3) 사이드바/메뉴 연동
- **소스**: `/api/menu` 응답 반영
- **표시 항목**
  - OTA
  - Reports
- **미개발 시**: `WIP` 상태로 렌더링 (비활성, 클릭 시 `/wip/:slug`)

---

## ✅ DoR (Definition of Ready)
- [x] 라우트 정의 완료(`/admin/ota/*`, `/admin/reports/*`)
- [x] Page.vue 스켈레톤 생성(빈 상태라도 라우터 진입 가능)

---

## ✅ DoD (Definition of Done)
- [x] 토큰 로그인 후 OTA/Reports 메뉴 진입 가능  
- [x] 빈 화면 또는 WIP 상태라도 정상 렌더링  
- [x] axios/세션 미사용, `http.ts` fetch 기반 호출만 사용  

---

👉 **산출 파일**: `2025-10-Phase2_FE_SpecDraft.md`  
👉 FE-Core는 이 스펙대로 구현 착수, QA/PM은 DoR·DoD 기준으로 검증.  
