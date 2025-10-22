# -*- coding: utf-8 -*-
# ============================================================================
# File    : app/routers/roles.py
# Version : 2025-10-31 · v3.5 (SSOT Phase 3.5 Final · Role CRUD Only)
# Purpose : Hotel Admin — 역할(Role) 관리 API (DeptAccess 분리 이후 순수화)
# ----------------------------------------------------------------------------
# 목적:
#   • 역할(Role) 생성/삭제/조회 API 제공
#   • DeptAccess(부서 기반 접근권한)는 /api/roles/access 라우터로 분리
# ----------------------------------------------------------------------------
# 변경 사항 (v3.5)
#   ✅ RoleAccess 관련 로직 완전 제거
#   ✅ DeptAccess 관리 전용 roles_access.py로 분리
#   ✅ 인증 스키마 require_token_local 기반으로 단순화
#   ✅ 모든 변경사항은 audit 로그 기록
# ----------------------------------------------------------------------------
# 연동 모듈:
#   • app/models/role.py         → Role
#   • app/schemas/role.py        → RoleIn / RoleOut
#   • app/core/audit.py          → write_audit()
#   • src/views/Admin/RoleList.vue (역할 관리 화면)
# ============================================================================
from __future__ import annotations
from typing import Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import require_token_local, require_roles
from app.core.audit import write_audit
from app.db.session import get_db
from app.models.role import Role
from app.schemas.role import RoleIn, RoleOut

# ─────────────────────────────────────────────
# Router 정의
# ─────────────────────────────────────────────
router = APIRouter(
    prefix="/api/roles",
    tags=["roles"],
    dependencies=[Depends(require_token_local)],
)

# ============================================================================
# 1️⃣ 역할(Role) 목록 조회
# ============================================================================
@router.get("", dependencies=[Depends(require_roles(["ADMIN", "SUPERADMIN"]))])
def list_roles(
    include_inactive: bool = Query(False, description="비활성 포함 여부"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    역할 목록 조회
    - ADMIN 이상 접근 가능
    - 기본은 활성 상태(is_active=True)만 조회
    """
    q = db.query(Role)
    if not include_inactive:
        q = q.filter(Role.is_active.is_(True))
    roles = q.order_by(Role.code.asc()).all()
    items = [RoleOut.model_validate(r).model_dump() for r in roles]
    return {"ok": True, "items": items, "total": len(items)}

# ============================================================================
# 2️⃣ 역할(Role) 생성
# ============================================================================
@router.post("", dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def create_role(body: RoleIn, db: Session = Depends(get_db)):
    """
    역할 신규 생성
    - SUPERADMIN 전용
    """
    code = (body.code or "").strip().upper()
    if not code:
        raise HTTPException(status_code=422, detail="code required")

    # 중복 코드 검사
    has = db.query(Role).filter(Role.code == code).first()
    if has:
        raise HTTPException(status_code=400, detail="duplicate role code")

    r = Role(code=code, name=body.name or code, is_active=bool(body.is_active))
    db.add(r)
    db.commit()
    db.refresh(r)

    # 감사 로그 기록
    write_audit(db, "system", "role.create", f"code={r.code}", {"name": r.name})
    return {"ok": True, "role": RoleOut.model_validate(r).model_dump()}

# ============================================================================
# 3️⃣ 역할(Role) 삭제
# ============================================================================
@router.delete("/{code}", dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def delete_role(code: str, db: Session = Depends(get_db)):
    """
    역할 삭제
    - SUPERADMIN 전용
    """
    code = code.strip().upper()
    r = db.query(Role).filter(Role.code == code).first()
    if not r:
        raise HTTPException(status_code=404, detail="role not found")

    db.delete(r)
    db.commit()

    # 감사 로그 기록
    write_audit(db, "system", "role.delete", f"code={code}")
    return {"ok": True, "deleted": code}

# ============================================================================
# End of File — app/routers/roles.py
# ============================================================================
