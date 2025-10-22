# app/routers/employee_files.py
# -*- coding: utf-8 -*-
# version: 2025-10-18 v3.1 (Stable / Audit Safe)
"""
직원 파일 관리 API (EmployeeFiles)
────────────────────────────────────────────
※ 절대 경로 주의
  • prefix는 반드시 '/api/employee-files' 이어야 함.
    (프런트 baseURL='/api' → 호출 시 'employee-files' 로 시작)
────────────────────────────────────────────
- 조회: ADMIN 이상
- 업로드/버전추가: HRADMIN, SUPERADMIN
────────────────────────────────────────────
"""

from __future__ import annotations
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import require_user, require_roles
from app.db.session import get_db
from app.core.audit import write_audit
from app.models.employee import Employee
from app.models.employee_file import EmployeeFile
from app.schemas.employee_file import EmployeeFileIn, EmployeeFileOut

# ──────────────────────────────────────────────
# Router 설정
# ──────────────────────────────────────────────
router = APIRouter(
    prefix="/api/employee-files",
    tags=["employee-files"],
    dependencies=[Depends(require_user)],
)

# ──────────────────────────────────────────────
# 1️⃣ 목록 조회 (ADMIN+)
# ──────────────────────────────────────────────
@router.get("", dependencies=[Depends(require_roles(["ADMIN", "SUPERADMIN"]))])
def list_employee_files(
    employee_id: Optional[int] = Query(None),
    latest_only: bool = Query(True),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """직원 파일 목록 조회"""
    q = db.query(EmployeeFile)
    if employee_id:
        q = q.filter(EmployeeFile.employee_id == employee_id)
    if latest_only:
        q = q.filter(EmployeeFile.is_latest.is_(True))
    rows = q.order_by(EmployeeFile.employee_id.asc(), EmployeeFile.version_no.desc()).all()
    items = [EmployeeFileOut.model_validate(r).model_dump() for r in rows]
    return {"items": items, "total": len(items)}

# ──────────────────────────────────────────────
# 2️⃣ 업로드/버전추가 (HRADMIN+)
# ──────────────────────────────────────────────
@router.post("", dependencies=[Depends(require_roles(["HRADMIN", "SUPERADMIN"]))])
def upload_employee_file(body: EmployeeFileIn, db: Session = Depends(get_db)):
    """직원 파일 업로드 및 버전 추가"""
    emp = db.query(Employee).filter(Employee.id == body.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="employee not found")

    latest = (
        db.query(EmployeeFile)
        .filter(EmployeeFile.employee_id == body.employee_id, EmployeeFile.is_latest.is_(True))
        .first()
    )
    ver = (latest.version_no + 1) if latest else 1
    if latest:
        latest.is_latest = False

    rec = EmployeeFile(
        employee_id=body.employee_id,
        file_name=body.file_name,
        file_type=body.file_type,
        file_path=body.file_path or "",
        description=body.description or "",
        version_no=ver,
        is_latest=True,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    # 감사 로그 (예외 무시)
    try:
        write_audit(
            db,
            "system",
            "employee_file.upload",
            f"emp={emp.id}",
            {"file": body.file_name, "ver": ver},
        )
    except Exception:
        pass

    return {"ok": True, "file": EmployeeFileOut.model_validate(rec).model_dump()}

# ──────────────────────────────────────────────
# 3️⃣ 이력 조회 (ADMIN+)
# ──────────────────────────────────────────────
@router.get("/history/{employee_id}", dependencies=[Depends(require_roles(["ADMIN", "SUPERADMIN"]))])
def file_history(employee_id: int, db: Session = Depends(get_db)):
    """직원 파일 버전 이력 조회"""
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="employee not found")

    rows = (
        db.query(EmployeeFile)
        .filter(EmployeeFile.employee_id == employee_id)
        .order_by(EmployeeFile.version_no.desc())
        .all()
    )
    items = [EmployeeFileOut.model_validate(r).model_dump() for r in rows]
    return {"employee_id": employee_id, "items": items, "total": len(items)}
