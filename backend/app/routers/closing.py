# app/routers/closing.py
# -*- coding: utf-8 -*-
"""
Hotel Admin — Closing Router (v2025.10 Final / BizDatePicker 통합 대응)
────────────────────────────────────────────────────────────────────
목적
  • 일자별 마감 상태 조회/변경, 월간 캘린더, 승인/잠금/해제
  • UploadSession/UploadedFile과 연계해 날짜별 진행률·완료도 계산
  • 프런트 초기 진입 시 `date` 미지정 요청을 허용(서버 기준일 fallback)

핵심 변경 (2025-10-20)
  ✅ `/api/closing/day` GET: `date`를 선택 인자(Optional)로 변경
     - 미지정 시 서버 기준 오늘 날짜(UTC, YYYY-MM-DD)로 처리
     - 응답에 `business_date` 필드를 추가(프런트 동기화용)
  ✅ 나머지 엔드포인트는 기존 스펙 유지(상태 set/approve/lock/unlock, 캘린더)

주의
  • 권한: require_token_local 필수, 상태 변경은 ADMIN/SUPERADMIN
  • 날짜 포맷은 YYYY-MM-DD 고정
"""

from __future__ import annotations
from datetime import datetime, timedelta, date as dt_date
from typing import Dict, List, Tuple, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.auth import require_roles, require_token_local
from app.db.session import get_db
from app.models.closing import ClosingDay, UploadSession, UploadedFile

router = APIRouter(prefix="/api", tags=["closing"])

REQUIRED_DATASETS = ["rooms_status", "sales_front", "fnb_sales", "expenses", "pay_settlement"]

# ───────────────────────────────────────────────
# 내부 유틸
# ───────────────────────────────────────────────
def _is_day_closed(db: Session, property_code: str, business_date: str) -> bool:
    row = db.query(ClosingDay).filter(
        ClosingDay.property_code == property_code,
        ClosingDay.business_date == business_date,
        ClosingDay.status == "CLOSED",
    ).first()
    return bool(row)

def _present_parts_for(db: Session, session_id: int) -> List[str]:
    rows = (
        db.query(UploadedFile.part_key)
        .filter(UploadedFile.session_id == session_id)
        .filter(func.length(UploadedFile.part_key) > 0)
        .distinct()
        .all()
    )
    return sorted({(pk or "").strip() for (pk,) in rows if (pk or "").strip()})

def _day_progress(db: Session, property_code: str, business_date: str) -> Tuple[int, int]:
    done, total = 0, len(REQUIRED_DATASETS)
    for ds in REQUIRED_DATASETS:
        sess = db.query(UploadSession).filter_by(
            dataset=ds, property_code=property_code, business_date=business_date
        ).first()
        if not sess:
            continue
        versions = db.query(UploadedFile).filter_by(session_id=sess.id).count()
        if versions > 0:
            done += 1
    return done, total

# ───────────────────────────────────────────────
# 상태 / 단일 일자
# ───────────────────────────────────────────────
@router.get("/closing/status", dependencies=[Depends(require_token_local)])
def closing_status(date: str, property_code: str = "MOP", db: Session = Depends(get_db)):
    out = []
    for ds in REQUIRED_DATASETS:
        sess = db.query(UploadSession).filter(
            UploadSession.dataset == ds,
            UploadSession.property_code == property_code,
            UploadSession.business_date == date,
        ).first()
        if not sess:
            out.append(
                {
                    "dataset": ds,
                    "exists": False,
                    "versions": 0,
                    "required_parts": [],
                    "present_parts": [],
                    "missing_parts": [],
                }
            )
            continue
        versions = db.query(UploadedFile).filter(UploadedFile.session_id == sess.id).count()
        present = _present_parts_for(db, sess.id)
        out.append(
            {
                "dataset": ds,
                "exists": versions > 0,
                "versions": versions,
                "required_parts": [],
                "present_parts": present,
                "missing_parts": [],
            }
        )
    return {"date": date, "property_code": property_code, "items": out}

@router.get("/closing/day", dependencies=[Depends(require_token_local)])
def closing_day_get(
    date: Optional[str] = Query(None, description="YYYY-MM-DD (미지정 시 서버 기준일 사용)"),
    property_code: str = Query("MOP"),
    db: Session = Depends(get_db),
):
    """
    일자별 마감 상태 조회
    - 프런트 초기 진입 시 `date`가 비어 있을 수 있으므로 서버가 기본값을 제공
    - 응답에 `business_date` 포함: 프런트 BizDatePicker와 동기화 용이
    """
    # ✅ fallback: date 미지정 → 서버 기준 오늘(UTC)
    if not date:
        date = datetime.utcnow().strftime("%Y-%m-%d")

    status = "CLOSED" if _is_day_closed(db, property_code, date) else "OPEN"
    done, total = _day_progress(db, property_code, date)
    return {
        "date": date,
        "business_date": date,  # 동기화용
        "status": status,
        "done": done,
        "total": total,
        "complete": (done == total),
    }

@router.put("/closing/day", dependencies=[Depends(require_token_local)])
def closing_day_set(
    body: Optional[dict] = Body(None),
    date: Optional[str] = Query(None),
    property_code: str = Query("MOP"),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(require_roles(["SUPERADMIN"])),
):
    """
    일자 상태 변경 (OPEN/CLOSED)
    - JSON Body와 Query 양쪽 모두 허용 (프런트/도구별 호환)
    - 필수: date, status(OPEN|CLOSED)
    """
    if body:
        _date = body.get("date")
        _pc = body.get("property_code") or "MOP"
        _st = (body.get("status") or "").upper()
    else:
        _date = date
        _pc = property_code or "MOP"
        _st = (status or "").upper()

    if not _date or _st not in ("OPEN", "CLOSED"):
        raise HTTPException(422, "date/status required")

    row = db.query(ClosingDay).filter_by(property_code=_pc, business_date=_date).first()
    if row:
        row.status = _st
    else:
        db.add(ClosingDay(property_code=_pc, business_date=_date, status=_st))
    db.commit()
    return {"ok": True, "status": _st}

# ───────────────────────────────────────────────
# 월간 캘린더
# ───────────────────────────────────────────────
@router.get("/closing/calendar", dependencies=[Depends(require_token_local)])
def closing_calendar(month: str = "", property_code: str = "MOP", db: Session = Depends(get_db)):
    today = datetime.utcnow()
    if not month:
        month = today.strftime("%Y-%m")
    y, m = map(int, month.split("-"))
    first = dt_date(y, m, 1)
    next_first = dt_date(y + 1, 1, 1) if m == 12 else dt_date(y, m + 1, 1)
    last = next_first - timedelta(days=1)

    sessions = (
        db.query(UploadSession)
        .filter(UploadSession.property_code == property_code)
        .filter(UploadSession.business_date >= first.strftime("%Y-%m-%d"))
        .filter(UploadSession.business_date <= last.strftime("%Y-%m-%d"))
        .all()
    )

    closings = db.query(ClosingDay).filter(
        ClosingDay.property_code == property_code,
        ClosingDay.business_date >= first.strftime("%Y-%m-%d"),
        ClosingDay.business_date <= last.strftime("%Y-%m-%d"),
    ).all()
    status_map = {c.business_date: (c.status or "OPEN").upper() for c in closings}

    day_map: Dict[str, Dict] = {}
    for s in sessions:
        b = s.business_date
        info = day_map.setdefault(b, {"datasets": set(), "counts": {}})
        info["datasets"].add(s.dataset)
        cnt = db.query(UploadedFile).filter(UploadedFile.session_id == s.id).count()
        info["counts"][s.dataset] = cnt

    days: List[Dict] = []
    d = first
    while d <= last:
        key = d.strftime("%Y-%m-%d")
        present = day_map.get(key, {"datasets": set(), "counts": {}})
        uploaded = sorted(list(present["datasets"]))
        counts = present["counts"]
        done = len(set(uploaded) & set(REQUIRED_DATASETS))
        total = len(REQUIRED_DATASETS)
        days.append(
            {
                "date": key,
                "uploaded": uploaded,
                "counts": counts,
                "done": done,
                "total": total,
                "complete": (done == total),
                "status": status_map.get(key, "OPEN"),
            }
        )
        d += timedelta(days=1)

    return {
        "property_code": property_code,
        "month": month,
        "timezone": "UTC",
        "from": first.strftime("%Y-%m-%d"),
        "to": last.strftime("%Y-%m-%d"),
        "required": REQUIRED_DATASETS,
        "days": days,
    }

# ───────────────────────────────────────────────
# Build 엔드포인트 (실제 반영 버전)
# ───────────────────────────────────────────────
@router.post("/closing/build", dependencies=[Depends(require_roles(["ADMIN", "SUPERADMIN"]))])
def closing_build(
    body: dict = Body(...),
    db: Session = Depends(get_db),
):
    """마감 데이터 집계(build) — 업로드 완료 후 수동 실행"""
    business_date = body.get("business_date")
    property_code = body.get("property_code", "MOP")

    if not business_date:
        raise HTTPException(422, "business_date required")

    done, total = _day_progress(db, property_code, business_date)
    complete = (done == total)

    # ClosingDay 상태 업데이트
    row = db.query(ClosingDay).filter_by(property_code=property_code, business_date=business_date).first()
    if not row:
        row = ClosingDay(property_code=property_code, business_date=business_date)
        db.add(row)

    row.status = "CLOSED" if complete else "OPEN"
    db.commit()

    return {
        "ok": True,
        "property_code": property_code,
        "business_date": business_date,
        "datasets_done": done,
        "datasets_total": total,
        "complete": complete,
        "status": row.status,
        "message": f"Closing build completed: status={row.status}",
    }

# ───────────────────────────────────────────────
# 마감 승인 / 잠금 / 해제
# ───────────────────────────────────────────────
@router.post("/closing/approve", dependencies=[Depends(require_roles(["ADMIN", "SUPERADMIN"]))])
def closing_approve(
    body: dict = Body(...),
    db: Session = Depends(get_db),
):
    """마감 승인(승인 시 상태를 CLOSED로 갱신)"""
    business_date = body.get("business_date")
    property_code = body.get("property_code", "MOP")
    if not business_date:
        raise HTTPException(422, "business_date required")

    row = db.query(ClosingDay).filter_by(property_code=property_code, business_date=business_date).first()
    if row:
        row.status = "CLOSED"
    else:
        db.add(ClosingDay(property_code=property_code, business_date=business_date, status="CLOSED"))
    db.commit()
    return {"ok": True, "status": "CLOSED", "message": "Day approved and closed."}

@router.post("/closing/lock", dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def closing_lock(
    body: dict = Body(...),
    db: Session = Depends(get_db),
):
    """잠금(Locked) 상태로 변경"""
    business_date = body.get("business_date")
    property_code = body.get("property_code", "MOP")
    if not business_date:
        raise HTTPException(422, "business_date required")

    row = db.query(ClosingDay).filter_by(property_code=property_code, business_date=business_date).first()
    if not row:
        raise HTTPException(404, "day not found")
    row.status = "LOCKED"
    db.commit()
    return {"ok": True, "status": "LOCKED", "message": "Day locked for editing."}

@router.post("/closing/unlock", dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def closing_unlock(
    body: dict = Body(...),
    db: Session = Depends(get_db),
):
    """잠금 해제 → OPEN 상태로 복귀"""
    business_date = body.get("business_date")
    property_code = body.get("property_code", "MOP")
    if not business_date:
        raise HTTPException(422, "business_date required")

    row = db.query(ClosingDay).filter_by(property_code=property_code, business_date=business_date).first()
    if not row:
        raise HTTPException(404, "day not found")
    row.status = "OPEN"
    db.commit()
    return {"ok": True, "status": "OPEN", "message": "Day unlocked and reopened."}
