# app/routers/reports.py
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from app.core.auth import require_roles
from app.core.locale import set_lang
from app.core.i18n import t
from app.db.session import get_db

router = APIRouter(
    prefix="/api/reports",
    tags=["reports"],
    dependencies=[Depends(set_lang), Depends(require_roles(["ADMIN"]))],
)

@router.get("/sales-tags/export")
async def export_sales_tags(
    request: Request,
    date_from: Optional[str] = Query(None, alias="date_from"),
    date_to: Optional[str]   = Query(None, alias="date_to"),
    db=Depends(get_db),
):
    lang = getattr(request.state, "lang", "en")

    # yyyy-mm-dd 형식만 허용 (빈 값은 허용)
    def _ok(d: Optional[str]) -> bool:
        if not d:
            return True
        if len(d) != 10:
            return False
        try:
            y, m, dd = d.split("-")
            return len(y) == 4 and len(m) == 2 and len(dd) == 2
        except Exception:
            return False

    if not _ok(date_from) or not _ok(date_to):
        raise HTTPException(status_code=422, detail=t("error.validation", lang))
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail=t("error.date_invert", lang))

    # 쿼리
    params: Dict[str, Any] = {}
    where: List[str] = []
    if date_from:
        where.append("business_date >= :df")
        params["df"] = date_from
    if date_to:
        where.append("business_date <= :dt")
        params["dt"] = date_to
    wh = ("WHERE " + " AND ".join(where)) if where else ""

    sql = text(f"""
        SELECT tag, COUNT(*) AS count, SUM(amount) AS amount
        FROM sales_front
        {wh}
        GROUP BY tag
        ORDER BY tag
    """)

    result = db.execute(sql, params)

    # 파일명은 영문 고정 (Phase 4 스펙)
    def compact(d: Optional[str]) -> str:
        return (d or "NA").replace("-", "")
    fname = f"sales-tags_{compact(date_from)}-{compact(date_to)}.csv"

    def gen():
        # CSV 헤더
        yield "tag,count,amount\n"
        for row in result:
            tag = (getattr(row, "tag", "") or "").replace(",", " ")
            count = int(getattr(row, "count", 0) or 0)
            amount = int(getattr(row, "amount", 0) or 0)
            yield f"{tag},{count},{amount}\n"

    headers = {"Content-Disposition": f'attachment; filename="{fname}"'}
    return StreamingResponse(gen(), media_type="text/csv", headers=headers)
