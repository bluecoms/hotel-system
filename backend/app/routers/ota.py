# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/routers/ota.py
# Version   : 2025.10-26 · v3.5 (Add Master Mapping · SSOT Extended)
# Purpose   : Hotel Admin — OTA Router (채널·수수료·주문 관리)
# ----------------------------------------------------------------------------
# 목적:
#   • OTA 관련 데이터(채널, 수수료, 주문, 요약) 관리 API
#   • MasterOtaChannel 과 자동 매핑 지원 (SSOT 일원화)
# ----------------------------------------------------------------------------
# 주요 엔드포인트:
#   - GET  /api/ota/channels           → OTA 채널 목록
#   - POST /api/ota/channels           → 신규 채널 등록 (Master 연동)
#   - GET  /api/ota/commissions        → 수수료 목록
#   - POST /api/ota/commissions        → 수수료 등록
#   - PUT  /api/ota/commissions/{id}   → 수수료 수정
#   - DELETE /api/ota/commissions/{id} → 수수료 삭제
#   - GET  /api/ota/orders             → 주문 목록
#   - GET  /api/ota/summary            → OTA 매출 요약
# ----------------------------------------------------------------------------
# 연계:
#   • app/models/ota.py
#   • app/models/master_ota_channel.py
#   • app/core/auth.py
# ============================================================================
from __future__ import annotations
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any

from fastapi import (
    APIRouter, Depends, HTTPException, Query, Path, Body, Header, Request, status
)
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc, or_

from app.core.auth import require_roles
from app.core.locale import set_lang
from app.core.i18n import t as _t
from app.core.audit import write_audit
from app.db.session import get_db
from app.models import OTAChannel, OTACommission, OTAOrder, MasterOtaChannel

router = APIRouter(
    prefix="/api/ota",
    tags=["ota"],
    dependencies=[Depends(set_lang), Depends(require_roles(["ADMIN", "SUPERADMIN"]))],
)

# ────────────────────────────
# Helpers
# ────────────────────────────
def _now() -> datetime:
    return datetime.utcnow()

def _parse_date(v) -> Optional[date]:
    if isinstance(v, date):
        return v
    if isinstance(v, str) and v.strip():
        return datetime.strptime(v.strip(), "%Y-%m-%d").date()
    return None

def _get_channel_by_code(db: Session, code: str, lang: str) -> OTAChannel:
    ch = db.query(OTAChannel).filter(OTAChannel.code == code).first()
    if not ch:
        raise HTTPException(status_code=404, detail=_t("error.not_found", lang))
    return ch

def _has_overlap(db: Session, channel_id: int, frm: date, to: date, exclude_id: Optional[int] = None) -> bool:
    q = db.query(OTACommission).filter(OTACommission.channel_id == channel_id)
    if exclude_id:
        q = q.filter(OTACommission.id != exclude_id)
    q = q.filter(OTACommission.valid_from <= to, frm <= OTACommission.valid_to)
    return db.query(q.exists()).scalar()

# ============================================================================
# 1️⃣ OTA 채널
# ============================================================================
@router.get("/channels")
def list_channels(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    total = db.query(OTAChannel).count()
    rows = (
        db.query(OTAChannel)
        .order_by(asc(OTAChannel.id))
        .offset(offset)
        .limit(limit)
        .all()
    )
    items = [{
        "id": r.id,
        "code": r.code,
        "name": r.name,
        "status": r.status,
        "master_id": r.master_id,
    } for r in rows]
    return {"total": int(total), "items": items}


@router.post("/channels", status_code=status.HTTP_201_CREATED)
def create_channel(
    request: Request,
    body: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    x_internal_token: Optional[str] = Header(None),
):
    lang = getattr(request.state, "lang", "en")
    code = (body.get("code") or "").strip().upper()
    name = (body.get("name") or "").strip()
    status_val = (body.get("status") or "").strip()

    if not code or not name:
        raise HTTPException(status_code=422, detail=_t("error.validation", lang))

    if db.query(OTAChannel).filter(OTAChannel.code == code).first():
        raise HTTPException(status_code=400, detail=_t("error.duplicate", lang))

    now = _now()
    ch = OTAChannel(code=code, name=name, status=status_val)

    # ✅ Master 채널 자동 매핑
    master = db.query(MasterOtaChannel).filter(MasterOtaChannel.code == code).first()
    if master:
        ch.master_id = master.id
    else:
        master = MasterOtaChannel(code=code, name=name, is_active=True)
        db.add(master)
        db.flush()
        ch.master_id = master.id

    if hasattr(ch, "created_at") and getattr(ch, "created_at") is None:
        setattr(ch, "created_at", now)
    if hasattr(ch, "updated_at"):
        setattr(ch, "updated_at", now)

    db.add(ch)
    db.commit()
    db.refresh(ch)

    write_audit(
        db,
        x_internal_token or "SYSTEM",
        "OTA_CHANNEL_CREATE",
        f"channel_code={ch.code}",
        {"lang": lang, "channel_id": ch.id, "name": ch.name},
    )
    db.commit()
    return {"id": ch.id, "code": ch.code, "name": ch.name, "status": ch.status, "master_id": ch.master_id}

# ============================================================================
# 2️⃣ OTA 수수료
# ============================================================================
@router.get("/commissions")
def list_commissions(
    channel: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    q = (
        db.query(
            OTACommission.id,
            OTAChannel.code.label("ch_code"),
            OTACommission.valid_from,
            OTACommission.valid_to,
            OTACommission.rate,
            OTACommission.note,
        )
        .join(OTAChannel, OTAChannel.id == OTACommission.channel_id)
    )
    if channel:
        q = q.filter(OTAChannel.code == channel)
    if date_from:
        q = q.filter(OTACommission.valid_to >= date_from)
    if date_to:
        q = q.filter(OTACommission.valid_from <= date_to)

    total = q.count()
    rows = q.order_by(asc(OTAChannel.code), asc(OTACommission.valid_from)).all()
    items = [{
        "id": r.id,
        "channel": r.ch_code,
        "valid_from": r.valid_from,
        "valid_to": r.valid_to,
        "rate": round((r.rate or 0.0) * 100.0, 2),
        "note": r.note or "",
    } for r in rows]
    return {"total": total, "items": items}

# ============================================================================
# 3️⃣ OTA 주문
# ============================================================================
@router.get("/orders")
def list_orders(
    q: str = "",
    channel: str = "",
    status: str = "",
    start: str = "",
    end: str = "",
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    page = max(1, page)
    size = max(1, min(100, size))
    stmt = db.query(OTAOrder)
    if q:
        like = f"%{q}%"
        stmt = stmt.filter(or_(OTAOrder.order_code.ilike(like), OTAOrder.guest_name.ilike(like)))
    if channel:
        stmt = stmt.filter(OTAOrder.channel == channel)
    if status:
        stmt = stmt.filter(OTAOrder.status == status)
    if start:
        stmt = stmt.filter(OTAOrder.check_in >= start)
    if end:
        stmt = stmt.filter(OTAOrder.check_in <= end)

    total = stmt.count()
    rows = (
        stmt.order_by(desc(OTAOrder.created_at))
            .offset((page - 1) * size)
            .limit(size)
            .all()
    )
    items = [{
        "id": r.id,
        "channel": r.channel,
        "order_code": r.order_code,
        "guest_name": r.guest_name,
        "check_in": r.check_in,
        "check_out": r.check_out,
        "status": r.status,
        "amount": r.amount,
        "currency": r.currency,
    } for r in rows]
    return {"total": total, "page": page, "size": size, "items": items}

# ============================================================================
# 4️⃣ OTA Summary — 매출 요약
# ============================================================================
@router.get("/summary")
def ota_summary(
    business_date: Optional[date] = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    if not business_date:
        raise HTTPException(status_code=422, detail=[{
            "type": "missing",
            "loc": ("query", "business_date"),
            "msg": "Field required",
        }])

    orders = db.query(OTAOrder).filter(OTAOrder.check_in == str(business_date)).all()

    summary: Dict[str, Dict[str, Any]] = {}
    for o in orders:
        ch = o.channel or "UNKNOWN"
        s = summary.setdefault(ch, {"gross": 0, "count": 0})
        s["gross"] += o.amount or 0
        s["count"] += 1

    result = []
    for ch, data in summary.items():
        gross = data["gross"]
        fee_pct = 15.0
        comm = (
            db.query(OTACommission.rate)
            .join(OTAChannel, OTAChannel.id == OTACommission.channel_id)
            .filter(OTAChannel.name == ch)
            .order_by(desc(OTACommission.valid_from))
            .first()
        )
        if comm:
            fee_pct = round((comm[0] or 0.0) * 100.0, 2)
        fee_amount = gross * (fee_pct / 100.0)
        net = gross - fee_amount
        result.append({
            "channel": ch,
            "gross": gross,
            "fee_pct": fee_pct,
            "fee_amount": fee_amount,
            "net": net,
            "count": data["count"],
        })

    total_gross = sum(r["gross"] for r in result)
    total_net = sum(r["net"] for r in result)

    return {
        "ok": True,
        "business_date": str(business_date),
        "items": result,
        "total": {"gross": total_gross, "net": total_net},
    }
