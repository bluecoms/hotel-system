# Hotel System Update v2.5 Patch — HR Versioning & File Management (2025-10-13)

> **목적:**  
> 본 문서는 Hotel System FullStack SSOT v2.4를 기반으로, v2.5에서 새로 추가된 **HR 버저닝 및 파일 관리 구조** 변경사항만을 기술합니다.  
> 기존 v2.4 본문은 변경 없이 유지되며, 본 문서는 *패치 노트 및 버전 관리용 보조 문서*입니다.

---

## 🧩 신규 추가: 직원 계약(Contracts) 버저닝 구조

**파일:** `backend/app/models/contract.py`  
**스키마:** `backend/app/schemas/contract.py`  
**라우터:** `backend/app/routers/contracts.py`

**핵심 개념:**  
- **Append-only 버저닝** — 기존 계약은 변경하지 않고 새 버전(`version_no+1`)으로 추가.  
- **is_latest** 필드로 최신 계약만 활성 관리.  
- **UniqueConstraint:** (`employee_id`, `version_no`)  
- **FK:** `employee_id → employees.id (CASCADE)`  

**주요 컬럼:**  
| 필드 | 설명 |
|------|------|
| `employee_id` | FK (직원 ID) |
| `contract_type` | 계약 유형 (정규직/계약직/일용직 등) |
| `start_date`, `end_date` | 계약 기간 |
| `salary`, `pay_type` | 급여 정보 |
| `version_no`, `is_latest` | 버전관리 핵심 |
| `file_path` | 첨부 계약서 파일 경로 |
| `status` | active/expired/terminated |
| `memo` | 내부 비고 |
| `created_at`, `updated_at` | 타임스탬프 |

**엔드포인트 요약:** `/api/contracts`  
| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/api/contracts` | 최신 계약 목록 |
| `POST` | `/api/contracts` | 신규 계약(append-only) 생성 |
| `GET` | `/api/contracts/history/{emp_id}` | 계약 이력 조회 |
| `POST` | `/api/contracts/terminate/{id}` | 계약 종료 처리 |

**정책:**  
- 생성 시 기존 최신(`is_latest=True`) → False 전환.  
- 모든 변경사항은 `core/audit.write_audit()` 로 감사로그 기록.

---

## 🗂 신규 추가: 직원 파일(EmployeeFiles) 버저닝 구조

**파일:**  
- `backend/app/models/employee_file.py`  
- `backend/app/schemas/employee_file.py`  
- `backend/app/routers/employee_files.py`  

**개요:**  
- 직원 관련 첨부 파일(계약서, 평가서, 증명서 등) 버저닝 관리.  
- DB에는 메타정보만 저장, 실제 파일은 NAS 경로(`/uploads/hr_files/`) 보관.  
- HRADMIN 이상 권한만 변경 가능.

**주요 필드:**  
| 필드 | 설명 |
|------|------|
| `employee_id` | FK → employees.id |
| `file_name` | 원본 파일명 |
| `file_path` | NAS 내 저장 경로 |
| `category` | 파일 분류 (계약, 평가, 증명 등) |
| `version_no`, `is_latest` | 버전 제어 |
| `uploaded_by` | 업로더 |
| `created_at` | 업로드 일시 |

**정책:**  
- Append-only, 동일 파일명은 version_no 증가.  
- 최신 파일만 `is_latest=True`.  
- `/api/employee-files/{emp_id}` → 목록 조회, 업로드, 다운로드 제공.

---

## 🔐 권한 업데이트

| 구분 | 권한 | 설명 |
|------|------|------|
| HR 모듈 관리 | `ADMIN↑` | 직원, 계약, 인사이력 관리 가능 |
| 파일 업로드/삭제 | `HRADMIN↑` | EmployeeFiles 작성/삭제 가능 |
| 감사/열람 | `AUDITOR` | 모든 HR 데이터 열람 전용 |

---

## 🧱 구조 반영 (structure.json)

```json
"app/models/employee_file.py": { "desc": "직원 파일 모델 (버저닝)", "optional": false },
"app/schemas/employee_file.py": { "desc": "직원 파일 스키마", "optional": false },
"app/routers/employee_files.py": { "desc": "직원 파일 관리 API (버저닝)", "optional": false }
```

---

## 📦 배포/적용 체크리스트

1️⃣ `alembic revision --autogenerate -m "v2.5 HR Contracts & EmployeeFiles versioning"`  
2️⃣ `alembic upgrade head`  
3️⃣ NAS 경로 `/uploads/hr_files` 생성 (권한 755)  
4️⃣ 백엔드 재시작 (`systemctl restart hotel-backend` or uvicorn reload)  
5️⃣ 테스트 명령으로 검증:

```bash
# 신규 계약 등록
curl -X POST -H "X-Internal-Token: dev-admin-token"   -H "Content-Type: application/json"   -d '{"employee_id":1,"contract_type":"정규직","start_date":"2025-01-01","salary":3500000}'   http://127.0.0.1:8000/api/contracts | jq .

# 계약 이력 조회
curl -H "X-Internal-Token: dev-admin-token"   http://127.0.0.1:8000/api/contracts/history/1 | jq .

# 파일 업로드 테스트
curl -X POST -H "X-Internal-Token: dev-admin-token"   -F "employee_id=1" -F "file=@/tmp/contract_v2.pdf"   http://127.0.0.1:8000/api/employee-files/upload | jq .
```

---

**작성일:** 2025‑10‑13  
**작성자:** GPT‑5 (Hotel System FullStack SSOT — Patch v2.5)
