# app/operations/closing/router.py
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Query
from app.operations.closing.schemas import ClosingCalendarResp

router = APIRouter(prefix="/api/closing", tags=["closing"])

def _month_range(month: str):
    start = datetime.strptime(month + "-01", "%Y-%m-%d")
    next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    end = next_month - timedelta(days=1)
    return start, end

@router.get("/calendar", response_model=ClosingCalendarResp)
def get_calendar(
    month: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    property_code: str = "MOP",
):
    if month:
        start, end = _month_range(month)
        return ClosingCalendarResp(
            property_code=property_code,
            date_from=start.strftime("%Y-%m-%d"),
            date_to=end.strftime("%Y-%m-%d"),
            items=[],
        )
    return ClosingCalendarResp(
        property_code=property_code,
        date_from=date_from or "",
        date_to=date_to or "",
        items=[],
    )
