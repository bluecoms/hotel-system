# app/core/auth.py
from fastapi import Depends, Header, HTTPException, status
from typing import Iterable, Optional
from app.core.settings import settings

def require_user(x_internal_token: Optional[str] = Header(None, alias="X-Internal-Token")):
    """
    운영 공통 인증: 내부 토큰 필수.
    필요하면 여기서 토큰 값 검증(화이트리스트 등) 추가 가능.
    """
    if not x_internal_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-Internal-Token")
    return {"token": x_internal_token}

def _effective_role(x_debug_role: Optional[str]) -> str:
    """
    운영(prod 등)에서는 디버그 롤 무시하고 ADMIN 고정.
    개발(dev 등)에서만 X-Debug-Role을 받아들이며, 기본값은 ADMIN.
    """
    is_dev = bool(getattr(settings, "DEBUG", False)) or str(getattr(settings, "ENV", "")).lower() in {"dev", "development", "local"}
    if not is_dev:
        return "ADMIN"
    return (x_debug_role or "ADMIN").upper()

def require_roles(need: Iterable[str]):
    need_upper = {r.upper() for r in need}

    def _dep(
        user = Depends(require_user),
        x_debug_role: Optional[str] = Header(None, alias="X-Debug-Role")  # DEV ONLY
    ):
        role = _effective_role(x_debug_role)
        if role not in need_upper:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return _dep
