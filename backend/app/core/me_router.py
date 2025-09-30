# app/core/me_router.py
# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends
from app.core.auth import require_user

router = APIRouter(prefix="/api", tags=["core"])

@router.get("/me")
def get_me(_: dict = Depends(require_user)):
    """
    규약 고정:
    { "user": { "email": "dev@local", "roles": ["ADMIN"] } }
    - roles는 대문자 문자열 배열, 최소 ADMIN 1개 포함
    - 인증은 X-Internal-Token 헤더만 사용 (require_user가 검증)
    """
    return {"user": {"email": "dev@local", "roles": ["ADMIN"]}}
