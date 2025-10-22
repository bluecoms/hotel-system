# app/routers/menu.py
from typing import List, Dict, Any
from fastapi import APIRouter, Depends

from app.core.auth import require_roles
from app.core.locale import set_lang

router = APIRouter(
    prefix="/api",
    tags=["menu"],
    dependencies=[Depends(set_lang), Depends(require_roles(["ADMIN"]))],
)

@router.get("/menu")
def get_menu() -> Dict[str, List[Dict[str, Any]]]:
    items: List[Dict[str, Any]] = [
        {"title": "OTA",     "to": "/admin/ota/list",           "roles": ["ADMIN"]},
        {"title": "Reports", "to": "/admin/reports/sales-tags", "roles": ["ADMIN"]},
    ]
    return {"items": items}
