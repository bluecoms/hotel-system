# ============================================================================
# File      : app/routers/reports.py
# Version   : 2025.10-20 Final Stable
# Purpose   : 리포트 API (Sales Tags + Dashboard KPI + OTA 매출 + Rooms Split)
# ----------------------------------------------------------------------------
# 변경사항 (v2025.10-20)
#   ✅ Dashboard KPI 엔드포인트 개선 (business_date / date 병용, pattern 제거)
#   ✅ 빈 문자열/누락 모두 허용 — FastAPI ValidationError 방지
#   ✅ reports_bank.py / reports_sales.py 구조와 일관성 유지
#   ✅ 주석 및 description 보강
# ----------------------------------------------------------------------------
# FastAPI: 0.116.x / SQLAlchemy Core 기반
# ============================================================================
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Request, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import text

from app.core.auth import require_roles
from app.core.locale import set_lang
from app.core.i18n import t as _t
from app.db.session import get_db

# 선택 모듈(없어도 작동)
try:
    from app.core.keywords import apply_keywords_and_summarize
except Exception:
    def apply_keywords_and_summarize(*_args, **_kw) -> Dict[str, Any]:
        return {"rooms": {"room_only": 0, "package": 0, "other": 0}}

router = APIRouter(
    prefix="/api/reports",
    tags=["reports"],
    dependencies=[Depends(set_lang), Depends(require_roles(["ADMIN", "SUPERADMIN"]))],
)

# ─────────────────────────────────────────────────────────────
# 내부 유틸
# ─────────────────────────────────────────────────────────────
def _valid_date(d: Optional[str]) -> bool:
    if not d:
        return True
    if len(d) != 10:
        return False
    try:
        y, m, dd = d.split("-")
        int(y); int(m); int(dd)
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────
# Sales Tags (집계 + CSV 내보내기)
# ─────────────────────────────────────────────────────────────
@router.get("/sales-tags")
def list_sales_tags(
    request: Request,
    property_code: str = Query("MOP", min_length=1),
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD (빈값 허용)"),
    date_to:   Optional[str] = Query(None, description="YYYY-MM-DD (빈값 허용)"),
    db=Depends(get_db),
):
    lang = getattr(request.state, "lang", "en")
    if not _valid_date(date_from) or not _valid_date(date_to):
        raise HTTPException(status_code=422, detail=_t("error.validation", lang))
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail=_t("error.date_invert", lang))

    params: Dict[str, Any] = {"pc": property_code}
    where: List[str] = ["property_code = :pc"]
    if date_from:
        where.append("business_date >= :df"); params["df"] = date_from
    if date_to:
        where.append("business_date <= :dt"); params["dt"] = date_to
    wh = "WHERE " + " AND ".join(where)

    rows = db.execute(text(f"""
        SELECT tag AS tag,
               COUNT(*) AS count,
               COALESCE(SUM(amount),0) AS amount
        FROM sales_front
        {wh}
        GROUP BY tag
        ORDER BY amount DESC, tag ASC
    """), params).mappings().all()

    snapshot = apply_keywords_and_summarize(db, date_from or "", property_code)

    return {
        "ok": True,
        "property_code": property_code,
        "from": date_from,
        "to": date_to,
        "summary": snapshot,
        "items": [
            {"tag": (r["tag"] or ""), "count": int(r["count"] or 0), "amount": int(r["amount"] or 0)}
            for r in rows
        ],
    }


@router.get("/sales-tags/export")
def export_sales_tags(
    request: Request,
    property_code: str = Query("MOP", min_length=1),
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD (빈값 허용)"),
    date_to:   Optional[str] = Query(None, description="YYYY-MM-DD (빈값 허용)"),
    db=Depends(get_db),
):
    lang = getattr(request.state, "lang", "en")
    if not _valid_date(date_from) or not _valid_date(date_to):
        raise HTTPException(status_code=422, detail=_t("error.validation", lang))
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail=_t("error.date_invert", lang))

    params: Dict[str, Any] = {"pc": property_code}
    where: List[str] = ["property_code = :pc"]
    if date_from:
        where.append("business_date >= :df"); params["df"] = date_from
    if date_to:
        where.append("business_date <= :dt"); params["dt"] = date_to
    wh = "WHERE " + " AND ".join(where)

    rows = db.execute(text(f"""
        SELECT tag AS tag,
               COUNT(*) AS count,
               COALESCE(SUM(amount),0) AS amount
        FROM sales_front
        {wh}
        GROUP BY tag
        ORDER BY amount DESC, tag ASC
    """), params).mappings().all()

    def compact(d: Optional[str]) -> str:
        return (d or "NA").replace("-", "")

    fname = f"sales-tags_{compact(date_from)}-{compact(date_to)}.csv"

    def gen():
        yield "tag,count,amount\r\n"
        for r in rows:
            tag = (r["tag"] or "").replace(",", " ")
            yield f"{tag},{int(r['count'] or 0)},{int(r['amount'] or 0)}\r\n"

    headers = {"Content-Disposition": f'attachment; filename="{fname}"'}
    return StreamingResponse(gen(), media_type="text/csv; charset=utf-8", headers=headers)


# ─────────────────────────────────────────────────────────────
# Dashboard KPI (화면에서 사용)
# ─────────────────────────────────────────────────────────────
@router.get("/dashboard-kpi")
def dashboard_kpi(
    property_code: str = Query("MOP", min_length=1, description="자산 코드"),
    business_date: Optional[str] = Query(None, description="사업일자 (YYYY-MM-DD, 빈값 허용)"),
    date: Optional[str] = Query(None, description="호환용 date 파라미터 (YYYY-MM-DD)"),
    db=Depends(get_db),
):
    biz_date = business_date or date
    if not biz_date:
        raise HTTPException(422, "business_date required (YYYY-MM-DD)")

    total_row = db.execute(text("""
        SELECT COALESCE(SUM(amount),0) AS total
        FROM sales_front
        WHERE business_date=:dt AND property_code=:pc
    """), {"dt": biz_date, "pc": property_code}).mappings().first()
    total = int(total_row["total"] if total_row and "total" in total_row else 0)

    kw_summary = apply_keywords_and_summarize(db, biz_date, property_code)
    rooms = kw_summary.get("rooms", {})

    return {
        "ok": True,
        "property_code": property_code,
        "business_date": biz_date,
        "rev": total,
        "occ": 0.0,
        "adr": 0,
        "room_only_amount": int(rooms.get("room_only", 0)),
        "package_amount":   int(rooms.get("package", 0)),
        "other_amount":     int(rooms.get("other", 0)),
    }


# ─────────────────────────────────────────────────────────────
# F&B Summary (Stub)
# ─────────────────────────────────────────────────────────────
@router.get("/fnb-summary")
def fnb_summary(
    property_code: str = Query("MOP", min_length=1),
    date_from: str = Query(..., description="YYYY-MM-DD"),
    date_to: str   = Query(..., description="YYYY-MM-DD"),
):
    return {
        "property_code": property_code,
        "date_from": date_from,
        "date_to": date_to,
        "items": [],
    }


# ─────────────────────────────────────────────────────────────
# OTA Sales (Stub)
# ─────────────────────────────────────────────────────────────
@router.get("/ota-sales")
def ota_sales(
    property_code: str = Query("MOP", min_length=1),
    _from: str = Query(..., alias="from", description="YYYY-MM-DD"),
    to:    str = Query(..., description="YYYY-MM-DD"),
):
    return {"property_code": property_code, "from": _from, "to": to, "items": []}


# ─────────────────────────────────────────────────────────────
# Rooms Split (Stub)
# ─────────────────────────────────────────────────────────────
@router.get("/rooms-split")
def rooms_split(
    request: Request,
    property_code: str = Query("MOP", min_length=1),
    date_from: Optional[str] = Query(None),
    date_to:   Optional[str] = Query(None),
    db=Depends(get_db),
):
    lang = getattr(request.state, "lang", "en")

    if not _valid_date(date_from) or not _valid_date(date_to):
        raise HTTPException(status_code=422, detail=_t("error.validation", lang))

    f = (date_from or "").strip()
    t = (date_to or "").strip()

    if not f and not t:
        import datetime as dt
        today = dt.date.today()
        first = today.replace(day=1)
        next_first = first.replace(
            year=first.year + 1, month=1, day=1
        ) if first.month == 12 else first.replace(month=first.month + 1, day=1)
        last = next_first - dt.timedelta(days=1)
        f, t = first.isoformat(), last.isoformat()
    elif f and not t:
        t = f
    elif not f and t:
        f = t
    else:
        if f > t:
            raise HTTPException(status_code=422, detail=_t("error.date_invert", lang))

    return {
        "property_code": property_code,
        "date_from": f,
        "date_to": t,
        "items": [],
    }
