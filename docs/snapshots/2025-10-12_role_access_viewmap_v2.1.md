# 🧩 Hotel Admin Role–View Mapping (v2.1 SSOT)

**버전:** 2025-10-12  
**담당:** BE-Core / FE-Core  
**목적:** 역할별 접근 제어 및 화면 매핑 일원화 (프런트–백엔드–권한 SSOT)

---

## 1️⃣ Role–View 매핑표

| 그룹 | 경로 | 파일 | Role | Access |
|------|------|------|------|--------|
| Dashboard | /dashboard | Dashboard.vue | FRONT, MGMT, EXEC, AUDIT | view |
| Closing | /closing | ClosingBoard.vue | FRONT, HK, MGMT, EXEC | edit/view |
| Housekeeping | /housekeeping | HK/*.vue | HK, MGMT | edit |
| Facilities | /facilities | FAC/*.vue | FAC, MGMT | edit |
| F&B | /fnb | Reports/FnbSummary.vue | FNB, MGMT | edit/view |
| Reservations | /reservations | Reservations/Quotation.vue | RESV, MGMT, EXEC, AUDIT | edit/view |
| OTA | /ota | OTA/Ota.vue | MGMT, EXEC | edit/view |
| Reports | /reports | Reports/*.vue | MGMT, EXEC, AUDIT | view |
| Keywords | /keywords | Keyword.vue | MGMT, SUPERADMIN | edit/admin |
| Employees | /users/employees | Employees.vue | MGMT, SUPERADMIN | edit/admin |
| Users | /users | User.vue | SUPERADMIN | admin |
| Reset PW | /admin/reset-password | ResetUserPassword.vue | SUPERADMIN | admin |
| Change PW | /auth/change-password | ChangePassword.vue | ALL | edit(self) |
| Audit Logs | /audit | Audit.vue | AUDIT, SUPERADMIN | view |
| Docs Admin | /docs-admin | DocsAdmin.vue | MGMT, SUPERADMIN | edit/admin |

---

## 2️⃣ Access Level 정의

| Level | 동작 | 예시 |
|-------|------|------|
| view | 조회만 | Reports, Dashboard |
| edit | 입력/업로드 | ClosingBoard, OTA |
| admin | 사용자/권한 수정 | User, RoleAccess |

---

## 3️⃣ 프런트 구현 규칙

- route.meta: `{ requiresAuth:true, need:'edit', roles:['MGMT'] }`
- usePerms().hasAccess(route, level) 로 가드
- v-can="'edit'" 로 버튼 제어
- Sidebar: meta.roles 기준으로 필터

---

## 4️⃣ 백엔드 규칙

| 라우터 | require_roles | 설명 |
|--------|----------------|------|
| Upload | ['MGMT'] | 관리자만 |
| OTA | ['MGMT','EXEC'] | OTA 담당 |
| Reports | ['MGMT','EXEC','AUDIT'] | 보고서 조회 |
| Users | ['SUPERADMIN'] | 계정 관리 |

---

## 5️⃣ role-access-defaults.json

```json
{
  "FRONT": { "dashboard": "view", "closing": "edit" },
  "HK": { "housekeeping": "edit" },
  "FAC": { "facilities": "edit" },
  "FNB": { "fnb-summary": "edit" },
  "RESV": { "reservations": "edit" },
  "MGMT": {
    "dashboard": "view",
    "reports": "view",
    "ota": "edit",
    "keywords": "edit",
    "employees": "edit",
    "docs-admin": "edit"
  },
  "EXEC": { "dashboard": "view", "reports": "view", "ota": "view" },
  "AUDIT": { "dashboard": "view", "reports": "view", "audit": "view" },
  "SUPERADMIN": { "*": "admin" }
}
```

---

## 6️⃣ QA 기준 요약

| Role | 검증 항목 | 기대 동작 |
|------|------------|-----------|
| RESV | /reservations | 편집 가능 |
| FRONT | /closing | 편집 가능 |
| FNB | /fnb | 편집 가능 |
| AUDIT | /audit | 조회만 |
| SUPERADMIN | 전체 접근 | 전체 허용 |

---

## 7️⃣ 구조 연계 요약

| 범주 | 경로 | 역할 |
|------|------|------|
| Reports | src/views/Reports/* | MGMT, AUDIT |
| Users | src/views/Users/* | SUPERADMIN, MGMT |
| OTA | src/views/OTA/Ota.vue | MGMT |
| Auth | src/views/Auth/* | ALL |
| Reservations | src/views/Reservations/* | RESV |
| Audit | src/views/Audit.vue | AUDIT |

---

## 8️⃣ 배포 정책

- 문서 저장 경로: `docs/runbooks/security/2025-10-12_role_access_viewmap_v2.1.md`
- Router patch 대상: `src/router/index.ts`
- DB seed: Alembic revision “add role RESV” 생성
