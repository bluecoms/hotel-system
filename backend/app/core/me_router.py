from fastapi import APIRouter, Depends
from app.core.auth import require_user

router = APIRouter(prefix="/api", tags=["core"])

@router.get("/me")
def get_me(user=Depends(require_user)):
    return {"user": user}
