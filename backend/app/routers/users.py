# app/routers/users.py
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Request

from app.core.auth import require_user
from app.core.locale import set_lang

router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    # 언어 컨텍스트 세팅(기능 영향 없음) + 로그인 사용자 보장
    dependencies=[Depends(set_lang), Depends(require_user)],
)

@router.get("")
def list_users(request: Request) -> Dict[str, List[Dict[str, Any]]]:
    """
    사용자 목록 (placeholder).
    - 인증된 호출만 허용(require_user)
    - 언어 컨텍스트는 request.state.lang 에 저장(set_lang)
    실제 구현은 기존 서비스 코드로 교체하세요.
    """
    # lang = getattr(request.state, "lang", "en")  # 필요 시 사용
    return {"items": []}
