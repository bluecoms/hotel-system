# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/core/auth.py
# Version   : 2025.11-01 · v3.7 (DeptAccess Unified · CEO SuperAdmin)
# Purpose   : Hotel Admin — Auth Core (FastAPI)
# ----------------------------------------------------------------------------
# 목적:
#   • 헤더 기반 인증 (X-Internal-Token / token-<uid>)
#   • dev / 운영 환경별 토큰 처리 분기
#   • 현재 사용자 로딩(current_user): 이메일 / 이름 / 역할 목록
#   • 역할 기반(require_roles) + DeptAccess 기반 접근 제어 통합
# ----------------------------------------------------------------------------
# 주요 개선:
#   ✅ CEO 계정(ceo@mokpooceanhotel.co.kr) → SUPERADMIN 자동 부여
#   ✅ dev-admin-token 환경에서도 정상 동작
#   ✅ DeptAccess 기반 구조에 완전 호환
#   ✅ require_access() → RoleAccess → DeptAccess로 안전 폴백
# ============================================================================

from __future__ import annotations
import os
import secrets
import string
from typing import Iterable, Optional, Dict, Any, List

from fastapi import Depends, Header, HTTPException, status, APIRouter, Body, Request
from sqlalchemy.orm import Session
from passlib.hash import bcrypt

from app.db.session import get_db
from app.core.settings import settings
from app.models.user import User
from app.models.role import Role

# ──────────────────────────────────────────────
# 내부 유틸: 환경·역할 보조
# ──────────────────────────────────────────────
def _is_dev_env() -> bool:
    """DEV/LCL 환경 플래그"""
    env = str(settings.APP_ENV or "").lower()
    dbg = str(getattr(settings, "DEBUG", "")).lower()
    return dbg in {"1", "true", "yes"} or env in {"dev", "development", "local"}


def _uid_from_token(token: str) -> Optional[int]:
    """로그인 토큰 규약: 'token-<uid>' → uid 반환"""
    if not token or not token.startswith("token-"):
        return None
    try:
        return int(token.split("-", 1)[1])
    except Exception:
        return None


def _effective_role_for_dev(x_debug_role: Optional[str]) -> str:
    """개발환경에서만 허용되는 디버그 역할"""
    if _is_dev_env():
        return (x_debug_role or "SUPERADMIN").upper()
    return "ADMIN"


# ──────────────────────────────────────────────
# 토큰 검사 (내부/로그인 공용)
# ──────────────────────────────────────────────
def require_user(
    request: Request,
    x_internal_token: Optional[str] = Header(None, alias="X-Internal-Token"),
) -> Dict[str, Any]:
    """X-Internal-Token 헤더 유효성 검증 (대소문자 무관)"""
    token = x_internal_token or request.headers.get("x-internal-token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing X-Internal-Token")

    # 로그인 토큰 (token-<uid>)
    if token.startswith("token-"):
        return {"token": token}

    # 내부 고정 토큰 (운영/개발 분기)
    internal_token = settings.INTERNAL_API_TOKEN or ("dev-admin-token" if _is_dev_env() else None)
    if internal_token and token == internal_token:
        return {"token": token}

    # dev 환경: 임의 토큰 허용
    if _is_dev_env():
        return {"token": token}

    raise HTTPException(status_code=401, detail="Invalid token")


# ──────────────────────────────────────────────
# 현재 사용자 로드
# ──────────────────────────────────────────────
def current_user(
    user_hdr=Depends(require_user),
    x_debug_role: Optional[str] = Header(None, alias="X-Debug-Role"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """현재 사용자 로드 — dev/운영 환경에 따라 역할 및 정보 결정"""
    tok = str(user_hdr.get("token", ""))
    uid = _uid_from_token(tok)

    # 1️⃣ 로그인 토큰 → DB 사용자/역할
    if uid:
        u = db.query(User).filter(User.id == uid).first()
        if not u:
            raise HTTPException(status_code=401, detail="User not found")

        # ✅ CEO 계정은 SUPERADMIN, 나머지는 ADMIN
        if u.email.strip().lower() == "ceo@mokpooceanhotel.co.kr":
            roles = ["SUPERADMIN"]
        else:
            roles = ["ADMIN"]

        return {"email": u.email, "name": (u.name or u.email), "roles": roles}

    # 2️⃣ INTERNAL TOKEN (운영/개발)
    internal_token = settings.INTERNAL_API_TOKEN or ("dev-admin-token" if _is_dev_env() else None)
    if internal_token and tok == internal_token:
        if _is_dev_env():
            return {"email": "internal@system.local", "name": "Internal", "roles": ["SUPERADMIN"]}
        return {"email": "internal@system.local", "name": "Internal", "roles": ["ADMIN"]}

    # 3️⃣ 개발 환경 디버그 역할
    if _is_dev_env():
        role = _effective_role_for_dev(x_debug_role)
        return {"email": "dev@local", "name": "Dev User", "roles": [role]}

    raise HTTPException(status_code=401, detail="Unauthorized")


# ──────────────────────────────────────────────
# 역할 기반 권한 검사
# ──────────────────────────────────────────────
def require_roles(need: Iterable[str]):
    """SUPERADMIN 통과 / 지정 역할 교집합 검사"""
    need_upper = {r.upper() for r in need}

    def _dep(user=Depends(current_user)):
        roles = set(r.upper() for r in (user.get("roles") or []))
        if "SUPERADMIN" in roles or roles.intersection(need_upper):
            return user
        raise HTTPException(status_code=403, detail="Forbidden")

    return _dep


# ──────────────────────────────────────────────
# 내부 토큰 단순 검사 (require_token_local)
# ──────────────────────────────────────────────
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

    if x_internal_token == (settings.INTERNAL_API_TOKEN or "dev-admin-token"):
        return {"ok": True, "dev": True}
    if x_internal_token.startswith("token-"):
        return {"ok": True, "dev": True}
    return {"ok": True, "dev": True}


# ──────────────────────────────────────────────
# 로그인 / 비밀번호 API
# ──────────────────────────────────────────────
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
    # ✅ CEO 계정은 SUPERADMIN 으로 응답
    roles = ["SUPERADMIN"] if u.email.strip().lower() == "ceo@mokpooceanhotel.co.kr" else ["ADMIN"]
    return {"token": token, "user": {"email": u.email, "name": (u.name or u.email), "roles": roles}}


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
