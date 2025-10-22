# app/routers/hr_bridge.py
# -*- coding: utf-8 -*-
"""
Hotel Admin — HR Bridge Router (v3.5.2, 2025-10-18)
────────────────────────────────────────────
변경사항:
  ✅ MasterTitle 반영 (titles → master_titles)
  ✅ HR 모델 로드 실패 오류 해소
────────────────────────────────────────────
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List
from datetime import date, datetime
from fastapi import APIRouter, Depends, Query, HTTPException, Form
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, asc, desc, text, func
from app.db.session import get_db
from app.core.auth import require_user

# ─────────────────────────────────────────────
# ORM 모델 로드
# ─────────────────────────────────────────────
try:
    from app.models import (
        Employee,
        EmployeeContract,
        MasterDepartment as Department,
        User,
        MasterTitle as Title,
    )
except Exception as e:
    Employee = EmployeeContract = Department = User = Title = None  # type: ignore
    _MODEL_ERR = e
else:
    _MODEL_ERR = None


def _assert_models(*names: str):
    if _MODEL_ERR:
        raise HTTPException(status_code=500, detail=f"HR 모델 로드 실패: {_MODEL_ERR}")
    missing = [n for n in names if globals().get(n) is None]
    if missing:
        raise HTTPException(status_code=500, detail=f"모델 누락: {', '.join(missing)}")


# ─────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────
router = APIRouter(
    prefix="/api/hr",
    tags=["hr"],
    dependencies=[Depends(require_user)],
)

# ─────────────────────────────────────────────
# 직책 코드 → 이름 매핑
# ─────────────────────────────────────────────
def _load_titles_map(db: Session) -> Dict[str, str]:
    try:
        rows = db.execute(text("SELECT code, name FROM master_titles")).mappings().all()  # ✅ 변경
        return {(r["code"] or "").upper(): r["name"] or "" for r in rows}
    except Exception:
        return {}

# ─────────────────────────────────────────────
# 직원 목록
# ─────────────────────────────────────────────
@router.get("/employees", summary="직원 목록(+최신 계약·부서/직책 명칭 포함)")
def hr_list_employees(
    q: Optional[str] = Query(None),
    dept: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    sort: str = Query(""),
    db: Session = Depends(get_db),
):
    _assert_models("Employee", "EmployeeContract", "Department")
    titles_map = _load_titles_map(db)

    qset = (
        db.query(
            Employee,
            EmployeeContract,
            Department.dept_name.label("dept_name"),
            text("NULL AS title_name"),
        )
        .outerjoin(
            EmployeeContract,
            and_(
                EmployeeContract.employee_id == Employee.id,
                EmployeeContract.is_latest.is_(True),
            ),
        )
        .outerjoin(Department, Department.dept_code == Employee.dept)
        .filter(Employee.deleted_at.is_(None))
    )

    if q:
        like = f"%{q}%"
        qset = qset.filter(or_(
            Employee.emp_no.ilike(like),
            Employee.name.ilike(like),
            Employee.dept.ilike(like),
            Employee.title.ilike(like),
            Employee.email.ilike(like),
        ))
    if dept:
        qset = qset.filter(Employee.dept == dept)
    if status == "active":
        qset = qset.filter(Employee.leave_date.is_(None))
    elif status == "leaved":
        qset = qset.filter(Employee.leave_date.is_not(None))

    total = qset.count()
    rows = qset.order_by(desc(Employee.id)).offset((page - 1) * size).limit(size).all()

    today = date.today()
    items: List[Dict[str, Any]] = []
    for e, c, dept_name, _ in rows:
        cstat = "active" if (c and c.end_date and c.end_date >= today) else (
            "expired" if (c and c.end_date) else "none"
        )
        title_name = titles_map.get((e.title or "").upper()) or None
        items.append({
            "id": e.id,
            "emp_no": e.emp_no,
            "name": e.name,
            "dept": e.dept,
            "dept_name": dept_name,
            "title": e.title,
            "title_name": title_name,
            "email": e.email,
            "hire_date": str(e.hire_date) if e.hire_date else None,
            "leave_date": str(e.leave_date) if e.leave_date else None,
            "contract_start": str(c.start_date) if c and c.start_date else None,
            "contract_end": str(c.end_date) if c and c.end_date else None,
            "contract_status": cstat,
        })
    return {"ok": True, "items": items, "total": total, "page": page, "size": size}

# ─────────────────────────────────────────────
# 헬스체크
# ─────────────────────────────────────────────
@router.get("/_ping")
def hr_bridge_ping():
    if _MODEL_ERR:
        return {"ok": False, "error": str(_MODEL_ERR)}
    return {"ok": True, "bridge": "hr"}
