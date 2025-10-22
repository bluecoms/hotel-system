# -*- coding: utf-8 -*-
# ============================================================================
# File    : app/routers/users.py
# Version : 2025-10-31 · v3.6 (SSOT Phase 3.5 Final · DeptAccess Split)
# Purpose : Hotel Admin — 사용자 관리 라우터 (/api/users)
# ----------------------------------------------------------------------------
# 목적:
#   • 사용자 CRUD, 승인/비활성화, 사원 매핑
#   • 내부 API(X-Internal-Token) 기반 보호
#   • ⚠️ 권한(DeptAccess) 관리는 app/routers/roles_access.py 로 완전 분리
# ----------------------------------------------------------------------------
# 정책 요약:
#   ✅ 인증 : require_token_local (헤더 X-Internal-Token)
#   ✅ 권한 : require_roles(["ADMIN","SUPERADMIN"]) 최소 가드
#   ✅ Audit : 모든 변경동작 기록 (write_audit)
#   ✅ Python 3.8 호환 완전보장 (typing.Optional/List/Dict 사용)
# ============================================================================
from __future__ import annotations
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from passlib.hash import bcrypt

from app.core.locale import set_lang
from app.core.auth import require_token_local, require_roles
from app.db.session import get_db
from app.models.user import User
from app.models.employee import Employee, UserEmployeeMap
from app.schemas.users import UserCreate, UserListOut, UserActivateIn, CreateFromEmployeeIn
from app.core.audit import write_audit

# ─────────────────────────────────────────────
# Router 정의
# ─────────────────────────────────────────────
router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    dependencies=[
        Depends(set_lang),
        Depends(require_token_local),  # ✅ 내부 토큰 인증
    ],
)

# ============================================================================
# 1️⃣ 사용자 단건 조회 (ADMIN+)
# ============================================================================
@router.get("/{user_id}", dependencies=[Depends(require_roles(["ADMIN", "SUPERADMIN"]))])
def get_user(user_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    단일 사용자 조회
    - UserEmployeeMap을 통해 employee_id 연결값을 함께 반환
    - roles 필드는 ORM 관계(selectin)로 읽기 전용 리스트
    """
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="user not found")

    mapping = db.query(UserEmployeeMap).filter(UserEmployeeMap.user_id == user_id).first()
    return {
        "id": u.id,
        "email": u.email,
        "name": u.name or u.email,
        "is_active": bool(u.is_active),
        "roles": getattr(u, "roles", []) or [],
        "employee_id": mapping.employee_id if mapping else None,
    }

# ============================================================================
# 2️⃣ 사용자 목록 조회 (ADMIN+)
# ============================================================================
@router.get("", dependencies=[Depends(require_roles(["ADMIN", "SUPERADMIN"]))])
def list_users(
    q: Optional[str] = Query("", description="검색어 (이름/이메일 부분일치)"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    사용자 목록 조회 (검색/페이징 지원)
    - employee_id는 별도 매핑 조회 후 합성
    - Pydantic UserListOut로 직렬화
    """
    qry = db.query(User)
    if q:
        like = f"%{q}%"
        qry = qry.filter(or_(User.email.ilike(like), User.name.ilike(like)))

    total = qry.count()
    rows = qry.order_by(User.id.desc()).offset((page - 1) * size).limit(size).all()

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
    return {
        "items": [i.model_dump() for i in items],
        "page": page,
        "size": size,
        "total": total,
    }

# ============================================================================
# 3️⃣ 사용자 생성 (SUPERADMIN)
# ============================================================================
@router.post("", dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def create_user(body: UserCreate, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    신규 사용자 생성
    - password 미지정 시 기본값 'hotel1234'
    - password_hash(bcrypt) 저장
    """
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="email exists")

    raw_pw = body.password or "hotel1234"
    hashed = bcrypt.hash(raw_pw)
    user = User(email=body.email, name=body.name or body.email, password_hash=hashed, is_active=body.is_active)
    db.add(user)
    db.commit()
    db.refresh(user)

    write_audit(db, "system", "user.create", f"user={user.email}, default_pw={'yes' if body.password is None else 'no'}")
    return {"ok": True, "id": user.id, "default_password": (None if body.password else "hotel1234")}

# ============================================================================
# 4️⃣ 사용자 승인/비활성화 (ADMIN+)
# ============================================================================
@router.put("/{user_id}/approve", dependencies=[Depends(require_roles(["ADMIN", "SUPERADMIN"]))])
def approve_user(user_id: int, body: UserActivateIn, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    사용자 활성/비활성 전환
    - is_active 토글
    """
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="user not found")
    u.is_active = body.is_active
    db.commit()
    write_audit(db, "system", "user.approve", f"user={user_id}, active={u.is_active}")
    return {"ok": True, "id": user_id, "is_active": u.is_active}

# ============================================================================
# 5️⃣ 사용자 비활성화 (삭제 아님) (SUPERADMIN)
# ============================================================================
@router.delete("/{user_id}", dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def deactivate_user(user_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    사용자 비활성화
    - 실제 삭제가 아닌 is_active=False
    """
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
def map_employee(user_id: int, emp_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    사용자와 사원(Employee) ID 매핑
    - 기존 매핑 존재 시 교체, 없으면 생성
    """
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
def create_from_employee(body: CreateFromEmployeeIn, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    사원정보로 사용자 계정 자동 생성
    - 이미 다른 유저와 매핑된 사원은 거부
    - 기본 비밀번호 'hotel1234'
    """
    emp = db.get(Employee, body.employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="employee not found")
    if db.query(UserEmployeeMap).filter(UserEmployeeMap.employee_id == emp.id).first():
        raise HTTPException(status_code=400, detail="employee already linked")

    email = body.email or emp.email or f"{getattr(emp, 'emp_no', emp.id)}@local"
    default_pw = "hotel1234"
    user = User(email=email, name=emp.name or email, password_hash=bcrypt.hash(default_pw), is_active=body.is_active)
    db.add(user)
    db.commit()
    db.refresh(user)
    db.add(UserEmployeeMap(user_id=user.id, employee_id=emp.id))
    db.commit()
    write_audit(db, "system", "user.create.from_employee", f"user={user.id}, emp={emp.id}")
    return {"ok": True, "id": user.id, "default_password": default_pw}

# ============================================================================
# ⚠️ 중요: 권한(DeptAccess) 관련 엔드포인트는 roles_access.py 로 이관
#   • /api/roles/access
#   • /api/roles/access/effective
# ============================================================================
