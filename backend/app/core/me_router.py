# app/core/me_router.py
from fastapi import APIRouter, Depends
from app.core.auth import require_user

router = APIRouter(prefix="/api", tags=["core"])

@router.get("/me")
def get_me(user=Depends(require_user)):
    # 다른 팀이 기대한 스키마: {"user": {...}}
    return {"user": user}
