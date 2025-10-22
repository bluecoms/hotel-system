# app/routers/reports_sales.py
# -*- coding: utf-8 -*-
from typing import List, Optional, Tuple
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from app.core.auth import require_roles

import datetime as dt

router = APIRouter(
    prefix="/api/reports/sales",
    tags=["reports"],
    dependencies=[Depends(require_roles(["ADMIN", "SUPERADMIN"]))],
)

# ─────────────────────────────────────────────────────────────
# 모델
# ─────────────────────────────────────────────────────────────
class SalesRecord(BaseModel):
    name: str
    memo: str = ""
    amount: int

class NormalizeOut(BaseModel):
    room_only: int
    package: int
    other: int

# ─────────────────────────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────────────────────────
def _parse_ymd(s: str) -> dt.date:
    """YYYY-MM-DD → date. 잘못된 형식은 ValueError."""
    return dt.datetime.strptime(s, "%Y-%m-%d").date()

def _month_bounds(today: Optional[dt.date] = None) -> Tuple[dt.date, dt.date]:
    """기본 범위: '오늘'이 속한 달의 1일 ~ 말일"""
    t = today or dt.date.today()
    first = t.replace(day=1)
    # 다음달 1일 - 1일 == 말일
    if first.month == 12:
        next_first = first.replace(year=first.year + 1, month=1, day=1)
    else:
        next_first = first.replace(month=first.month + 1, day=1)
    last = next_first - dt.timedelta(days=1)
    return first, last

def _normalize_dates(
    date_from: Optional[str],
    date_to: Optional[str],
) -> Tuple[dt.date, dt.date]:
    """
    빈 문자열/공백/None 모두 안전 처리.
    규칙:
      1) 둘 다 비었으면 → 현재 월 전체
      2) 하나만 있으면 → 단일 일자 범위(같은 날짜로 from=to)
      3) 둘 다 있으면 → 정상 파싱, from > to면 스왑
    """
    s_from = (date_from or "").strip()
    s_to   = (date_to or "").strip()

    has_from = bool(s_from)
    has_to   = bool(s_to)

    if not has_from and not has_to:
        return _month_bounds()

    if has_from and not has_to:
        d = _parse_ymd(s_from)
        return d, d

    if not has_from and has_to:
        d = _parse_ymd(s_to)
        return d, d

    # 둘 다 존재
    df = _parse_ymd(s_from)
    dt_ = _parse_ymd(s_to)
    if df > dt_:
        df, dt_ = dt_, df
    return df, dt_

def _sanitize_property_code(prop: Optional[str]) -> str:
    p = (prop or "").strip()
    if not p:
        # 422보다는 명확한 메시지를 가진 400이 실무에 유리
        raise HTTPException(status_code=400, detail="property_code가 필요합니다.")
    return p

# ─────────────────────────────────────────────────────────────
# 엔드포인트
# ─────────────────────────────────────────────────────────────
@router.post("/normalize", response_model=NormalizeOut)
def normalize_sales(records: List[SalesRecord]):
    """
    간단 분류 스텁:
    - 'ROOM' 포함 → 룸온리
    - '패키지' 또는 'PKG' 포함 → 패키지
    - 나머지 → 기타
    """
    up = lambda s: (s or "").upper()
    room_only = sum(r.amount for r in records if "ROOM" in up(r.name))
    package   = sum(r.amount for r in records if ("패키지" in r.name) or ("PKG" in up(r.name)))
    other     = max(0, sum(r.amount for r in records) - room_only - package)
    return {"room_only": room_only, "package": package, "other": other}

@router.get("/front/by-kind")
def sales_front_by_kind(
    # ✅ 빈 문자열/누락 모두 허용 (근본 처리)
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to:   Optional[str] = Query(None, description="YYYY-MM-DD"),
    property_code: Optional[str] = Query(None, min_length=0, description="자산 코드"),
):
    """
    프런트 매출(종별) 집계 스텁.
    - date_from / date_to 가 비어 있으면: '현재 월 전체'를 기본값으로 사용
    - 하나만 있으면: 단일 일자 범위(from=to)
    - 둘 다 있으면: 유효성 검사 및 from>to 스왑
    - property_code 공백/누락: 400
    """
    prop = _sanitize_property_code(property_code)
    try:
        df, dt_ = _normalize_dates(date_from, date_to)
    except ValueError:
        raise HTTPException(status_code=400, detail="date_from/date_to 형식은 YYYY-MM-DD 이어야 합니다.")

    # 데모 응답(실데이터 연결 전)
    return {
        "property_code": prop,
        "date_from": df.isoformat(),
        "date_to": dt_.isoformat(),
        "rooms": {"room_only": 1200000, "package": 800000, "other": 40000},
    }
