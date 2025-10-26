# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/routers/contracts.py
# Version   : 2025.10-31 Final Stable (v3.9.1 · 3.8 Safe OR · SSOT 규격 · Syntax Fix)
# Purpose   : Hotel Admin — 직원 계약 관리 API (EmployeeContracts)
# ----------------------------------------------------------------------------
# 목적:
#   • 직원(Employee)별 계약 생성/조회/이력/확정/종료 관리
#   • 계약 확정 시 Employee 테이블(contract_status/start/end) 자동 반영
#   • 계약이 없는 직원도 "미계약" 상태로 목록에 표시 (LEFT JOIN)
#   • Property(지점 코드) 단위 필터 지원
# ----------------------------------------------------------------------------
# 주요 개선사항 (v3.9.1)
#   ✅ Python 3.8 호환: 검색 필터에서 `|` → `or_(...)`로 전환
#   ✅ dept_name 접근 오류 수정 (Employee.dept ↔ MasterDepartment.dept_code JOIN)
#   ✅ LEFT JOIN 안정화 (Employee ← EmployeeContract ← MasterDepartment)
#   ✅ 문법 오류(SyntaxError) 수정: JOIN 조건 사이 콤마 누락 보완
#   ✅ SSOT 원칙 강화 — Employee는 dept(코드)만 보유, 부서명은 MasterDepartment 참조
# ----------------------------------------------------------------------------
# 엔드포인트:
#   • GET    /api/contracts                     → 계약 목록 조회 (LEFT JOIN)
#   • POST   /api/contracts                     → 신규 계약 생성 (Append-only)
#   • GET    /api/contracts/history/{emp_id}    → 직원별 계약 이력 조회
#   • GET    /api/contracts/{id}/versions       → 특정 계약 전체 버전 조회
#   • POST   /api/contracts/terminate/{id}      → 계약 종료(논리 상태)
#   • PATCH  /api/contracts/{id}/activate       → 계약 확정(인쇄 후 활성화)
# ============================================================================

from __future__ import annotations
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.audit import write_audit
from app.core.auth import require_roles, require_user
from app.db.session import get_db
from app.models.contract import EmployeeContract
from app.models.employee import Employee
from app.models.master_department import MasterDepartment
from app.schemas.contract import ContractOut

# ─────────────────────────────────────────────
# 내부 유틸: 안전한 날짜 변환
# ─────────────────────────────────────────────
def _safe_date(v: Any) -> Optional[date]:
    """문자열 → datetime.date 변환 (에러 안전)"""
    if not v:
        return None
    if isinstance(v, date):
        return v
    try:
        return datetime.strptime(str(v)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


# ─────────────────────────────────────────────
# Router 설정
# ─────────────────────────────────────────────
router = APIRouter(
    prefix="/api/contracts",
    tags=["contracts"],
    dependencies=[Depends(require_user)],
)


# ============================================================================
# 1️⃣ 계약 목록 조회 (Employee 기준 LEFT JOIN)
#   - Employee ← EmployeeContract (LEFT)
#   - Employee.dept (코드) → MasterDepartment.dept_code (LEFT) 로 부서명 합성
#   - 계약이 없는 직원도 status='none' 으로 노출
# ============================================================================
@router.get("", dependencies=[Depends(require_roles(["ADMIN", "SUPERADMIN"]))])
def list_contracts(
    property_code: str = Query(..., description="지점 코드 (예: MOP)"),
    q: Optional[str] = Query(None, description="검색어 (이름/사번/부서명 등)"),
    status: Optional[str] = Query(None, description="계약 상태 필터 (none/active/terminated)"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    직원 기준 계약 목록 조회
    --------------------------------------------------------------------------
    LEFT JOIN
      - Employee.id = EmployeeContract.employee_id
      - Employee.dept(코드) = MasterDepartment.dept_code AND property_code 동치
    검색/필터
      - q: name/emp_no/dept_name 부분일치 검색
      - status: none → 계약레코드가 없는 직원만, 그 외(active/terminated) → 계약 상태 필터
    --------------------------------------------------------------------------
    """
    qset = (
        db.query(Employee, EmployeeContract, MasterDepartment.dept_name)
        .outerjoin(EmployeeContract, Employee.id == EmployeeContract.employee_id)
        .outerjoin(
            MasterDepartment,
            and_(
                Employee.dept == MasterDepartment.dept_code,            # ✅ 콤마 누락 보완
                Employee.property_code == MasterDepartment.property_code,
            ),
        )
        .filter(Employee.property_code == property_code)
    )

    # 검색어 필터 (3.8 Safe: or_)
    if q:
        like = f"%{q}%"
        qset = qset.filter(
            or_(
                Employee.name.ilike(like),
                Employee.emp_no.ilike(like),
                MasterDepartment.dept_name.ilike(like),
            )
        )

    # 상태 필터
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

    # 결과 구성
    items: List[Dict[str, Any]] = []
    for emp, c, dept_name in rows:
        items.append(
            {
                # 직원 정보
                "employee_id": emp.id,
                "emp_no": emp.emp_no,
                "emp_name": emp.name,
                "dept_name": dept_name or "-",
                "title_name": getattr(emp, "title_name", None),
                "property_code": emp.property_code,
                # 계약 정보 (없으면 None)
                "contract_id": c.id if c else None,
                "contract_type": c.contract_type if c else None,
                "contract_start": c.start_date if c else None,
                "contract_end": c.end_date if c else None,
                "salary": c.salary if c else None,
                "status": (c.status if c else "none"),
            }
        )

    return {"ok": True, "items": items, "page": page, "size": size, "total": total}


# ============================================================================
# 2️⃣ 계약 생성 (Append-only)
# ============================================================================
@router.post("", dependencies=[Depends(require_roles(["HRADMIN", "SUPERADMIN"]))])
def create_contract(
    body: Dict[str, Any] = Body(..., description="계약 생성 페이로드"),
    db: Session = Depends(get_db),
):
    """신규 계약 생성 (Append-only)"""
    employee_id = body.get("employee_id")
    contract_type = (body.get("contract_type") or "").strip().upper()
    if not employee_id or not contract_type:
        raise HTTPException(status_code=422, detail="employee_id, contract_type is required")

    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="employee not found")

    # 기존 최신 계약 비활성화
    latest = (
        db.query(EmployeeContract)
        .filter(EmployeeContract.employee_id == employee_id, EmployeeContract.is_latest.is_(True))
        .first()
    )
    version_no = (latest.version_no + 1) if latest else 1
    if latest:
        latest.is_latest = False

    rec = EmployeeContract(
        employee_id=employee_id,
        contract_type=contract_type,
        start_date=_safe_date(body.get("start_date")),
        end_date=_safe_date(body.get("end_date")),
        pay_type=body.get("pay_type") or ("MONTHLY" if contract_type == "MONTHLY" else "HOURLY"),
        salary=body.get("salary"),
        currency=body.get("currency") or "KRW",
        memo=body.get("memo") or "",
        file_path=body.get("file_path") or "",
        contract_no=body.get("contract_no") or "",
        meta=body.get("meta"),
        version_no=version_no,
        is_latest=True,
        status="draft",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    try:
        write_audit(db, "system", "contract.create", f"emp={emp.id}", {"ver": version_no})
    except Exception:
        pass

    return {"ok": True, "contract": ContractOut.model_validate(rec).model_dump()}


# ============================================================================
# 3️⃣ 계약 이력 (직원별)
# ============================================================================
@router.get("/history/{employee_id}", dependencies=[Depends(require_roles(["ADMIN", "SUPERADMIN"]))])
def contract_history(employee_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """직원별 계약 이력 조회"""
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="employee not found")

    rows = (
        db.query(EmployeeContract)
        .filter(EmployeeContract.employee_id == employee_id)
        .order_by(EmployeeContract.version_no.desc())
        .all()
    )
    items = [ContractOut.model_validate(r).model_dump() for r in rows]
    return {"employee_id": employee_id, "items": items, "total": len(items)}


# ============================================================================
# 4️⃣ 계약 버전 목록 (계약 ID 기준)
# ============================================================================
@router.get("/{contract_id}/versions", dependencies=[Depends(require_roles(["ADMIN", "SUPERADMIN"]))])
def contract_versions(contract_id: int, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """특정 계약 ID 기준 전체 버전 조회"""
    anchor = db.query(EmployeeContract).filter(EmployeeContract.id == contract_id).first()
    if not anchor:
        raise HTTPException(status_code=404, detail="contract not found")

    rows = (
        db.query(EmployeeContract)
        .filter(EmployeeContract.employee_id == anchor.employee_id)
        .order_by(EmployeeContract.version_no.desc())
        .all()
    )
    return [ContractOut.model_validate(r).model_dump() for r in rows]


# ============================================================================
# 5️⃣ 계약 종료 (논리적 종료 처리)
# ============================================================================
@router.post("/terminate/{contract_id}", dependencies=[Depends(require_roles(["HRADMIN", "SUPERADMIN"]))])
def terminate_contract(contract_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """계약 종료 처리"""
    rec = db.query(EmployeeContract).filter(EmployeeContract.id == contract_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="contract not found")

    rec.status = "terminated"
    rec.updated_at = datetime.utcnow()
    db.commit()

    # 직원 상태 반영
    emp = db.query(Employee).filter(Employee.id == rec.employee_id).first()
    if emp:
        emp.contract_status = "terminated"
        emp.contract_end = datetime.utcnow().date()
        db.commit()

    try:
        write_audit(db, "system", "contract.terminate", f"cid={contract_id}")
    except Exception:
        pass

    return {"ok": True, "terminated": contract_id}


# ============================================================================
# 6️⃣ 계약 확정 (인쇄 완료 후 활성화)
# ============================================================================
@router.patch("/{contract_id}/activate", dependencies=[Depends(require_roles(["HRADMIN", "SUPERADMIN"]))])
def activate_contract(contract_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """계약 확정 → active 상태로 전환 + Employee 상태 동기화"""
    rec = db.query(EmployeeContract).filter(EmployeeContract.id == contract_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="contract not found")

    # 동일 직원 기존 계약 최신 해제
    db.query(EmployeeContract).filter(
        EmployeeContract.employee_id == rec.employee_id
    ).update({"is_latest": False})

    rec.status = "active"
    rec.is_latest = True
    rec.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(rec)

    # 직원 계약 상태 동기화
    emp = db.query(Employee).filter(Employee.id == rec.employee_id).first()
    if emp:
        emp.contract_status = "active"
        emp.contract_start = rec.start_date
        emp.contract_end = rec.end_date
        db.commit()

    try:
        write_audit(db, "system", "contract.activate", f"cid={contract_id}")
    except Exception:
        pass

    return {
        "ok": True,
        "id": rec.id,
        "employee_id": rec.employee_id,
        "status": rec.status,
        "is_latest": rec.is_latest,
    }
