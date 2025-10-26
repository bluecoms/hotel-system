# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/core/auth.py
# Version   : 2025.11-01 · v3.8 (Dev SuperAdmin Auto · SSOT Final)
# Purpose   : Hotel Admin — Auth Core (FastAPI)
# ----------------------------------------------------------------------------
# 목적:
#   • 개발환경(dev)에서는 SUPERADMIN 자동 부여 (로컬 토큰/디버그 헤더 포함)
#   • CEO(ceo@mokpooceanhotel.co.kr)는 운영환경에서도 SUPERADMIN 고정
#   • INTERNAL_TOKEN(dev-admin-token)도 SUPERADMIN으로 처리
# ----------------------------------------------------------------------------
# 개발용 슈퍼어드민 정책:
#   ✅ 조건
#       - APP_ENV=dev 또는 DEBUG=True
#       - X-Internal-Token=dev-admin-token 이거나
#       - X-Debug-Role 헤더 지정 시 ("SUPERADMIN" 자동)
#   ✅ 결과
#       - 모든 DeptAccess, RoleAccess, require_roles() 검사 통과
#       - 메뉴/화면 전체 접근 허용
# ============================================================================
from __future__ import annotations
import os, secrets, string
from typing import Iterable, Optional, Dict, Any, List
from fastapi import Depends, Header, HTTPException, status, APIRouter, Body, Request
from sqlalchemy.orm import Session
from passlib.hash import bcrypt

from app.db.session import get_db
from app.core.settings import settings
from app.models.user import User
from app.models.role import Role


# ----------------------------------------------------------------------------
# 환경 감지 유틸
# ----------------------------------------------------------------------------
def _is_dev_env() -> bool:
    """개발환경(dev/local) 여부 확인"""
    env = str(settings.APP_ENV or "").lower()
    dbg = str(getattr(settings, "DEBUG", "")).lower()
    return dbg in {"1", "true", "yes"} or env in {"dev", "development", "local"}


def _uid_from_token(token: str) -> Optional[int]:
    """로그인 토큰 규약: token-<uid>"""
    if not token or not token.startswith("token-"):
        return None
    try:
        return int(token.split("-", 1)[1])
    except Exception:
        return None


def _effective_role_for_dev(x_debug_role: Optional[str]) -> str:
    """개발환경에서는 SUPERADMIN 자동"""
    if _is_dev_env():
        return (x_debug_role or "SUPERADMIN").upper()
    return "ADMIN"


# ----------------------------------------------------------------------------
# 1️⃣ 기본 토큰 검증
# ----------------------------------------------------------------------------
def require_user(
    request: Request,
    x_internal_token: Optional[str] = Header(None, alias="X-Internal-Token"),
) -> Dict[str, Any]:
    """X-Internal-Token 헤더 유효성 검증"""
    token = x_internal_token or request.headers.get("x-internal-token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing X-Internal-Token")

    # 로그인 토큰 (token-<uid>)
    if token.startswith("token-"):
        return {"token": token}

    # 내부 고정 토큰 (운영/개발)
    internal_token = settings.INTERNAL_API_TOKEN or ("dev-admin-token" if _is_dev_env() else None)
    if internal_token and token == internal_token:
        return {"token": token}

    # 개발환경에서는 아무 토큰이나 허용
    if _is_dev_env():
        return {"token": token}

    raise HTTPException(status_code=401, detail="Invalid token")


# ----------------------------------------------------------------------------
# 2️⃣ 현재 사용자 로드
# ----------------------------------------------------------------------------
def current_user(
    user_hdr=Depends(require_user),
    x_debug_role: Optional[str] = Header(None, alias="X-Debug-Role"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """현재 사용자 로드 — dev/운영 환경에 따라 SUPERADMIN 자동 반영"""
    tok = str(user_hdr.get("token", ""))
    uid = _uid_from_token(tok)

    # 로그인 토큰 → DB 조회
    if uid:
        u = db.query(User).filter(User.id == uid).first()
        if not u:
            raise HTTPException(status_code=401, detail="User not found")
        # CEO는 항상 SUPERADMIN
        if u.email.strip().lower() == "ceo@mokpooceanhotel.co.kr":
            roles = ["SUPERADMIN"]
        else:
            roles = ["ADMIN"]
        return {"email": u.email, "name": u.name or u.email, "roles": roles}

    # 내부 토큰
    internal_token = settings.INTERNAL_API_TOKEN or ("dev-admin-token" if _is_dev_env() else None)
    if internal_token and tok == internal_token:
        role = "SUPERADMIN" if _is_dev_env() else "ADMIN"
        return {"email": "internal@system.local", "name": "Internal", "roles": [role]}

    # 개발 환경 (디버그 롤 포함)
    if _is_dev_env():
        role = _effective_role_for_dev(x_debug_role)
        return {"email": "dev@local", "name": "Dev SuperAdmin", "roles": [role]}

    raise HTTPException(status_code=401, detail="Unauthorized")


# ----------------------------------------------------------------------------
# 3️⃣ 역할 기반 권한 검사
# ----------------------------------------------------------------------------
def require_roles(need: Iterable[str]):
    """SUPERADMIN 통과 / 지정 역할 교집합 검사"""
    need_upper = {r.upper() for r in need}

    def _dep(user=Depends(current_user)):
        roles = set(r.upper() for r in (user.get("roles") or []))
        if "SUPERADMIN" in roles or roles.intersection(need_upper):
            return user
        raise HTTPException(status_code=403, detail="Forbidden")

    return _dep


# ----------------------------------------------------------------------------
# 4️⃣ 내부 토큰 간이 검사 (require_token_local)
# ----------------------------------------------------------------------------
def require_token_local(
    x_internal_token: Optional[str] = Header(None, alias="X-Internal-Token"),
) -> Dict[str, Any]:
    """내부 엔드포인트용 간이 토큰 검사"""
    if not x_internal_token:
        raise HTTPException(status_code=401, detail="Missing X-Internal-Token")

    if not _is_dev_env():
        if x_internal_token == (settings.INTERNAL_API_TOKEN or ""):
            return {"ok": True}
        raise HTTPException(status_code=401, detail="Invalid internal token")

    # 개발환경은 전부 허용
    if x_internal_token == (settings.INTERNAL_API_TOKEN or "dev-admin-token"):
        return {"ok": True, "dev": True, "role": "SUPERADMIN"}
    if x_internal_token.startswith("token-"):
        return {"ok": True, "dev": True, "role": "SUPERADMIN"}
    return {"ok": True, "dev": True, "role": "SUPERADMIN"}


# ----------------------------------------------------------------------------
# 5️⃣ 로그인 / 비밀번호 관련 API
# ----------------------------------------------------------------------------
router = APIRouter(prefix="/api", tags=["auth"])

@router.post("/login", operation_id="auth_login")
def login(
    email: str = Body(..., embed=True),
    password: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    """로그인: 이메일/비밀번호 검증 → token-<uid> 발급"""
    u = db.query(User).filter(User.email == email).first()
    if not u:
        raise HTTPException(status_code=404, detail="Not Found")
    if not u.password_hash or not bcrypt.verify(password, u.password_hash):
        raise HTTPException(status_code=401, detail="비밀번호가 올바르지 않습니다.")

    token = f"token-{u.id}"
    # CEO → SUPERADMIN, 일반 → ADMIN
    roles = ["SUPERADMIN"] if u.email.strip().lower() == "ceo@mokpooceanhotel.co.kr" else ["ADMIN"]
    return {"token": token, "user": {"email": u.email, "name": u.name or u.email, "roles": roles}}


@router.get("/me", operation_id="auth_me")
def me(user=Depends(current_user)):
    """현재 사용자 정보 반환"""
    return {"user": user}


@router.post("/password/change", operation_id="auth_change_password")
def change_password(
    user=Depends(current_user),
    current_password: str = Body(..., embed=True),
    new_password: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    """비밀번호 변경 (로그인 토큰 사용자만 가능)"""
    if (user.get("email") == "internal@system.local") and not _is_dev_env():
        raise HTTPException(status_code=401, detail="Login token required")

    u = db.query(User).filter(User.email == user["email"]).first()
    if not u or not u.password_hash:
        raise HTTPException(status_code=404, detail="User not found")
    if not bcrypt.verify(current_password, u.password_hash):
        raise HTTPException(status_code=400, detail="현재 비밀번호가 올바르지 않습니다.")
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="새 비밀번호는 8자 이상이어야 합니다.")

    u.password_hash = bcrypt.hash(new_password)
    db.add(u)
    db.commit()
    return {"ok": True}


@router.post("/users/password/reset", operation_id="auth_reset_password")
def reset_password(
    user=Depends(current_user),
    email: str = Body(..., embed=True),
    new_password: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db),
):
    """사용자 비밀번호 초기화 (SUPERADMIN 전용)"""
    roles = set(r.upper() for r in (user.get("roles") or []))
    if "SUPERADMIN" not in roles:
        raise HTTPException(status_code=403, detail="SUPERADMIN only")

    target = db.query(User).filter(User.email == email).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    if not new_password:
        alphabet = string.ascii_letters + string.digits
        new_password = "".join(secrets.choice(alphabet) for _ in range(12))

    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="임시 비밀번호는 8자 이상이어야 합니다.")

    target.password_hash = bcrypt.hash(new_password)
    db.add(target)
    db.commit()
    return {"ok": True, "email": email, "temp_password": new_password}
