# backend/app/routers/user_roles.py
# -*- coding: utf-8 -*-
# version: 2025-10-16  v2.5
"""
User ↔ Role 매핑 API (UserRole)
────────────────────────────────────────────
- prefix: /api/user-roles
- 조회: ADMIN 이상
- 변경(POST/DELETE): SUPERADMIN 전용
- 모든 변경은 audit 로그 기록
- 신규: GET /effective → 현재 사용자 역할 + 효과 권한맵 제공 (빈 dict 금지)
"""

from __future__ import annotations
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, Query, Body, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.auth import require_user, require_roles
from app.core.audit import write_audit
from app.db.session import get_db
from app.models.user import User
from app.models.role import Role, UserRole
from app.schemas.role_map import RoleMapIn, RoleMapOut, RoleMapListOut

# ─────────────────────────────────────────────
# 라우터 선언
# ─────────────────────────────────────────────
router = APIRouter(
    prefix="/api/user-roles",
    tags=["roles", "users"],
    dependencies=[Depends(require_user)],  # 인증 공통
)

# ─────────────────────────────────────────────
# 내부 유틸
# ─────────────────────────────────────────────
def _pluck_id(obj: Any) -> Optional[int]:
    """require_user 가 User 객체 또는 dict로 반환되더라도 ID 추출."""
    if obj is None:
        return None
    if isinstance(obj, User):
        return obj.id
    return getattr(obj, "id", None) or (obj.get("id") if isinstance(obj, dict) else None)


def _get_role_codes(db: Session, user_id: int) -> List[str]:
    """UserRole → Role.code 목록 조회 (활성 Role만)."""
    if not user_id:
        return []
    q = (
        db.query(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user_id, Role.is_active.is_(True))
    )
    return sorted({(c or "").upper() for (c,) in q.all() if c})

# ─────────────────────────────────────────────
# NEW: 현재 사용자 "효과 권한맵" 조회
# GET /api/user-roles/effective
#
# 반환:
#   {
#     "user_id": 1,
#     "roles": ["SUPERADMIN", "ADMIN"],
#     "access": { "*": "admin" }
#   }
#
# 규칙:
#   - SUPERADMIN → 모든 리소스 admin
#   - ADMIN      → 모든 리소스 edit
#   - 기타       → 빈 맵 {} (프런트 폴백으로 세부 권한 계산)
#
# 보장:
#   ⚠️ 절대 None 리턴 금지. 최소 {} 보장.
# ─────────────────────────────────────────────
@router.get("/effective")
def get_effective_for_me(
    current=Depends(require_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    user_id = _pluck_id(current)
    roles = _get_role_codes(db, user_id) if user_id else []

    access: Dict[str, str] = {}
    if "SUPERADMIN" in roles:
        access = {"*": "admin"}
    elif "ADMIN" in roles:
        access = {"*": "edit"}

    # 반환은 항상 dict 보장 (None 방지)
    return {
        "user_id": user_id or 0,
        "roles": roles or [],
        "access": access or {},
    }

# ─────────────────────────────────────────────
# 목록 조회 (ADMIN+)
# GET /api/user-roles
# ─────────────────────────────────────────────
@router.get("", dependencies=[Depends(require_roles(["ADMIN", "SUPERADMIN"]))])
def list_user_roles(
    user_id: Optional[int] = Query(None, description="특정 사용자 ID 필터"),
    role_code: Optional[str] = Query(None, description="특정 역할 코드 필터"),
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    q = db.query(UserRole)

    if user_id is not None:
        q = q.filter(UserRole.user_id == user_id)

    if role_code:
        q = q.join(Role, Role.id == UserRole.role_id).filter(Role.code == role_code.upper())

    total = q.count()
    rows: List[UserRole] = (
        q.order_by(UserRole.id.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    # Role.code 매핑
    role_by_id: Dict[int, str] = {}
    if rows:
        role_ids = {r.role_id for r in rows}
        for r in db.query(Role).filter(Role.id.in_(role_ids)).all():
            role_by_id[r.id] = (r.code or "").upper()

    items = [
        RoleMapOut(
            id=ur.id,
            user_id=ur.user_id,
            role_code=role_by_id.get(ur.role_id, ""),
            created_at=getattr(ur, "created_at", None),
        )
        for ur in rows
    ]

    return RoleMapListOut(items=items, total=total).model_dump(exclude_none=True)

# ─────────────────────────────────────────────
# 매핑 생성 (SUPERADMIN 전용)
# POST /api/user-roles
# ─────────────────────────────────────────────
@router.post("", dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def create_user_role(
    body: RoleMapIn,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")

    code = (body.role_code or "").upper().strip()
    role = db.query(Role).filter(Role.code == code, Role.is_active.is_(True)).first()
    if not role:
        raise HTTPException(status_code=404, detail="role not found")

    has = db.query(UserRole).filter(
        and_(UserRole.user_id == user.id, UserRole.role_id == role.id)
    ).first()
    if has:
        out = RoleMapOut(
            id=has.id,
            user_id=user.id,
            role_code=code,
            created_at=getattr(has, "created_at", None),
        )
        return {"ok": True, "mapping": out.model_dump(), "duplicated": True}

    # 생성
    m = UserRole(user_id=user.id, role_id=role.id)
    db.add(m)
    db.commit()
    db.refresh(m)

    # 감사 로그
    try:
        write_audit(
            db,
            actor="system",
            action="userrole.create",
            target=f"user_id={user.id}",
            meta={"role_code": code},
        )
    except Exception:
        pass

    out = RoleMapOut(
        id=m.id,
        user_id=user.id,
        role_code=code,
        created_at=getattr(m, "created_at", None),
    )
    return {"ok": True, "mapping": out.model_dump(), "duplicated": False}

# ─────────────────────────────────────────────
# 매핑 삭제 (SUPERADMIN 전용)
# DELETE /api/user-roles?user_id=..&role_code=..
# ─────────────────────────────────────────────
@router.delete("", dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def delete_user_role(
    user_id: int = Query(..., description="대상 사용자 ID"),
    role_code: str = Query(..., description="삭제할 역할 코드"),
    db: Session = Depends(get_db),
):
    code = (role_code or "").upper().strip()

    role = db.query(Role).filter(Role.code == code).first()
    if not role:
        raise HTTPException(status_code=404, detail="role not found")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")

    deleted = db.query(UserRole).filter(
        and_(UserRole.user_id == user.id, UserRole.role_id == role.id)
    ).delete(synchronize_session=False)
    db.commit()

    try:
        write_audit(
            db,
            actor="system",
            action="userrole.delete",
            target=f"user_id={user.id}",
            meta={"role_code": code, "deleted": deleted},
        )
    except Exception:
        pass

    return {"ok": True, "deleted": deleted}

# ======================================================================
# END OF FILE — version 2025-10-16 v2.5 (근본수정 완료)
# 변경 요약:
#   ✅ /effective 가 None/null 절대 반환하지 않음
#   ✅ SUPERADMIN/ADMIN 기본 access 자동 생성
#   ✅ RoleMapListOut 응답 안정화 (exclude_none)
#   ✅ create/delete 멱등/감사로그 유지
# ======================================================================
