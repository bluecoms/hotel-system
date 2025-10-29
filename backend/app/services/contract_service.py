# -*- coding: utf-8 -*-
# =============================================================================
# File      : app/services/contract_service.py
# Version   : 2025.11-10 · v1.0 (SSOT Final · Safe Service Layer)
# Purpose   : Hotel Admin — 직원 계약 관리 Service 계층 (EmployeeContracts)
# -----------------------------------------------------------------------------
# 목적:
#   • 라우터(app/routers/contracts.py)에서 사용하는 계약 도메인 로직을 Service로 분리
#   • 트랜잭션/검증/정합성(append-only, is_latest) 보장
#   • Python 3.8/SQLAlchemy 1.4+ 호환, SSOT 규격 유지
# -----------------------------------------------------------------------------
# 제공 기능:
#   1) list_contracts(...)          → 직원 기준 계약 목록 (LEFT JOIN)
#   2) create_contract(...)         → 신규 계약 생성 (append-only)
#   3) contract_history(...)        → 직원별 계약 이력 (최신 우선)
#   4) contract_versions(...)       → 특정 계약 ID 기준 전체 버전
#   5) terminate_contract(...)      → 계약 종료 (논리 상태)
#   6) activate_contract(...)       → 계약 확정 (is_latest 동기화 + 직원 상태 반영)
# -----------------------------------------------------------------------------
# 설계 원칙:
#   • 모든 쓰기 연산은 명시적으로 commit/refresh
#   • append-only 원칙: 기존 최신 계약은 is_latest=False 처리
#   • 직원(Employee) 상태(contract_status/start/end)와 계약 상태 동기화
#   • 예외는 HTTPException을 라우터에서 처리할 수 있도록 ValueError/LookupError로 전달 권장
#     (원한다면 라우터에서 HTTPException으로 변환)
# -----------------------------------------------------------------------------
# 의존 모델/스키마:
#   • app/models/employee.py           → Employee
#   • app/models/contract.py           → EmployeeContract
#   • app/models/master_department.py  → MasterDepartment (dept_name 합성용)
#   • app/schemas/contract.py          → ContractOut (라우터에서 직렬화 사용)
# =============================================================================

from __future__ import annotations
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.employee import Employee
from app.models.contract import EmployeeContract
from app.models.master_department import MasterDepartment


# -----------------------------------------------------------------------------
# 내부 유틸: 안전한 날짜 변환
# -----------------------------------------------------------------------------
def _safe_date(v: Any) -> Optional[date]:
    """
    문자열/날짜 → date 로 안전 변환.
    허용 포맷: YYYY-MM-DD (앞 10자).
    잘못된 값은 None.
    """
    if not v:
        return None
    if isinstance(v, date):
        return v
    try:
        return datetime.strptime(str(v)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


# -----------------------------------------------------------------------------
# 1) 목록 조회 (직원 기준 LEFT JOIN)
# -----------------------------------------------------------------------------
def list_contracts(
    db: Session,
    *,
    property_code: str,
    q: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    size: int = 20,
) -> Tuple[int, List[Dict[str, Any]]]:
    """
    직원 기준 계약 목록 조회 (LEFT JOIN)
      - Employee ← EmployeeContract (LEFT)
      - Employee.dept(코드) = MasterDepartment.dept_code AND property_code 동일
      - 검색(q): name/emp_no/dept_name 부분일치
      - 상태(status): none/active/terminated/draft
    반환:
      (total, items[list[dict]])
    """
    qset = (
        db.query(Employee, EmployeeContract, MasterDepartment.dept_name)
        .outerjoin(EmployeeContract, Employee.id == EmployeeContract.employee_id)
        .outerjoin(
            MasterDepartment,
            and_(
                Employee.dept == MasterDepartment.dept_code,
                Employee.property_code == MasterDepartment.property_code,
            ),
        )
        .filter(Employee.property_code == property_code)
    )

    if q:
        like = f"%{q}%"
        qset = qset.filter(
            or_(
                Employee.name.ilike(like),
                Employee.emp_no.ilike(like),
                MasterDepartment.dept_name.ilike(like),
            )
        )

    if status:
        s = (status or "").strip().lower()
        if s == "none":
            qset = qset.filter(EmployeeContract.id.is_(None))
        elif s in {"active", "terminated", "draft"}:
            qset = qset.filter(EmployeeContract.status == s)

    total = qset.count()
    rows = (
        qset.order_by(Employee.emp_no.asc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    items: List[Dict[str, Any]] = []
    for emp, c, dept_name in rows:
        items.append(
            {
                "employee_id": emp.id,
                "emp_no": emp.emp_no,
                "emp_name": emp.name,
                "dept_name": dept_name or "-",
                "title_name": getattr(emp, "title_name", None),
                "property_code": emp.property_code,
                "contract_id": c.id if c else None,
                "contract_type": c.contract_type if c else None,
                "contract_start": c.start_date if c else None,
                "contract_end": c.end_date if c else None,
                "salary": c.salary if c else None,
                "status": (c.status if c else "none"),
            }
        )
    return int(total), items


# -----------------------------------------------------------------------------
# 2) 신규 계약 생성 (Append-only)
# -----------------------------------------------------------------------------
def create_contract(
    db: Session,
    *,
    employee_id: int,
    contract_type: str,
    start_date: Optional[Any],
    end_date: Optional[Any],
    pay_type: Optional[str] = None,
    salary: Optional[Any] = None,
    currency: Optional[str] = "KRW",
    memo: Optional[str] = "",
    file_path: Optional[str] = "",
    contract_no: Optional[str] = "",
    meta: Optional[Dict[str, Any]] = None,
) -> EmployeeContract:
    """
    신규 계약 생성 (Append-only)
    - 필수: employee_id, contract_type
    - append-only: 기존 최신(is_latest=True) 계약은 is_latest=False로 내리고, 새 계약을 ver+1 로 생성
    """
    # 직원 검증
    emp: Optional[Employee] = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise LookupError("employee not found")

    # 최신 계약 롤다운 (is_latest=False)
    latest: Optional[EmployeeContract] = (
        db.query(EmployeeContract)
        .filter(EmployeeContract.employee_id == employee_id, EmployeeContract.is_latest.is_(True))
        .first()
    )
    version_no = (latest.version_no + 1) if latest else 1
    if latest:
        latest.is_latest = False

    rec = EmployeeContract(
        employee_id=employee_id,
        contract_type=(contract_type or "").strip().upper(),
        start_date=_safe_date(start_date),
        end_date=_safe_date(end_date),
        pay_type=(pay_type or "MONTHLY").strip().upper(),
        salary=salary,
        currency=(currency or "KRW").strip().upper(),
        memo=memo or "",
        file_path=file_path or "",
        contract_no=contract_no or "",
        meta=meta,
        version_no=version_no,
        is_latest=True,
        status="draft",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


# -----------------------------------------------------------------------------
# 3) 직원별 계약 이력
# -----------------------------------------------------------------------------
def contract_history(db: Session, *, employee_id: int) -> List[EmployeeContract]:
    """
    직원별 계약 이력 (최신 버전 우선)
    """
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise LookupError("employee not found")
    rows = (
        db.query(EmployeeContract)
        .filter(EmployeeContract.employee_id == employee_id)
        .order_by(EmployeeContract.version_no.desc())
        .all()
    )
    return rows


# -----------------------------------------------------------------------------
# 4) 특정 계약 ID 기준 전체 버전
# -----------------------------------------------------------------------------
def contract_versions(db: Session, *, contract_id: int) -> List[EmployeeContract]:
    """
    특정 계약 ID(anchor)와 동일한 employee_id 의 전체 버전 목록
    """
    anchor = db.query(EmployeeContract).filter(EmployeeContract.id == contract_id).first()
    if not anchor:
        raise LookupError("contract not found")
    rows = (
        db.query(EmployeeContract)
        .filter(EmployeeContract.employee_id == anchor.employee_id)
        .order_by(EmployeeContract.version_no.desc())
        .all()
    )
    return rows


# -----------------------------------------------------------------------------
# 5) 계약 종료 (논리 상태)
# -----------------------------------------------------------------------------
def terminate_contract(db: Session, *, contract_id: int) -> EmployeeContract:
    """
    계약 종료 → 상태 terminated 로 전환
    직원 상태도 함께 terminated, contract_end는 오늘 날짜로 세팅
    """
    rec: Optional[EmployeeContract] = (
        db.query(EmployeeContract).filter(EmployeeContract.id == contract_id).first()
    )
    if not rec:
        raise LookupError("contract not found")

    rec.status = "terminated"
    rec.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(rec)

    emp: Optional[Employee] = db.query(Employee).filter(Employee.id == rec.employee_id).first()
    if emp:
        emp.contract_status = "terminated"
        emp.contract_end = datetime.utcnow().date()
        db.commit()
    return rec


# -----------------------------------------------------------------------------
# 6) 계약 확정 (인쇄 완료 후 활성화)
# -----------------------------------------------------------------------------
def activate_contract(db: Session, *, contract_id: int) -> EmployeeContract:
    """
    계약 확정 → status=active, is_latest=True
    동일 직원의 다른 계약은 모두 is_latest=False
    직원(Employee)의 contract_status/start/end 를 계약과 동기화
    """
    rec: Optional[EmployeeContract] = (
        db.query(EmployeeContract).filter(EmployeeContract.id == contract_id).first()
    )
    if not rec:
        raise LookupError("contract not found")

    # 동일 직원 기존 계약 최신 플래그 해제
    db.query(EmployeeContract).filter(
        EmployeeContract.employee_id == rec.employee_id
    ).update({"is_latest": False})

    rec.status = "active"
    rec.is_latest = True
    rec.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(rec)

    emp: Optional[Employee] = db.query(Employee).filter(Employee.id == rec.employee_id).first()
    if emp:
        emp.contract_status = "active"
        emp.contract_start = rec.start_date
        emp.contract_end = rec.end_date
        db.commit()

    return rec


# -----------------------------------------------------------------------------
# 헬퍼: 도메인 dict 직렬화 (라우터/서비스 공용)
# -----------------------------------------------------------------------------
def serialize_contract(rec: EmployeeContract) -> Dict[str, Any]:
    """
    EmployeeContract ORM → dict (라우터 응답 변환용)
    (라우터에서 Pydantic 모델을 이미 사용한다면 생략 가능)
    """
    if rec is None:
        return {}
    return {
        "id": rec.id,
        "employee_id": rec.employee_id,
        "contract_type": rec.contract_type,
        "start_date": rec.start_date,
        "end_date": rec.end_date,
        "pay_type": rec.pay_type,
        "salary": rec.salary,
        "currency": rec.currency,
        "memo": rec.memo,
        "file_path": rec.file_path,
        "contract_no": rec.contract_no,
        "meta": rec.meta,
        "version_no": rec.version_no,
        "is_latest": rec.is_latest,
        "status": rec.status,
        "created_at": rec.created_at,
        "updated_at": rec.updated_at,
    }
