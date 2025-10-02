# app/routers/audit.py
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
import json

from app.core.auth import require_roles
from app.core.locale import set_lang
from app.db.session import get_db

router = APIRouter(
    prefix="/api/audit",
    tags=["audit"],
    dependencies=[Depends(set_lang), Depends(require_roles(["ADMIN"]))],
)

@router.get("/logs")
def get_logs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    최근 감사 로그 목록.
    - meta_json 컬럼은 파싱하여 'meta' 필드로 반환 (파싱 실패 시 원문 문자열 유지)
    """
    rows = (
        db.execute(
            text("SELECT * FROM audit_logs ORDER BY ts DESC LIMIT :lim OFFSET :off"),
            {"lim": limit, "off": offset},
        )
        .mappings()
        .all()
    )

    out: List[Dict[str, Any]] = []
    for r in rows:
        d = dict(r)
        raw = d.pop("meta_json", None)
        meta: Optional[Any] = None
        if raw is not None:
            try:
                meta = json.loads(raw)
            except Exception:
                meta = raw  # 파싱 실패 시 원문 유지
        d["meta"] = meta
        out.append(d)

    return out
