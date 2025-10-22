# 🔐 Hotel Admin 권한 시스템 SSOT 규정서 v2.0
**버전:** 2025-10-12  
**작성자:** BE-Core / FE-Core 공동  
**목적:** 시스템의 접근 및 관리 권한을 ‘업무 단위(Role Domain)’로 일관되게 정의하고, 운영·감사·확장에 일관성을 보장한다.

---

## 🧱 1. Role 정의 (업무 단위 기준)

| Role 코드 | 한글명 | 주요 책임 | 기본 접근 수준 |
|------------|---------|------------|----------------|
| FRONT | 프런트 데스크 | 객실예약, 투숙객 응대, 일마감 보조 | 대부분 view / 일부 edit |
| HK | 하우스키핑 | 객실상태, 청소스케줄 관리 | hk-* 전체 edit |
| FAC | 시설관리 | 설비점검, 고장/정비 내역 | 시설 관련 route edit |
| FNB | 부대업장 | FNB 매출, 상품, 정산 | fnb-* edit |
| MGMT | 경영지원 | OTA, 회계, 인사, 보고서 관리 | reports*, ota*, employees edit/admin |
| EXEC | 총괄(지배인·대표) | 전반 승인/리포트 열람 | admin-level view+approve |
| AUDIT | 감사 | 시스템 전반 흐름 감사(회계감사와 별도) | 전체 view, edit/admin 금지 |
| SUPERADMIN | 시스템 관리자 | 정책/권한 관리, 전권한 | 전체 admin (DB 기록 불필요) |

---

## ⚙️ 2. 권한 평가 우선순위

1️⃣ SUPERADMIN (절대 우선, DB 불필요)  
2️⃣ EXEC  
3️⃣ MGMT  
4️⃣ FRONT / HK / FAC / FNB  
5️⃣ AUDIT (읽기전용)  
→ 다중 역할일 경우 `max(access_level)` 적용

---

## 📘 3. 권한 레벨 의미 (고정)

| Level | 의미 | UI/기능 제한 |
|--------|------|--------------|
| none | 접근 불가 | 메뉴 비표시 |
| view | 조회 가능 | 테이블, 리포트 |
| edit | 수정 가능 | 폼, 업로드 |
| admin | 관리 기능 | RoleAccess, User관리 등 |

---

## 🧩 4. 업무 그룹별 route_name SSOT

| 그룹 | 예시 route_name | 기본 권한 |
|-------|------------------|-----------|
| Dashboard | dashboard-kpi | EXEC:view, MGMT:view |
| Housekeeping | hk-status, hk-schedule, hk-summary | HK:edit |
| Facilities | fac-status, fac-log, fac-summary | FAC:edit |
| FNB | fnb-items, fnb-tenders, fnb-summary | FNB:edit |
| OTA | ota-channels, ota-commissions, ota-orders | MGMT:edit |
| Bank | bank-ledger, pay-settlement, expenses | MGMT:edit |
| Reports | sales-tags, daily-summary, comparison | MGMT:view, AUDIT:view |
| Admin | users, employees, role-access | SUPERADMIN:admin |
| Audit | audit-log, audit-trace | AUDIT:view |

---

## 🧠 5. 데이터 구조

```sql
CREATE TABLE role_access (
    id INTEGER PRIMARY KEY,
    role_code VARCHAR(50) NOT NULL,
    route_name VARCHAR(120) NOT NULL,
    access_level VARCHAR(10) NOT NULL CHECK (access_level IN ('none','view','edit','admin')),
    UNIQUE (role_code, route_name)
);
```

---

## 🧮 6. 백엔드 정책

- `SUPERADMIN`: 모든 route `admin` 처리 (DB 무시)  
- `AUDIT`: 모든 route `view` 처리 (DB 값 무시)  
- `/api/users/roles/access`: CRUD API 유지, 변경 시 `write_audit('role_access', ...)` 로 로그 기록  
- `/api/users/roles/access/effective`: 사용자 로그인 시 현재 역할들의 최대 권한 계산  

---

## 💻 7. 프런트 정책

| 항목 | 규정 |
|------|------|
| 역할 선택 | 드롭다운 목록 = [FRONT, HK, FAC, FNB, MGMT, EXEC, AUDIT, SUPERADMIN] |
| 권한 토글 | none/view/edit/admin 버튼 |
| SUPERADMIN | 모든 버튼 admin + 비활성화 |
| AUDIT | 모든 버튼 view + 비활성화 |
| RoleAccessDashboard | 그룹별 accordion (Dashboard, HK, FNB, OTA 등) |
| Router Guard | meta.need 비교(`hasAccess(route, level)`) |
| QA/시뮬 | `/users/roles/access/effective` 호출로 시각적 검증 |

---

## 🧾 8. 운영 및 확장 규정

| 구분 | 규정 |
|------|------|
| 역할 추가 | `role_access`에 신규 role_code 추가, 프런트 자동 반영 |
| 역할 삭제 | `DELETE FROM role_access WHERE role_code='X'` |
| 초기화 | `/src/assets/role-defaults.json` 로 bulk insert |
| 감사 로그 | `/logs/audit_role_access.log`에 자동 기록 |
| 향후 확장 | Phase 4에서 `DEPT_MANAGER`, `HR`, `FINANCE` 등 세분화 가능 |
| SSOT 관리 | `/docs/runbooks/security/role_access_ssot.md` 유지 (append-only) |

---

✅ 본 문서는 Hotel Admin 권한 체계의 단일 진실 원본(SSOT)으로서,  
FastAPI · Vue3 전반의 인증/인가 구조 변경 시 **본 문서부터 수정 후 코드에 반영**한다.
