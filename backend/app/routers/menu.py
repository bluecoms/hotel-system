# app/routers/menu.py
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Header

from app.core.auth import require_user, _effective_role  # 내부 유틸 재사용
from app.core.locale import set_lang  # 일관성: 언어 컨텍스트만 세팅(기능 영향 없음)

router = APIRouter(
    prefix="/api",
    tags=["menu"],
    # 언어 세팅 먼저, 이후 인증 사용자 확보
    dependencies=[Depends(set_lang)],
)

@router.get("/menu")
def get_menu(
    user = Depends(require_user),
    x_debug_role: Optional[str] = Header(None, alias="X-Debug-Role"),  # DEV ONLY
) -> Dict[str, List[Dict[str, Any]]]:
    """
    역할 기반 메뉴.
    - ADMIN: OTA, Reports 노출
    - 그 외: 빈 배열
    """
    role = _effective_role(x_debug_role)
    items: List[Dict[str, Any]] = []

    admin_items = [
        # title은 FE에서 그대로 사용하거나, i18n 키를 쓰려면 titleKey로 넘겨도 됨
        {"title": "OTA",     "to": "/admin/ota/list",           "roles": ["ADMIN"]},
        {"title": "Reports", "to": "/admin/reports/sales-tags", "roles": ["ADMIN"]},
    ]

    if role == "ADMIN":
        items.extend(admin_items)

    return {"items": items}
