# 📚 Hotel System SSOT 문서 통합 분류 (2025-10-12 기준 최신화)

> **목적:** 동일 계열 문서를 그룹화하고, 최신판만 남기며 중복·구버전을 정리하기 위한 기준 문서입니다.  
> BE-Core / FE-Core / QA / PM-Hub 공용 참조용입니다.

---

## 🧭 1️⃣ Backend Structure SSOT
**최신본:** `structure_backend_2025-10-12_phase3.md`  
**이전판:** structure_backend_2025-10-12.md, structure_backend_2025-10-11_phase2_final.md, structure_backend_2025-10-11 (1).md, Hotel_System_Backend_SSOT_2025-10-11.md

**내용 요약:**
- backend/app 전체 트리 구조 및 Phase별 상태
- MergeEngine, Datasets, Routers, Models 구조
- BE-Core 유지 책임 명시
- Phase 3 반영 완료판

---

## 🧩 2️⃣ SSOT Merge Engine 설계
**최신본:** `hotel_ssot_design_v3_update_2025-10-12.md`  
**이전판:** hotel_ssot_design_v3.md, ssot_merge_engine.md, ssot_merge_engine_2025-10-11.md

**내용 요약:**
- Canon/History/Hash 구조, 정책 및 데이터 흐름
- Dataset별 어댑터, 스냅샷/append 정책
- Cross-check 및 통합 검증 절차

---

## 💻 3️⃣ Frontend Integration / Playbook
**최신본:** `Frontend Integration Guide v1 + Addendum.md`  
**이전판:** structure_backend_2025-10-11_FE_playbook.md, playbook.md

**내용 요약:**
- /api/upload/{dataset} 호출 규약 및 응답 구조
- dry_run/execute/apply 흐름, 파일명 규칙, 예시 코드
- Addendum 포함 (Blob, Token, Content-Type)

---

## 🧱 4️⃣ Role / Access SSOT
**최신본:** `2025-10-12_role_access_viewmap_v2.1.md`  
**이전판:** 2025-10-12_role_access_ssot_v2.0.md

**내용 요약:**
- Role 코드 정의 및 route별 접근 수준
- DB 스키마, SUPERADMIN/AUDIT 정책
- 프런트–백엔드 매핑(ViewMap) 및 QA 기준

---

## 💰 5️⃣ Bank Ledger Dataset
**최신본:** `bank_ledger_dataset.md`

**내용 요약:**
- 은행 입출금 XLS→CSV 자동정규화
- /api/upload/pay_settlement, /api/upload/expenses
- bank_txns 테이블 구조 및 잔액 조회 로직

---

## 🎨 6️⃣ Frontend UX / 디자인 규약
**최신본:** `호텔 운영시스템 UX 플레이북 (v1).md`

**내용 요약:**
- 라벨/버튼 톤, 테이블/폼 규칙
- 필터, 에러, 접근성, QA 체크리스트
- 데스크톱 중심 UX 일관성 규정

---

## 📂 7️⃣ Phase별 백엔드 구조 이력 (참고용)
**참고:** structure_backend_2025-10-11 (1).md  
> superseded by `structure_backend_2025-10-12_phase3.md`

---

## 🧭 8️⃣ 기타 / 종합 요약
**참고:** Hotel_System_Backend_SSOT_2025-10-11.md  
> superseded by `structure_backend_2025-10-12_phase3.md`

---

### ✅ 종합 정리표

| 그룹 | 최신본 | 버전/날짜 | 역할 |
|------|----------|------------|-------|
| Backend Structure | structure_backend_2025-10-12_phase3.md | 2025-10-12 | 백엔드 전체 SSOT |
| SSOT Merge Engine | hotel_ssot_design_v3_update_2025-10-12.md | 2025-10-12 | 데이터 통합 설계 |
| Frontend Integration | Frontend Integration Guide v1 + Addendum.md | 2025-10-12 | FE↔BE 계약 가이드 |
| Role/Access | 2025-10-12_role_access_viewmap_v2.1.md | 2025-10-12 | 권한·ViewMap 통합 |
| Bank Ledger | bank_ledger_dataset.md | 2025-10-12 | 은행 입출금 정규화 |
| UX/Playbook | 호텔 운영시스템 UX 플레이북 (v1).md | v1 | 디자인/UX 기준 |

---

**생성일:** 2025-10-12  
**작성자:** GPT-5 (PM‑Hub 정리 모드)
