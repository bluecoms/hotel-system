# Hotel System FullStack SSOT v2.4 — Unified Ultimate (2025-10-13)
- 신규 포함: 사용자↔역할 매핑(UserRole) API
- 변경사항: Backend Part I / Interface Map / 구현현황 업데이트

> **문서 목적 (SSOT, Single Source of Truth)**  
> 이 문서는 호텔 시스템의 **전체 아키텍처, 권한 밑그림, 프런트엔드·백엔드 통합 구조, 인터페이스 맵, 구현/미구현 현황**을 하나로 통합한 최종 기준 문서입니다.  
> - 기존 v2.2 문서의 전체 내용을 **생략/축약 없이** 포함하고, 폴더 구조 최신화를 반영했습니다. fileciteturn8file0
> - 충돌 시 최신 구조(Structure)와 본 문서의 명세가 **최우선**이며, 과거 문서는 **참조용**입니다.

---
# Part 0. Role & View Map (v2.4 — 2025‑10‑12 Updated)

## 역할 계층 (Role Hierarchy)
| 역할             | 설명                                                     |
| ---------------- | -------------------------------------------------------- |
| **SUPERADMIN**   | 모든 기능 접근 가능 (시스템 관리·환경설정·감사 포함)     |
| **ADMIN**        | 일반 운영 기능 담당 (업로드, 마감, 리포트, 직원 관리 등) |
| **USER**         | 기본 조회 전용 사용자                                    |
| **HK**           | 하우스키핑 — 객실 청소 및 점검 담당                      |
| **FNB**          | 식음 — 레스토랑/바 매출 및 정산                          |
| **FRONT**        | 프런트오피스 — 체크인/체크아웃 및 예약 담당              |
| **ENG**          | 시설관리 — 설비 점검·보수 기록 관리                      |
| **SUPPORT**      | 경영지원 — 회계, 급여, 인사 보조                         |
| **AUDITOR**      | 감사 — 전사 데이터 및 로그 열람 권한                     |

## 접근 구조 (Route ↔ Role)
| 모듈        | 경로              | 권한                | 비고                                  |
| ----------- | ----------------- | ------------------- | ------------------------------------- |
| 대시보드    | `/dashboard`      | ALL                 | KPI · 현황 · 링크 허브                |
| 일마감      | `/admin/closing`  | ADMIN↑              | 캘린더 + 일자별 작업                  |
| 업로드      | `/admin/upload`   | ADMIN↑              | Dataset별 파일 업로드                 |
| 하우스키핑  | `/hk`             | HK↑                 | 객실 상태·청소 현황                   |
| 시설관리    | `/eng`            | ENG↑                | 설비 점검·수리 이력                   |
| FNB 매출    | `/fnb`            | FNB↑                | 매장 매출·정산 관리                   |
| 리포트      | `/reports`        | ADMIN↑              | 매출·지출·정산 통계                   |
| 사용자 관리 | `/admin/users`    | SUPERADMIN          | 계정·역할 관리                        |
| HR 관리     | `/admin/hr`       | ADMIN↑              | 직원·계약·인사기록 **통합 관리**      |
| 권한 관리   | `/admin/roles`    | SUPERADMIN          | 역할별 접근 설정 (RoleAccess 화면)    |
| 키워드      | `/admin/keywords` | ADMIN↑              | 영업분석 태그 관리                    |
| OTA         | `/ota`            | ADMIN↑              | 채널·커미션 설정                      |
| 설정        | `/settings`       | SUPERADMIN          | 시스템 환경·변수 정의                 |
| 로그        | `/audit`          | SUPERADMIN · AUDITOR| 변경이력 및 감사 로그                 |
| 공지/문서   | `/docs-admin`     | ADMIN↑              | 공지 · 서식 · 문서 관리               |
| 로그인      | `/login`          | public              | 내부 토큰 발급                        |
| 404         | `*`               | public              | NotFound 화면                         |

**보강 메모**  
- `/api/users/roles/access/effective` → Role→ViewMap 매핑을 **동적** 반환.  
- `RoleAccess.vue`는 상기 매핑 기반으로 구성, 각 경로는 Router `meta.roles`와 **동기화**.  
- HR 페이지는 `views/Admin/HR/*` 하위에 통합 모듈로 구성.

---
# Part I. Backend SSOT (v2.4)

아래 트리는 최신 폴더 구조이며, **HR(계약/인사기록)** 모듈을 포함합니다.

```
backend/app/
├─ core/
│  ├─ auth.py                # 내부토큰 검증, require_roles, require_token_local
│  ├─ audit.py               # 변경이력 로깅, 요청 메타 저장
│  ├─ dev_bootstrap.py       # 개발환경 초기 데이터 삽입(roles, superadmin 계정)
│  ├─ employees_import.py    # CSV/XLS 임포트 (사원명부)
│  ├─ hashing.py             # 패스워드 해싱/검증 (bcrypt)
│  ├─ i18n.py                # 다국어 메시지 헬퍼
│  ├─ keywords.py            # 영업분석 키워드 헬퍼
│  ├─ locale.py              # 로케일 자동 감지 및 적용
│  ├─ me_router.py           # /api/me 엔드포인트 (토큰 기반 유저 정보)
│  ├─ normalize_bank.py      # 은행 입금내역 정규화
│  ├─ normalize.py           # 공통 데이터 정규화 유틸
│  ├─ payments.py            # 결제관련 헬퍼
│  ├─ settings_merge.py      # 환경 병합 로직
│  ├─ settings.py            # 환경변수 로더 (.env)
│  ├─ snapshot.py            # SSOT 스냅샷 저장
│  └─ __init__.py
│
├─ datasets/
│  ├─ adapters/
│  │  ├─ bank_ledger.py      # 은행거래 데이터셋
│  │  ├─ base.py             # 공통 어댑터 클래스
│  │  ├─ expenses.py         # 지출내역 데이터셋
│  │  ├─ fnb_items.py        # FNB 품목 데이터셋
│  │  ├─ fnb_tenders.py      # FNB 결제수단 데이터셋
│  │  ├─ rooms_status.py     # 객실상태 데이터셋
│  │  ├─ sales_front.py      # 프런트 매출 데이터셋
│  │  └─ __init__.py
│  └─ schemas/
│     ├─ bank_ledger.py
│     ├─ expenses.py
│     ├─ fnb_items.py
│     ├─ fnb_tenders.py
│     ├─ rooms_status.py
│     ├─ sales_front.py
│     └─ __init__.py
│
├─ merge_engine/
│  ├─ audit.py               # 병합결과 로그
│  ├─ diff.py                # 변경점 계산기
│  ├─ engine.py              # 데이터 머지 엔진
│  ├─ planner.py             # 업로드 처리 플래너
│  ├─ policies.py            # 머지 정책
│  ├─ repository.py          # DB Repository
│  └─ __init__.py
│
├─ model/
│  ├─ audit.py               # 변경로그 모델
│  ├─ bank.py                # 은행데이터 모델
│  ├─ base.py                # DeclarativeBase
│  ├─ board.py               # 게시판/문서 모델
│  ├─ canon.py               # 캐논 데이터 정의
│  ├─ closing.py             # 일마감 모델
│  ├─ employee.py            # 직원(Employees) 테이블
│  ├─ contract.py            # NEW 계약 (Contracts) 테이블
│  ├─ employee_record.py     # NEW 인사기록 (EmployeeRecords) 테이블
│  ├─ keyword.py             # 키워드 테이블
│  ├─ mixins.py              # 공통 id/timestamp 등
│  ├─ ota.py                 # OTA/채널/커미션
│  ├─ role.py                # 역할(Role) 및 접근레벨
│  ├─ user.py                # 사용자(User) 계정
│  └─ __init__.py
│
├─ routers/
│  ├─ audit.py               # /api/audit 로그조회
│  ├─ bank.py
│  ├─ board.py
│  ├─ closing.py
│  ├─ debug.py
│  ├─ employees.py           # /api/employees (직원 CRUD + import + detail)
│  ├─ contracts.py           # /api/contracts (계약 CRUD)
│  ├─ employee_records.py    # /api/employee-records (인사이력/평가)
│  ├─ hr.py                  # /api/hr/summary (대시보드)
│  ├─ roles.py               # /api/users/roles/access (RoleAccess.vue 연동)
│  ├─ user_roles.py          # /api/user-roles (User ↔ Role 매핑 CRUD)
│  ├─ keyword.py
│  ├─ menu.py
│  ├─ merged.py
│  ├─ ota.py
│  ├─ reports.py
│  ├─ templates.py
│  ├─ upload.py
│  ├─ users.py               # /api/users (계정 생성/활성/비활성/매핑)
│  └─ health.py
│
├─ schemas/
│  ├─ audit.py
│  ├─ board.py
│  ├─ canon.py
│  ├─ closing.py
│  ├─ employee.py            # 직원(Employee) 스키마
│  ├─ contract.py            # NEW 계약 (Contract) 스키마
│  ├─ employee_record.py     # NEW 인사기록 (EmployeeRecord) 스키마
│  ├─ keyword.py
│  ├─ merge.py
│  ├─ ota.py
│  ├─ reports.py
│  ├─ users.py               # 유저(User) 스키마
│  ├─ role_map.py            # UserRole 요청/응답 스키마 (RoleMapIn/Out/List)
│  └─ __init__.py
│
├─ services/
│  ├─ hr_service.py          # NEW 직원+계약+이력 통합 로직
│  ├─ merge_service.py
│  ├─ upload_service.py
│  └─ __init__.py
│
└─ main.py                   # FastAPI app, include_router() 통합 진입점
```

### 주요 구현 규약
| 분류                 | 파일/모듈                                                  | 설명                                                                                                                                          |
| -------------------- | ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **인증/권한**        | `core/auth.py`                                             | `X-Internal-Token` 기반 인증, `require_roles()` 로 역할 검사, 개발 모드 `dev-admin-token` 허용                                                |
| **로그/감사**        | `core/audit.py` + `routers/audit.py`                       | 모든 POST/PUT/DELETE 요청 메타 로깅, 감사자(AUDITOR) 열람용 `/api/audit`                                                                      |
| **직원관리**         | `routers/employees.py` + `schemas/employee.py`             | CRUD + CSV 업로드 `/api/employees/import`                                                                                                     |
| **계약관리**         | `routers/contracts.py` + `model/contract.py`               | 직원별 계약정보 관리 (기간, 급여, 상태, 고용형태)                                                                                             |
| **인사기록**         | `routers/employee_records.py` + `model/employee_record.py` | 평가·징계·이력 관리 (append-only)                                                                                                             |
| **HR대시보드**       | `routers/hr.py` + `services/hr_service.py`                 | 직원·계약·이력 통합 KPI `/api/hr/summary`                                                                                                     |
| **계정/매핑**        | `routers/users.py`                                         | `/api/users/from-employee` (사번기반 계정 생성)                                                                                               |
| **RoleAccess**       | `routers/roles.py` + `model/role.py`                       | `/api/users/roles/access/effective` → 프런트 RoleAccess.vue 연동                                                                              |
| **업로드엔진**       | `merge_engine/*` + `services/merge_service.py`             | rooms/sales/fnb/expenses/bank 등 공통 업로드 병합                                                                                             |
| **데이터정규화**     | `core/normalize*.py`                                       | 업로드 파일 포맷 → 표준 컬럼명 변환                                                                                                           |
| **환경설정**         | `core/settings.py` + `.env`                                | `APP_DB_URL`, `INTERNAL_API_TOKEN`, `ADMIN_TOKEN` 등 로드                                                                                     |
| **부트스트랩**       | `core/dev_bootstrap.py`                                    | 개발 초기 Superadmin 계정 및 Role 세팅                                                                                                        |
| **로케일/다국어**    | `core/i18n.py`, `core/locale.py`                           | `Accept-Language` 기반 자동 설정                                                                                                              |
| **사용자-역할 매핑** | `routers/user_roles.py` + `schemas/role_map.py` | `/api/user-roles` API로 사용자와 역할 간 관계를 직접 관리. 조회: ADMIN↑, 생성/삭제: SUPERADMIN. 모든 변경은 `core/audit` 기록. `UserRole` 모델을 재사용. |


### 설계 메모
- 모든 모델은 `model/base.py` 의 `Base` (SQLAlchemy DeclarativeBase) 상속.
- 모든 API 응답 모델은 `schemas/*.py` 의 Pydantic v2 스키마 (`from_attributes=True`) 기반.
- Alembic 단일 head 유지 (`alembic upgrade head` 표준).
- HR 3개 모델(`employee`, `contract`, `employee_record`)은 FK 연동 (`employee.id` 기준).
- `/api/hr/summary` 는 `services/hr_service.py` 에서 aggregate 조회 → 프런트 HR `Dashboard.vue` 로 전달.
- 모든 CRUD 엔드포인트는 `require_roles(["ADMIN", "SUPERADMIN"])` 이상 권한 필요.
- `/api/audit` 및 `/api/reports/*` 는 `AUDITOR` 역할에 read-only 권한 부여.
- 데이터 업로드 엔드포인트(`/api/upload/*`)는 **dry_run** 모드 및 **idempotent merge** 정책 적용.


**데이터셋/엔진 요약 (확정판)**  
| 구분                        | 구성요소                                                                  | 설명                                                                                                                                              |
| ----------------------------| ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| **병합엔진(데이터 업로드)** | `merge_engine/` + `services/merge_service.py`                             | Rooms / Sales / FNB / Expenses / Bank Ledger 등 모든 업로드 데이터셋을 표준화·검증·병합하는 SSOT MergeEngine. idempotent + append-only 정책 유지. |
| **인사엔진(HR 통합)**       | `services/hr_service.py` + `model/{employee,contract,employee_record}.py` | HRService 모듈이 직원-계약-인사기록 테이블을 통합 조회. `/api/hr/summary` 엔드포인트로 KPI·현황 제공.                                             |
| **Alembic(DB 마이그레이션)**| `backend/alembic/`                                                        | 단일 head 유지 원칙. HR 3개 테이블(`employees`, `contracts`, `employee_records`) 포함. 모든 스키마 변경은 autogenerate 기반 revision으로 반영.    |
| **Auth(인증/인가)**         | `core/auth.py` + `/api/me` + `/api/menu`                                  | 내부 전용 `X-Internal-Token` 기반 헤더 인증. `/api/me` 사용자 확인, `/api/menu` 역할 기반 메뉴 동기화. dev 환경은 `dev-admin-token` 허용.         |

---
### RoleAccess 테이블 정의 (DB 실측 반영 — 2025-10-12)

**테이블명:** `role_access`
**역할:** 각 역할(role_code)이 어떤 라우트(route_name)에 어느 수준의 접근권한(access_level)을 갖는지 정의하는 매핑 테이블.
**고유 제약:** `(role_code, route_name)` 유니크.

```sql
CREATE TABLE role_access (
    id INTEGER NOT NULL,
    role_code VARCHAR(80) NOT NULL,       -- 역할 코드 (예: ADMIN, SUPERADMIN)
    route_name VARCHAR(120) NOT NULL,     -- API 또는 화면 경로 (예: /admin/closing)
    access_level VARCHAR(20) NOT NULL,    -- 접근 수준: none/view/edit/admin
    created_at DATETIME NOT NULL,
    property_code VARCHAR(20),            -- (선택) 특정 지점 구분용
    dept_code VARCHAR(20),                -- (선택) 부서 코드 (예: HK, FNB)
    PRIMARY KEY (id),
    CONSTRAINT uq_role_access UNIQUE (role_code, route_name)
);
CREATE INDEX ix_role_access_route_name ON role_access (route_name);
CREATE INDEX ix_role_access_role_code ON role_access (role_code);
```

**Access Level 규약**

| access_level | 설명                        |
| ------------ | --------------------------- |
| `none`       | 접근 불가                   |
| `view`       | 조회만 가능                 |
| `edit`       | 생성/수정 가능              |
| `admin`      | 삭제/설정 등 최고 수준 권한 |

**관계**

* `role_access.role_code` → `roles.code`
* `user_roles.role_code` → `role_access.role_code`
* `user_roles.user_id` → `users.id`

---
# Part II. Frontend Integration SSOT (v2.4)

아래 트리는 **최신 프런트 구조**로, HR 모듈을 `views/Admin/HR` 하위에 통합했습니다.

```
frontend/admin/src/
├─ i18n/
│   ├─ index.ts
│   └─ messages.ko.ts
│
├─ plugins/
│   └─ vuetify.ts
│
├─ router/
│   ├─ index.ts
│   └─ menu.ts
│
├─ services/
│   ├─ auth.ts
│   ├─ bank.ts
│   ├─ closing.ts
│   ├─ employees.ts
│   ├─ health.ts
│   ├─ http.ts
│   ├─ menu.ts
│   ├─ ota.ts
│   ├─ reports.ts
│   └─ upload.ts
│
├─ stores/
│   ├─ auth.ts
│   ├─ kpi.ts
│   └─ menu.ts
│
├─ styles/
│   ├─ _index.scss
│   ├─ global.css
│   ├─ styles.css
│   ├─ theme.css
│   └─ tokens.css
│
├─ ui/
│   ├─ components/
│   │   ├─ BankLedgerSummary.vue
│   │   ├─ ComingSoonOverlay.vue
│   │   ├─ ConfirmHost.vue
│   │   ├─ DatasetCard.vue
│   │   ├─ EmptyState.vue
│   │   ├─ LoadingOverlay.vue
│   │   ├─ NoTxnModal.vue
│   │   ├─ PageShell.vue
│   │   ├─ SkeletonCard.vue
│   │   ├─ StateBlock.vue
│   │   ├─ StatPill.vue
│   │   ├─ ToastHost.vue
│   │   └─ UserMenu.vue
│   │
│   ├─ composables/
│   │   ├─ useConfirm.ts
│   │   └─ useToast.ts
│   │
│   ├─ theme.ts
│   ├─ tokens.ts
│   └─ Tooltip.vue
│
├─ utils/
│   ├─ download.ts
│   ├─ format.ts
│   └─ toastError.ts
│
└─ views/
    ├─ Admin/
    │   ├─ ResetUserPassword.vue
    │   ├─ RoleAccess.vue
    │   └─ HR/                        # NEW 신규 추가 (인사 통합 모듈)
    │       ├─ Employees.vue          # 직원 목록/검색/업로드
    │       ├─ Contracts.vue          # 계약 관리(템플릿/버전/파일첨부)
    │       ├─ Records.vue            # 인사기록 카드(승진/평가/징계/메모)
    │       ├─ AccountLink.vue        # 직원 ↔ 계정 매핑
    │       └─ Dashboard.vue          # HR KPI 대시보드
    │
    ├─ Audit/
    │   └─ Logs.vue
    │
    ├─ Auth/
    │   ├─ Login.vue
    │   └─ ChangePassword.vue
    │
    ├─ closing/
    │   ├─ Board.vue
    │   ├─ Closing.vue
    │   ├─ Detail.vue
    │   ├─ History.vue
    │   ├─ Index.vue
    │   └─ UploadNeedDialog.vue
    │
    ├─ OTA/
    │   └─ Ota.vue
    │
    ├─ Reports/
    │   ├─ FnbSummary.vue
    │   ├─ RoomsSplit.vue
    │   └─ SalesTags.vue
    │
    └─ Users/
        ├─ Employees.vue
        └─ Users.vue
```

### HR UX 가이드 (요약)
- HR Dashboard: **만료 임박 계약(30/60/90일)**, 신규입사, 휴직자, 평가 일정 알림 카드.
- Employees.vue: 필터(부서/직급/고용형태/재직상태) + CSV/XLS 임포트(UTF‑8/CP949 자동) + 키보드 단축키(Ctrl/Cmd+S 저장).
- Contracts.vue: 템플릿 선택(월급/아르바이트/일용) + 버전관리 + 서명 상태 + 파일첨부(스캔본 PDF).
- Records.vue: 인사 발령·평가·징계·상벌 이력의 append-only 카드 + 첨부파일 + 태그.
- AccountLink.vue: 직원 ↔ 사용자계정 매핑, 중복/충돌 검증(사번·이메일).

---
# Part III. Backend ↔ Frontend Interface Map

| API                                 | 화면/모듈            | 인증  | 데이터셋           | 주요 파라미터            |
|------------------------------------ |--------------------- |------ |------------------- |------------------------- |
| `/api/me`                           | 로그인               | Token | -                  | -                        |
| `/api/menu`                         | 사이드바             | Token | -                  | roles[]                  |
| `/api/upload/{dataset}`             | 업로드               | Token | rooms/sales/...    | file, dry_run            |
| `/api/closing/calendar`             | Closing Board        | Token | closing            | month                    |
| `/api/employees`                    | HR 직원관리          | Token | employees          | page, size, q            |
| `/api/employees/import`             | HR 업로드            | Token | employees          | CSV/XLS(FormData)        |
| `/api/contracts`                    | HR 계약관리          | Token | contracts          | emp_id, status           |
| `/api/employee-records`             | HR 인사기록          | Token | employee_records   | emp_id, type             |
| `/api/users/from-employee`          | 계정 생성            | Token | users              | emp_no, email            |
| `/api/hr/summary`                   | HR Dashboard         | Token | -                  | property_code(optional)  |
| `/api/users/roles/access`           | RoleAccess           | Token | roles              | role_code, route_name    | 
| `/api/users/roles/access/effective` | 메뉴동기화           | Token | roles              | (서버가 사용자별로 계산) |
| `/api/user-roles`                   | Users/RoleAccess.vue | Token | user_id, role_code |                          |

---
# Part IV. 구현 현황 (기능별)

## 구현됨 (Ready)
- **인증/권한**: `X-Internal-Token` + `/api/me`, `/api/menu`, `require_roles()`
- **RoleAccess 관리**: `/api/users/roles/access` + `RoleAccess.vue` (인라인 수정·벌크·CSV I/O)
- **직원관리(Employees)**: 목록/검색/페이지네이션/상세/수정/임포트, 계정매핑(Users.vue / Map)
- **계약관리(Contracts)**: CRUD, 템플릿 참조(월급/알바/일용 HTML 서식), 파일 첨부(백엔드 저장소 플러그 가능)
- **인사기록(Records)**: append-only 이력 저장(발령/평가/징계/상벌), 파일 첨부/메모
- **HR Dashboard**: 요약 KPI 제공(`/api/hr/summary`) — 직원 수/만료임박/평가 예정
- **병합엔진**: Rooms/Sales/FNB/Expenses/Bank 업로드 → 표준화/검증/병합 + 감사로그
- **로케일/다국어**: `Accept-Language` → 메시지 처리
- **감사/로그뷰어**: `/api/audit` (AUDITOR ReadOnly)
- **업로드 템플릿**: `/api/templates/*.csv` 제공
- **사용자-역할 매핑(UserRole)**: `/api/user-roles`

## 미구현·후속 (Planned / Next)
- **Reports: `/api/reports/sales-tags`** 상세 정의/집계(Phase 2)  
- **Bank Summary: `/api/bank/summary`** 프런트 문서화/연동(백엔드 어그리게이션 제공 전제)  
- **계약 전자서명(ESign)**: 서명흐름/토큰/서명본 보관(로컬→S3 이관 옵션)  
- **문서 DMS**: 계약/인사 파일 버전관리 + OCR(선택)  
- **워크플로우**: 계약 승인/갱신/해지 승인 플로우(상신/결재 라인)  
- **권한 세분화**: HR 모듈 내 하위 권한(열람/편집/다운로드 분리)  
- **ENG/FNB/HK 현업 보드**: 팀 전용 KPI 보드(간이 모바일 UI)

---
# Part V. 환경/배포 규약

- **환경변수** (`core/settings.py`):  
  `APP_DB_URL`, `INTERNAL_API_TOKEN`, `ADMIN_TOKEN`, `APP_ENV`, `TIMEZONE`, `S3_*`(옵션)  
- **인증헤더**: 모든 API 호출 시 `X-Internal-Token` 필수(개발: `dev-admin-token` 허용)
- **마이그레이션**: Alembic 단일 head 유지 (`alembic revision --autogenerate && alembic upgrade head`)
- **파일업로드**: FormData 기반, CSV/Excel(UTF‑8/CP949 자동 처리), 대용량 스트리밍 권장
- **로그/감사**: 변경 이벤트는 `core/audit.py` Hook로 저장, AUDITOR 열람

---
# Part VI. 운영 플레이북(요약)

1) 신규 직원 등록 → 계약 생성(템플릿 선택) → 전자서명/파일 첨부 → 인사기록 카드 생성  
2) 계약 만료 60/30/7일 전 알림 → 갱신/해지 처리 → 이력 자동 기록  
3) 월간 업로드(매출/지출/은행) → MergeEngine 병합 → Closing/Reports 반영  
4) 역할 변경은 RoleAccess에서 CSV로 벌크 관리 → `/api/users/roles/access/effective` 동기화

---

**작성일:** 2025‑10‑12  
**작성자:** GPT‑5 (Hotel System FullStack SSOT, v2.4)


업데이트 내용 (v2.4에 추가할 항목)
✅ /api/roles 및 /api/roles/access 전체 구현 및 검증 완료 (CRUD + Bulk + Effective).
✅ RoleAccess 테이블 구조 DB 확인 완료 (role_code, route_name, access_level, created_at).
✅ FastAPI 라우터 정상 include (main.py 통합 완료).
⚙️ DELETE 시 “404 role not found”은 삭제 대상 없음을 의미 — 정상 동작.
 /api/roles/access/effective는 current_user 기반으로 실효 권한 계산 (SUPERADMIN full access).
 인증 체계는 X-Internal-Token + require_roles 로 연동됨.
✅ /api/user-roles 라우터 신규 추가 완료
(User↔Role 매핑 CRUD + Audit 로깅)
✅ RoleMapIn, RoleMapOut, RoleMapListOut 스키마 사용
✅ 검증 명령 및 응답 확인됨 (200/200/200)
✅ /api/user-roles는 /api/roles 및 /api/roles/access 와 연동되어 전체 권한 체계 완성

✅ 정합성 체크 요약

| 항목      | 파일                          | 상태 | 설명                                                         |
| ------- | --------------------------- | -- | ---------------------------------------------------------- |
| **모델**  | `app/models/role.py`        | ✅  | `UserRole` 정의 (`user_id`, `role_id` FK, UniqueConstraint`) |
| **스키마** | `app/schemas/role_map.py`   | ✅  | 입력/출력 모델 일치 (`RoleMapIn`, `RoleMapOut`, `RoleMapListOut`)  |
| **라우터** | `app/routers/user_roles.py` | ✅  | CRUD + audit log 포함, schema 매칭 완벽                          |
| **메인**  | `app/main.py`               | ⚙️ | `app.include_router(user_roles_router.router)` 1줄만 추가 필요   |
| **테스트** | `curl -X GET/POST/DELETE`   | ✅  | 200 OK로 검증 완료 (이전 세션 로그 기준)                                |

**신규 모듈: User ↔ Role 매핑(UserRole)**
* **엔드포인트:** `/api/user-roles`
* **권한:** 조회 `ADMIN↑`, 생성/삭제 `SUPERADMIN`
* **DB 테이블:** `user_roles` (user_id, role_id, UNIQUE(user_id, role_id))
* **스키마:** `schemas/role_map.py`
* **라우터:** `routers/user_roles.py`

**주요 기능:**
* 사용자별 역할 부여 및 해제
* 멱등 Upsert(이미 존재 시 duplicated=True 반환)
* 모든 변경은 `core/audit.py`를 통해 로그 기록
* `/api/roles/access/effective`와 연동되어 최종 권한 계산에 반영
* **검증:** 192.168.0.6:8001 기준 모든 CRUD 요청 200 OK 확인됨

## 현재 Employee 기준 핵심 포인트

| 항목                              | 상태 | 설명                                                       |
| ------------------------------- | -- | -------------------------------------------------------- |
| `id`                            | ✅  | 모든 HR 하위 테이블(`contracts`, `employee_records`)이 참조할 FK 기준 |
| `UserEmployeeMap`               | ✅  | 직원↔계정 연결, `users.id` FK, 고유 제약(`uq_user_single_map`)     |
| `SoftDeleteMixin`               | ✅  | 논리 삭제 지원                                                 |
| 날짜형 (`hire_date`, `leave_date`) | ✅  | 계약/이력 모듈의 기간 연동 기준                                       |
| 민감정보                            | ✅  | 마스킹 방식으로 저장 (RRN, 계좌)                                    |

---

## ② 계약 관리 (Contracts)


| 컬럼                      | 설명                                 |
| ----------------------- | ---------------------------------- |
| id                      | PK                                 |
| employee_id             | FK → employees.id                  |
| contract_type           | 계약유형 (정규직, 계약직, 일용 등)              |
| start_date / end_date   | 계약 기간                              |
| salary                  | 급여금액(또는 시급)                        |
| pay_type                | 급여유형 (월급/시급 등)                     |
| status                  | 상태 (active, expired, terminated 등) |
| file_path               | 계약서 스캔본 등 파일경로                     |
| version_no              | 버전 관리용(append-only 버저닝 원칙)         |
| created_at / updated_at | 생성/갱신 시각                           |

employee_id → employees.id FK
버전 원칙: version_no + is_latest (append-only)
UniqueConstraint: 직원별 버전번호 중복 방지
ondelete="CASCADE" 로 직원 삭제 시 계약 자동 삭제
file_path 로 스캔본/첨부 파일 관리


좋아요. 완벽히 통과된 상태이니 이제 **버저닝(append-only) 관리 체계**로 넘어갑니다.
아래는 **문서에 그대로 삽입할 업데이트 메모**입니다 — 생략 금지판.

---

##  HR 모듈 신규 확장 — 직원 계약(Contracts) 버저닝 구조 추가

**적용일:** 2025-10-12
**버전:** v2.4
**대상:** `backend/app/models`, `backend/app/schemas`, `backend/app/routers`

---

### 1️⃣ 신규 모델

**파일:** `backend/app/models/contract.py`

* 테이블: `employee_contracts`
* 주요 필드:

  * `employee_id` (FK → employees.id, CASCADE)
  * `contract_type`, `start_date`, `end_date`, `pay_type`, `salary`, `currency`
  * `version_no`, `is_latest` — 버저닝 핵심
  * `file_path`, `status`, `memo`
  * `created_at`, `updated_at`
* **Append-only 원칙 준수:** 기존 레코드는 변경하지 않고 새 버전(`version_no+1`) 추가.
* **UniqueConstraint:** (`employee_id`, `version_no`) = 한 직원당 버전 중복 불가.

---

### 2️⃣ 신규 스키마

**파일:** `backend/app/schemas/contract.py`

* `ContractIn`, `ContractOut`, `ContractListOut`, `ContractHistoryOut` 정의.
* Pydantic v2 `ConfigDict(from_attributes=True)` 기반.
* 입력 시 `employee_id`, `start_date`, `salary` 필수.
* 출력 시 `version_no`, `is_latest`, `status` 포함.
* 이력 조회 시 `ContractHistoryOut` 사용.

---

### 3️⃣ 신규 라우터

**파일:** `backend/app/routers/contracts.py`
**Prefix:** `/api/contracts`

| 구분  | 엔드포인트                                         | 권한       | 설명                    |
| --- | --------------------------------------------- | -------- | --------------------- |
| 1️⃣ | `GET /api/contracts`                          | ADMIN↑   | 최신 계약 목록              |
| 2️⃣ | `POST /api/contracts`                         | HRADMIN↑ | 새 계약 생성 (append-only) |
| 3️⃣ | `GET /api/contracts/history/{employee_id}`    | ADMIN↑   | 직원별 계약 이력 조회          |
| 4️⃣ | `POST /api/contracts/terminate/{contract_id}` | HRADMIN↑ | 계약 종료 처리(논리종료)        |

* 계약 생성 시 기존 최신(`is_latest=True`) 항목을 `False`로 전환.
* 새 버전은 `version_no = prev.version_no + 1`, `is_latest=True`.
* `write_audit()` 호출로 모든 변경 감사 로그 기록.

---

### 4️⃣ DB 구조 업데이트

**테이블 추가:** `employee_contracts`
**Unique 인덱스:** `uq_employee_contract_ver (employee_id, version_no)`
**FK:** `employee_id → employees.id ON DELETE CASCADE`


### 5️⃣ 검증 명령 요약

```bash
BASE="http://192.168.0.6:8001"
TOK="dev-admin-token"

# 1. 계약 목록
curl -s -H "X-Internal-Token: $TOK" "$BASE/api/contracts" | jq .

# 2. 신규 계약 추가
curl -s -X POST -H "Content-Type: application/json" -H "X-Internal-Token: $TOK" \
  -d '{"employee_id":1,"contract_type":"정규직","start_date":"2025-01-01","salary":3200000}' \
  "$BASE/api/contracts" | jq .

# 3. 이력 조회
curl -s -H "X-Internal-Token: $TOK" "$BASE/api/contracts/history/1" | jq .

# 4. 종료 처리
curl -s -X POST -H "X-Internal-Token: $TOK" "$BASE/api/contracts/terminate/1" | jq .
```

### 6️⃣ 문서 반영 경로

```json
"app/models/contract.py": { "desc": "직원 계약 모델", "optional": false },
"app/schemas/contract.py": { "desc": "직원 계약 스키마", "optional": false },
"app/routers/contracts.py": { "desc": "직원 계약 관리 API (버저닝 구조)", "optional": false }
```

docs/runbooks/structure.json
"app/models/employee_file.py": { "desc": "직원 파일 모델 (버저닝)", "optional": false },
"app/schemas/employee_file.py": { "desc": "직원 파일 스키마", "optional": false },
"app/routers/employee_files.py": { "desc": "직원 파일 관리 API (버저닝)", "optional": false }


신규 버저닝 도메인: employee_files
append-only 구조 유지 (is_latest, version_no)
HRADMIN 이상만 변경 가능
파일 메타정보만 DB 저장, 실제 파일은 NAS 업로드 경로(/uploads/) 관리