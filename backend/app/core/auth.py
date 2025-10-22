# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/core/auth.py
# Version   : 2025-10-31 · v3.9 (SSOT Phase 3.5 Final · DeptAccess Unified)
# Purpose   : Hotel Admin — Auth Core (FastAPI)
# ----------------------------------------------------------------------------
# 목적:
#   • 헤더 기반 인증 (X-Internal-Token / token-<uid>)
#   • dev / 운영 환경별 토큰 처리 분기
#   • 현재 사용자 로딩(current_user): 이메일 / 이름 / 역할 목록
#   • 역할(require_roles) + 세부 접근(require_access) 권한 검사
# ----------------------------------------------------------------------------
# 주요 개선 (v3.9)
#   ✅ UserRole / RoleAccess 완전 제거
#   ✅ DeptAccess 기반 require_access 로 재작성
#   ✅ X-Internal-Token 기반 인증 구조 표준화
#   ✅ SUPERADMIN 즉시 통과 / Dev 환경 X-Debug-Role 지원
# ----------------------------------------------------------------------------
# 헤더 계약:
#   • X-Internal-Token : 필수 (dev=임의값 허용, prod=고정 토큰 또는 token-<uid>)
#   • X-Debug-Role     : 선택 (dev용 강제 역할 지정, 기본 SUPERADMIN)
# ----------------------------------------------------------------------------
# 반환 사용자 스키마 예시:
#   {"email": "dev@local", "name": "Dev User", "roles": ["SUPERADMIN"]}
# ----------------------------------------------------------------------------
# 보안 정책:
#   • 운영: INTERNAL_API_TOKEN 일치 시만 접근 허용
#   • 개발: 미설정 시 dev-admin-token 으로 통과 허용
#   • SUPERADMIN → 모든 권한 자동 승인
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
from app.models.roles_access import DeptAccess

# ----------------------------------------------------------------------------
# 내부 유틸
# ----------------------------------------------------------------------------
def _is_dev_env() -> bool:
    """DEV/LCL 환경 플래그 (DEBUG=1|true|yes 또는 APP_ENV in {dev, development, local})"""
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
    """dev 환경에서만 허용되는 디버그 역할 헤더"""
    if _is_dev_env():
        return (x_debug_role or "SUPERADMIN").upper()
    return "ADMIN"  # 운영 기본값


# ----------------------------------------------------------------------------
# 토큰 검사 (내부/로그인 공용)
# ----------------------------------------------------------------------------
def require_user(
    request: Request,
    x_internal_token: Optional[str] = Header(None, alias="X-Internal-Token"),
) -> Dict[str, Any]:
    """
    X-Internal-Token 헤더 유효성 검증 (대소문자/하이픈 무관)
    실제 사용자 로딩은 current_user 가 수행.
    """
    token = x_internal_token or request.headers.get("x-internal-token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-Internal-Token")

    # 1️⃣ 로그인 토큰 (token-<uid>)
    if str(token).startswith("token-"):
        return {"token": token}

    # 2️⃣ 내부 고정 토큰
    internal_token = settings.INTERNAL_API_TOKEN or ("dev-admin-token" if _is_dev_env() else None)
    if internal_token and token == internal_token:
        return {"token": token}

    # 3️⃣ 개발 환경: 임의 토큰 허용
    if _is_dev_env():
        return {"token": token}

    # ❌ 운영: 불일치 시 거부
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# ----------------------------------------------------------------------------
# 현재 사용자 로드 (dev 우회)
# ----------------------------------------------------------------------------
def current_user(
    user_hdr=Depends(require_user),
    x_debug_role: Optional[str] = Header(None, alias="X-Debug-Role"),
) -> Dict[str, Any]:
    """현재 사용자 로드 — dev/운영 환경에 따라 역할 및 정보 결정"""
    tok = str(user_hdr.get("token", ""))

    # 1️⃣ 내부 고정 토큰 (운영/개발)
    internal_token = settings.INTERNAL_API_TOKEN or ("dev-admin-token" if _is_dev_env() else None)
    if internal_token and tok == internal_token:
        if not _is_dev_env():
            return {"email": "internal@system.local", "name": "Internal", "roles": ["ADMIN"]}
        return {"email": "internal@system.local", "name": "Internal", "roles": ["SUPERADMIN"]}

    # 2️⃣ 개발 환경: X-Debug-Role 사용
    if _is_dev_env():
        role = _effective_role_for_dev(x_debug_role)
        return {"email": "dev@local", "name": "Dev User", "roles": [role]}

    # ❌ 운영에서 user-token 기반 로그인은 현재 비활성 (User 테이블 연결 제거)
    raise HTTPException(status_code=401, detail="Unauthorized")


# ----------------------------------------------------------------------------
# 역할 기반 권한 검사
# ----------------------------------------------------------------------------
def require_roles(need: Iterable[str]):
    """SUPERADMIN 통과 / 지정 역할 교집합 검사"""
    need_upper = {r.upper() for r in need}

    def _dep(user=Depends(current_user)):
        roles = set([r.upper() for r in (user.get("roles") or [])])
        if "SUPERADMIN" in roles or roles.intersection(need_upper):
            return user
        raise HTTPException(status_code=403, detail="Forbidden")

    return _dep


# ----------------------------------------------------------------------------
# 세부 접근 수준(require_access) — DeptAccess 기반
# ----------------------------------------------------------------------------
def require_access(route_name: str, level: str = "view"):
    """DeptAccess 기반 세부 접근 수준 검사"""
    LEVEL_ORDER = {"none": 0, "view": 1, "edit": 2, "admin": 3}

    def _dep(user=Depends(current_user), db: Session = Depends(get_db)):
        roles = [r.upper() for r in (user.get("roles") or [])]
        if "SUPERADMIN" in roles:
            return user

        needed = LEVEL_ORDER.get(level, 1)
        rec = db.query(DeptAccess).filter(DeptAccess.route_name == route_name).first()
        if not rec:
            raise HTTPException(status_code=403, detail=f"no access record for {route_name}")

        scopes = [s.upper() for s in (rec.access_scope or [])]
        if "ALL_EDIT" in scopes or "ALL_VIEW" in scopes:
            return user
        raise HTTPException(status_code=403, detail=f"insufficient:{route_name}")

    return _dep


# ----------------------------------------------------------------------------
# 내부 토큰 검사 (Shim)
# ----------------------------------------------------------------------------
def require_token_local(
    x_internal_token: Optional[str] = Header(None, alias="X-Internal-Token"),
) -> Dict[str, Any]:
    """내부 엔드포인트용 단순 토큰 검사 (dev 허용 / prod 고정값 일치 필수)"""
    if not x_internal_token:
        raise HTTPException(status_code=401, detail="Missing X-Internal-Token")

    if not _is_dev_env():
        if x_internal_token == (settings.INTERNAL_API_TOKEN or ""):
            return {"ok": True}
        raise HTTPException(status_code=401, detail="Invalid internal token")

    if x_internal_token == (settings.INTERNAL_API_TOKEN or "dev-admin-token"):
        return {"ok": True, "dev": True}
    return {"ok": True, "dev": True}


# ----------------------------------------------------------------------------
# 로그인 / 세션 / 비밀번호 API (옵션 유지)
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
    if not u or not u.password_hash:
        raise HTTPException(status_code=404, detail="User not found or no password set")
    if not bcrypt.verify(password, u.password_hash):
        raise HTTPException(status_code=401, detail="비밀번호가 올바르지 않습니다.")
    token = f"token-{u.id}"
    return {"token": token, "user": {"email": u.email, "name": u.name or u.email, "roles": ["ADMIN"]}}

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
    """비밀번호 초기화 (SUPERADMIN 전용)"""
    roles = set([r.upper() for r in (user.get("roles") or [])])
    if "SUPERADMIN" not in roles:
        raise HTTPException(status_code=403, detail="SUPERADMIN only")

    target = db.query(User).filter(User.email == email).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    if not new_password:
        alphabet = string.ascii_letters + string.digits
        new_password = "".join(secrets.choice(alphabet) for _ in range(12))
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="비밀번호는 8자 이상이어야 합니다.")

    target.password_hash = bcrypt.hash(new_password)
    db.add(target)
    db.commit()
    return {"ok": True, "email": email, "temp_password": new_password}

# ============================================================================
# End of File — app/core/auth.py
# ============================================================================
