# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/routers/master_departments.py
# Version   : 2025.10-31 · v1.3 (Prefix/Imports Final · SSOT Stable)
# Purpose   : Hotel Admin — Master Departments Router (/api/master/departments)
# ----------------------------------------------------------------------------
# 목적:
#   • 부서(Departments) 기준정보 CRUD + 순서 변경 + 옵션 목록 관리
#   • ✅ 부서별 팀장(leader_emp_id) 지정 / 변경 / 해제 기능 포함
#   • ✅ SQLite / PostgreSQL 호환 보장
# ----------------------------------------------------------------------------
# 변경사항 (v1.3)
#   ✅ prefix 구조 정비 (/master/departments)
#   ✅ schema import 정합성 (MasterDepartmentIn/Out/Option)
#   ✅ reorder / leader API 주석 보강
#   ✅ SSOT 주석 구조 일원화
# ----------------------------------------------------------------------------
# Naming 규칙 (SSOT 고정)
#   • Model  : app/models/master_department.py      → 단수
#   • Schema : app/schemas/master_departments.py    → 복수
#   • Router : app/routers/master_departments.py    → 복수
# ============================================================================

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.models.master_department import MasterDepartment
from app.models.employee import Employee
from app.schemas.master_department import (
    MasterDepartmentIn,
    MasterDepartmentOut,
    MasterDepartmentOption,
    MasterDepartmentReorderBody,
)
from app.core.auth import require_roles, require_token_local

# ============================================================================
# Router 선언
# ============================================================================
router = APIRouter(
    prefix="/api/master/departments",  # ✅ /api/master/departments 로 정확히 매핑
    tags=["master-departments"],
    dependencies=[
        Depends(require_token_local),
        Depends(require_roles(["ADMIN", "SUPERADMIN"])),
    ],
)

# ============================================================================
# 1️⃣ 목록 조회
# ============================================================================
@router.get("", response_model=dict, summary="부서 목록 조회")
def list_departments(
    db: Session = Depends(get_db),
    property_code: str = Query("MOP"),
):
    """부서 목록 조회 — 기본 정보 + 팀장 이름 포함"""
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
            emp = db.get(Employee, d.leader_emp_id)
            if emp:
                leader_name = emp.name
        data = MasterDepartmentOut.model_validate(d).model_dump()
        data["leader_emp_id"] = d.leader_emp_id
        data["leader_name"] = leader_name
        result.append(data)

    return {"ok": True, "items": result}

# ============================================================================
# 2️⃣ 부서 생성
# ============================================================================
@router.post("", response_model=MasterDepartmentOut, summary="부서 생성")
def create_department(body: MasterDepartmentIn, db: Session = Depends(get_db)):
    """부서 신규 생성"""
    dup = (
        db.query(MasterDepartment)
        .filter(
            MasterDepartment.property_code == body.property_code,
            MasterDepartment.dept_code == body.dept_code,
        )
        .first()
    )
    if dup:
        raise HTTPException(status_code=409, detail="이미 존재하는 부서 코드입니다.")
    row = MasterDepartment(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

# ============================================================================
# 3️⃣ 부서 수정
# ============================================================================
@router.patch("/{dept_id}", response_model=MasterDepartmentOut, summary="부서 수정")
def update_department(dept_id: int, body: MasterDepartmentIn, db: Session = Depends(get_db)):
    """부서 정보 수정"""
    row = db.get(MasterDepartment, dept_id)
    if not row:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다.")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row

# ============================================================================
# 4️⃣ 부서 삭제
# ============================================================================
@router.delete("/{dept_id}", summary="부서 삭제")
def delete_department(dept_id: int, db: Session = Depends(get_db)):
    """부서 삭제"""
    row = db.get(MasterDepartment, dept_id)
    if not row:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다.")
    db.delete(row)
    db.commit()
    return {"ok": True, "deleted": dept_id}

# ============================================================================
# 5️⃣ 순서 재정렬
# ============================================================================
@router.put("/reorder", summary="부서 순서 재정렬", response_model=dict)
def reorder_departments(body: MasterDepartmentReorderBody, db: Session = Depends(get_db)):
    """부서 일괄 순서 재정렬"""
    for item in body.items:
        db.execute(
            text("UPDATE departments SET order_no = :o WHERE id = :i"),
            {"i": item.id, "o": item.order_no},
        )
    db.commit()
    return {"ok": True, "count": len(body.items)}

# ============================================================================
# 6️⃣ 옵션 목록 (v-select용)
# ============================================================================
@router.get("/options", response_model=List[MasterDepartmentOption], summary="부서 옵션 목록 (v-select용)")
def department_options(
    property_code: str = Query("MOP"),
    only_active: int = Query(1, description="1=활성 부서만, 0=전체"),
    db: Session = Depends(get_db),
):
    """부서 옵션 목록 — 프런트 v-select용 title/value 형식 반환"""
    q = db.query(MasterDepartment).filter(MasterDepartment.property_code == property_code)
    if int(only_active or 0) == 1:
        q = q.filter(MasterDepartment.is_active.is_(True))
    rows = q.order_by(
        MasterDepartment.order_no.asc().nulls_last(),
        MasterDepartment.dept_name.asc(),
    ).all()
    return [
        MasterDepartmentOption(title=r.dept_name, value=r.dept_code)
        for r in rows
    ]

# ============================================================================
# 7️⃣ 팀장 지정 / 변경 / 해제
# ============================================================================
@router.put("/{dept_id}/leader", summary="부서 팀장 지정/변경/해제", response_model=dict)
def assign_department_leader(
    dept_id: int,
    body: dict = Body(..., example={"leader_emp_id": 1}),
    db: Session = Depends(get_db),
):
    """부서별 팀장(leader_emp_id) 지정/변경/해제"""
    dept = db.get(MasterDepartment, dept_id)
    if not dept:
        raise HTTPException(status_code=404, detail="부서를 찾을 수 없습니다.")

    leader_id: Optional[int] = body.get("leader_emp_id")
    if leader_id:
        emp = db.get(Employee, leader_id)
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
