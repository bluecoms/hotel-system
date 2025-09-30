# app/core/auth.py
from fastapi import Header, HTTPException, Depends, status
from typing import Optional, List
from functools import lru_cache
from pydantic_settings import BaseSettings

class _Settings(BaseSettings):
    APP_ENV: str = "dev"
    APP_DB_URL: str = "sqlite:////volume1/web/hotel-system/backend/hotel.db"  # ← 추가
    INTERNAL_API_TOKEN: str = "dev-admin-token"
    class Config:
        env_file = "/volume1/web/hotel-system/backend/.env"
        env_file_encoding = "utf-8"

@lru_cache
def settings(): return _Settings()

ROLES = {
    "SUPERADMIN": "SUPERADMIN",
    "ADMIN": "ADMIN",
}

def require_token(x_internal_token: Optional[str] = Header(None, alias="X-Internal-Token")):
    if not x_internal_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-Internal-Token")
    if settings().APP_ENV.lower() == "dev":
        return True
    if x_internal_token != settings().INTERNAL_API_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return True

def current_user(
    x_internal_token: Optional[str] = Header(None, alias="X-Internal-Token"),
    x_debug_role: Optional[str] = Header(None, alias="X-Debug-Role"),
):
    s = settings()
    if s.APP_ENV.lower() == "dev":
        role = (x_debug_role or ROLES["SUPERADMIN"]).upper()
        if role not in ROLES.values():
            role = ROLES["SUPERADMIN"]
        return {"email": "admin@example.com", "name": "Admin", "roles": [role]}

    if not x_internal_token or x_internal_token != s.INTERNAL_API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"email": "admin@example.com", "name": "Admin", "roles": [ROLES["ADMIN"]]}

def require_user(user = Depends(current_user)):
    return user

def require_roles(need: List[str]):
    def _dep(user = Depends(current_user)):
        roles = set(user.get("roles", []))
        if not roles.intersection(set(need)):
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return _dep
