# ============================================================================
# File    : app/routers/users.py
# Version : 2025-10-23 · v3.1 (Auto Default Password · Stable)
# Purpose : Hotel Admin — 사용자 관리 라우터 (/api/users)
# ----------------------------------------------------------------------------
# 목적:
#   • 사용자 계정 생성, 목록, 비활성화, 사원 매핑 관리
# ----------------------------------------------------------------------------
# 변경사항 (v3.1)
#   ✅ 신규 사용자 생성 시 비밀번호 자동 생성("hotel1234")
#   ✅ bcrypt 해시 적용 (passlib)
#   ✅ UserCreate.password 필드 없이도 정상 등록
#   ✅ 생성 시 Audit 로그 기록 유지
# ============================================================================
from __future__ import annotations
import secrets
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from passlib.hash import bcrypt

from app.core.locale import set_lang
from app.core.auth import require_user, require_roles
from app.db.session import get_db
from app.models.user import User
from app.models.employee import Employee, UserEmployeeMap
from app.models.role import RoleAccess
from app.schemas.users import (
    UserCreate, UserListOut, UserActivateIn, CreateFromEmployeeIn
)
from app.core.audit import write_audit

# ─────────────────────────────────────────────
# Router 정의
# ─────────────────────────────────────────────
router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    dependencies=[Depends(set_lang), Depends(require_user)],
)

# ============================================================================
# 1️⃣ 사용자 단건 조회 (ADMIN+)
# ============================================================================
@router.get("/{user_id}", dependencies=[Depends(require_roles(["ADMIN", "SUPERADMIN"]))])
def get_user(user_id: int, db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="user not found")

    mapping = db.query(UserEmployeeMap).filter(UserEmployeeMap.user_id == user_id).first()
    employee_id = mapping.employee_id if mapping else None
    roles = getattr(u, "roles", []) or []

    return {
        "id": u.id,
        "email": u.email,
        "name": u.name or u.email,
        "is_active": bool(u.is_active),
        "roles": roles,
        "employee_id": employee_id,
    }

# ============================================================================
# 2️⃣ 사용자 목록 조회 (ADMIN+)
# ============================================================================
@router.get("", dependencies=[Depends(require_roles(["ADMIN", "SUPERADMIN"]))])
def list_users(
    q: Optional[str] = Query("", description="검색어"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    qry = db.query(User)
    if q:
        like = f"%{q}%"
        qry = qry.filter((User.email.ilike(like)) | (User.name.ilike(like)))

    total = qry.count()
    rows: List[User] = qry.order_by(User.id.desc()).offset((page - 1) * size).limit(size).all()

    # 사원 매핑 정보
    maps: Dict[int, int] = {}
    if rows:
        user_ids = [u.id for u in rows]
        for m in db.query(UserEmployeeMap).filter(UserEmployeeMap.user_id.in_(user_ids)).all():
            maps[m.user_id] = m.employee_id

    items: List[UserListOut] = [
        UserListOut(
            id=u.id,
            email=u.email,
            name=u.name or u.email,
            is_active=bool(getattr(u, "is_active", True)),
            employee_id=maps.get(u.id),
        )
        for u in rows
    ]
    return {"items": [i.model_dump() for i in items], "page": page, "size": size, "total": total}

# ============================================================================
# 3️⃣ 사용자 생성 (SUPERADMIN)
# ============================================================================
@router.post("", dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def create_user(body: UserCreate, db: Session = Depends(get_db)):
    """신규 사용자 생성 — 기본 비밀번호 자동 부여"""
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="email exists")

    # ✅ 비밀번호 자동 생성 (없으면 기본값 hotel1234)
    raw_pw = body.password or "hotel1234"
    hashed = bcrypt.hash(raw_pw)

    user = User(
        email=body.email,
        name=body.name or body.email,
        password_hash=hashed,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    write_audit(db, "system", "user.create", f"user={user.email}, pw=default")
    return {"ok": True, "id": user.id, "default_password": "hotel1234"}

# ============================================================================
# 4️⃣ 사용자 승인/비활성화 (ADMIN+)
# ============================================================================
@router.put("/{user_id}/approve", dependencies=[Depends(require_roles(["ADMIN", "SUPERADMIN"]))])
def approve_user(user_id: int, body: UserActivateIn, db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="user not found")
    u.is_active = body.is_active
    db.commit()
    write_audit(db, "system", "user.approve", f"user={user_id}, active={u.is_active}")
    return {"ok": True, "id": user_id, "is_active": u.is_active}

# ============================================================================
# 5️⃣ 사용자 삭제(비활성화)
# ============================================================================
@router.delete("/{user_id}", dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def deactivate_user(user_id: int, db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="user not found")
    u.is_active = False
    db.commit()
    write_audit(db, "system", "user.deactivate", f"user={user_id}")
    return {"ok": True}

# ============================================================================
# 6️⃣ 사용자-사원 매핑 (ADMIN+)
# ============================================================================
@router.put("/{user_id}/employee/{emp_id}", dependencies=[Depends(require_roles(["ADMIN", "SUPERADMIN"]))])
def map_employee(user_id: int, emp_id: int, db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    e = db.get(Employee, emp_id)
    if not u or not e:
        raise HTTPException(status_code=404, detail="user or employee not found")

    existing = db.query(UserEmployeeMap).filter(UserEmployeeMap.user_id == user_id).first()
    if existing:
        existing.employee_id = emp_id
    else:
        db.add(UserEmployeeMap(user_id=user_id, employee_id=emp_id))
    db.commit()
    write_audit(db, "system", "user.map.employee", f"user={user_id}, emp={emp_id}")
    return {"ok": True}

# ============================================================================
# 7️⃣ 사원으로부터 사용자 생성 (HRADMIN+)
# ============================================================================
@router.post("/from-employee", dependencies=[Depends(require_roles(["HRADMIN", "SUPERADMIN"]))])
def create_from_employee(body: CreateFromEmployeeIn, db: Session = Depends(get_db)):
    emp = db.get(Employee, body.employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="employee not found")
    if db.query(UserEmployeeMap).filter(UserEmployeeMap.employee_id == emp.id).first():
        raise HTTPException(status_code=400, detail="employee already linked")

    email = emp.email or f"{emp.emp_no}@local"
    default_pw = "hotel1234"
    user = User(email=email, name=emp.name, password_hash=bcrypt.hash(default_pw), is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    db.add(UserEmployeeMap(user_id=user.id, employee_id=emp.id))
    db.commit()

    write_audit(db, "system", "user.create.from_employee", f"user={user.id}, emp={emp.id}")
    return {"ok": True, "id": user.id, "default_password": default_pw}

# ============================================================================
# 8️⃣ 역할 접근 관리 (ADMIN+)
# ============================================================================
@router.get("/roles/access/effective", dependencies=[Depends(require_roles(["ADMIN", "SUPERADMIN"]))])
def get_effective_access(db: Session = Depends(get_db)):
    rows = db.query(RoleAccess).all()
    items = [{"role": r.role, "resource": r.resource, "access": r.access} for r in rows]
    return {"items": items, "total": len(items)}

@router.put("/roles/access", dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def update_access(data: List[Dict[str, Any]], db: Session = Depends(get_db)):
    db.query(RoleAccess).delete()
    for row in data:
        db.add(RoleAccess(role=row["role"], resource=row["resource"], access=row["access"]))
    db.commit()
    write_audit(db, "system", "roleaccess.update", f"count={len(data)}")
    return {"ok": True, "count": len(data)}

@router.delete("/roles/access", dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def clear_access(db: Session = Depends(get_db)):
    n = db.query(RoleAccess).delete()
    db.commit()
    write_audit(db, "system", "roleaccess.clear", f"deleted={n}")
    return {"ok": True, "deleted": n}
