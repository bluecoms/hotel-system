# ============================================================================
# File      : app/routers/master_departments.py
# Version   : 2025.10-22 v1.1 (Add Leader Assign API · SSOT Stable)
# Purpose   : Hotel Admin — Master Departments Router (/api/master/departments)
# ----------------------------------------------------------------------------
# 목적:
#   • 부서(Departments) 기준정보 CRUD + 순서 변경 + 옵션 목록 관리
#   • ✅ 부서별 팀장(leader_emp_id) 지정 / 변경 / 해제 기능 추가
# ----------------------------------------------------------------------------
# 주요 변경사항(v1.1)
#   ✅ PUT /api/master/departments/{dept_id}/leader  추가
#   ✅ employees.id 참조(FK) 기반 팀장 지정
#   ✅ 기존 기능 CRUD / reorder / options 그대로 유지
# ============================================================================
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from app.db.session import get_db
from app.models import MasterDepartment, Employee
from app.schemas import (
    MasterDepartmentIn,
    MasterDepartmentOut,
    MasterDepartmentOption,
    MasterDepartmentReorderBody,
)
from app.core.auth import require_roles, require_token_local

# ─────────────────────────────────────────────
# Router 선언
# ─────────────────────────────────────────────
router = APIRouter(
    prefix="/api/master/departments",
    tags=["master-departments"],
    dependencies=[
        Depends(require_token_local),
        Depends(require_roles(["ADMIN", "SUPERADMIN"]))
    ],
)

# ─────────────────────────────────────────────
# 1️⃣ 목록 조회
# ─────────────────────────────────────────────
@router.get("", response_model=dict, summary="부서 목록 조회")
def list_departments(
    db: Session = Depends(get_db),
    property_code: str = Query("MOP"),
):
    """부서 목록 조회 — 기본 정보 + 팀장 ID 포함"""
    items = (
        db.query(MasterDepartment)
        .filter(MasterDepartment.property_code == property_code)
        .order_by(MasterDepartment.order_no.asc().nulls_last(), MasterDepartment.dept_name.asc())
        .all()
    )
    result = []
    for d in items:
        leader_name = None
        if d.leader_emp_id:
            emp = db.query(Employee).get(d.leader_emp_id)
            if emp:
                leader_name = emp.name
        data = MasterDepartmentOut.model_validate(d).model_dump()
        data["leader_emp_id"] = d.leader_emp_id
        data["leader_name"] = leader_name
        result.append(data)
    return {"ok": True, "items": result}

# ─────────────────────────────────────────────
# 2️⃣ 부서 생성
# ─────────────────────────────────────────────
@router.post("", response_model=MasterDepartmentOut, summary="부서 생성")
def create_department(body: MasterDepartmentIn, db: Session = Depends(get_db)):
    dup = db.query(MasterDepartment).filter(
        MasterDepartment.property_code == body.property_code,
        MasterDepartment.dept_code == body.dept_code,
    ).first()
    if dup:
        raise HTTPException(status_code=409, detail="이미 존재하는 부서 코드입니다.")
    row = MasterDepartment(**body.dict())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

# ─────────────────────────────────────────────
# 3️⃣ 부서 수정
# ─────────────────────────────────────────────
@router.patch("/{dept_id}", response_model=MasterDepartmentOut, summary="부서 수정")
def update_department(dept_id: int, body: MasterDepartmentIn, db: Session = Depends(get_db)):
    row = db.query(MasterDepartment).get(dept_id)
    if not row:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다.")
    for k, v in body.dict().items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row

# ─────────────────────────────────────────────
# 4️⃣ 부서 삭제
# ─────────────────────────────────────────────
@router.delete("/{dept_id}", summary="부서 삭제")
def delete_department(dept_id: int, db: Session = Depends(get_db)):
    row = db.query(MasterDepartment).get(dept_id)
    if not row:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다.")
    db.delete(row)
    db.commit()
    return {"ok": True}

# ─────────────────────────────────────────────
# 5️⃣ 순서 재정렬
# ─────────────────────────────────────────────
@router.put("/reorder", summary="부서 순서 재정렬", response_model=dict)
def reorder_departments(body: MasterDepartmentReorderBody, db: Session = Depends(get_db)):
    for item in body.items:
        db.execute(
            text("UPDATE departments SET order_no = :o WHERE id = :i"),
            {"i": item.id, "o": item.order_no},
        )
    db.commit()
    return {"ok": True, "count": len(body.items)}

# ─────────────────────────────────────────────
# 6️⃣ 옵션 목록 (selectbox용)
# ─────────────────────────────────────────────
@router.get("/options", response_model=List[MasterDepartmentOption], summary="부서 옵션 목록")
def department_options(
    property_code: str = Query("MOP"),
    only_active: int = Query(1),
    db: Session = Depends(get_db),
):
    query = db.query(MasterDepartment).filter(MasterDepartment.property_code == property_code)
    if int(only_active or 0) == 1:
        query = query.filter(MasterDepartment.is_active.is_(True))
    rows = query.order_by(MasterDepartment.order_no.asc().nulls_last(), MasterDepartment.dept_name.asc()).all()
    return [MasterDepartmentOption(title=r.dept_name, value=r.dept_code) for r in rows]

# ─────────────────────────────────────────────
# 7️⃣ 팀장 지정 / 변경 / 해제
# ─────────────────────────────────────────────
@router.put("/{dept_id}/leader", summary="부서 팀장 지정/변경/해제", response_model=dict)
def assign_department_leader(
    dept_id: int,
    body: dict = Body(..., example={"leader_emp_id": 1}),
    db: Session = Depends(get_db),
):
    """부서별 팀장(leader_emp_id) 지정/변경/해제"""
    dept = db.query(MasterDepartment).get(dept_id)
    if not dept:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다.")

    leader_id: Optional[int] = body.get("leader_emp_id")
    if leader_id:
        emp = db.query(Employee).get(leader_id)
        if not emp:
            raise HTTPException(status_code=404, detail="지정할 직원을 찾을 수 없습니다.")

    dept.leader_emp_id = leader_id  # None이면 해제
    db.commit()
    db.refresh(dept)

    return {
        "ok": True,
        "dept_id": dept.id,
        "leader_emp_id": dept.leader_emp_id,
    }
