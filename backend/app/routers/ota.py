# app/routers/ota.py
from typing import Optional, List
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, Header, Request
from sqlalchemy.orm import Session
from sqlalchemy import asc, text
import json

from app.core.auth import require_roles
from app.core.locale import set_lang
from app.core.i18n import t as _t
from app.core.audit import write_audit

from app.db.session import get_db
from app.models import OTAChannel, OTACommission
from app.schemas import (
    OTAChannelOut, OTAChannelCreate,
    OTACommissionOut, OTACommissionCreate, OTACommissionUpdate,
)

router = APIRouter(
    prefix="/api/ota",
    tags=["ota"],
    dependencies=[Depends(set_lang), Depends(require_roles(["ADMIN"]))],
)

# ─────────────────────────────────────────────────────────────────────────────
# 유틸

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

# ─────────────────────────────────────────────────────────────────────────────
# 채널

@router.get("/channels")
def list_channels(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    total = db.query(OTAChannel).count()
    rows = db.query(OTAChannel).order_by(asc(OTAChannel.id)).offset(offset).limit(limit).all()
    return {"total": total, "items": rows}

@router.post("/channels", response_model=OTAChannelOut, status_code=status.HTTP_201_CREATED)
def create_channel(
    request: Request,
    payload: OTAChannelCreate,
    db: Session = Depends(get_db),
    x_internal_token: Optional[str] = Header(None),
):
    lang = getattr(request.state, "lang", "en")

    if db.query(OTAChannel).filter(OTAChannel.code == payload.code).first():
        raise HTTPException(status_code=400, detail=_t("error.duplicate", lang))

    ch = OTAChannel(code=payload.code, name=payload.name)
    db.add(ch); db.commit(); db.refresh(ch)

    write_audit(
        db,
        x_internal_token or "SYSTEM",
        "OTA_CHANNEL_CREATE",
        f"channel_code={ch.code}",
        {"lang": lang, "channel_id": ch.id, "name": ch.name},
    )
    db.commit()
    return ch

@router.get("/channels/{channel_id}/history", response_model=List[OTACommissionOut])
def channel_history(request: Request, channel_id: int, db: Session = Depends(get_db)):
    lang = getattr(request.state, "lang", "en")

    ch_code = db.query(OTAChannel.code).filter(OTAChannel.id == channel_id).scalar()
    if not ch_code:
        raise HTTPException(status_code=404, detail=_t("error.not_found", lang))

    rows = (
        db.query(
            OTACommission.id,
            OTACommission.valid_from,
            OTACommission.valid_to,
            OTACommission.rate,
            OTACommission.note,
        )
        .filter(OTACommission.channel_id == channel_id)
        .order_by(asc(OTACommission.valid_from))
        .all()
    )

    out: List[OTACommissionOut] = []
    for r in rows:
        out.append(
            OTACommissionOut(
                id=r.id,
                channel=ch_code,
                valid_from=r.valid_from,
                valid_to=r.valid_to,
                rate=round((r.rate or 0.0) * 100.0, 4),
                note=r.note,
            )
        )
    return out

# ─────────────────────────────────────────────────────────────────────────────
# 커미션

@router.get("/commissions")
def list_commissions(
    channel: Optional[str] = Query(None, description="채널 코드"),
    date_from: Optional[date] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[date] = Query(None, description="YYYY-MM-DD"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
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
    q = q.filter(OTACommission.rate >= 0.0, OTACommission.rate <= 1.0)

    total = q.count()
    rows = q.order_by(asc(OTAChannel.code), asc(OTACommission.valid_from)).offset(offset).limit(limit).all()

    out: List[OTACommissionOut] = []
    for r in rows:
        out.append(
            OTACommissionOut(
                id=r.id,
                channel=r.ch_code,
                valid_from=r.valid_from,
                valid_to=r.valid_to,
                rate=round((r.rate or 0.0) * 100.0, 4),
                note=r.note,
            )
        )
    return {"total": total, "items": out}

@router.post("/commissions", response_model=OTACommissionOut, status_code=status.HTTP_201_CREATED)
def create_commission(
    request: Request,
    payload: OTACommissionCreate,
    db: Session = Depends(get_db),
    x_internal_token: Optional[str] = Header(None),
):
    lang = getattr(request.state, "lang", "en")

    if payload.valid_from > payload.valid_to:
        raise HTTPException(status_code=422, detail=_t("error.date_invert", lang))

    ch = _get_channel_by_code(db, payload.channel, lang)

    if _has_overlap(db, ch.id, payload.valid_from, payload.valid_to):
        raise HTTPException(status_code=409, detail=_t("error.duplicate", lang))

    obj = OTACommission(
        channel_id=ch.id,
        valid_from=payload.valid_from,
        valid_to=payload.valid_to,
        rate=(payload.rate or 0.0) / 100.0,
        note=payload.note,
        effective_date=payload.valid_from,
    )
    db.add(obj); db.commit(); db.refresh(obj)

    write_audit(
        db,
        x_internal_token or "SYSTEM",
        "OTA_COMMISSION_CREATE",
        f"commission_id={obj.id}",
        {
            "lang": lang,
            "commission_id": obj.id,
            "channel": ch.code,
            "valid_from": str(obj.valid_from),
            "valid_to": str(obj.valid_to),
            "rate_pct": round((obj.rate or 0.0) * 100.0, 4),
            "note": obj.note,
        },
    )
    db.commit()

    return OTACommissionOut(
        id=obj.id,
        channel=ch.code,
        valid_from=obj.valid_from,
        valid_to=obj.valid_to,
        rate=round((obj.rate or 0.0) * 100.0, 4),
        note=obj.note,
    )

@router.put("/commissions/{commission_id}", response_model=OTACommissionOut)
def update_commission(
    request: Request,
    commission_id: int = Path(..., ge=1),
    payload: OTACommissionUpdate = None,
    db: Session = Depends(get_db),
    x_internal_token: Optional[str] = Header(None),
):
    lang = getattr(request.state, "lang", "en")

    obj = db.query(OTACommission).filter(OTACommission.id == commission_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail=_t("error.not_found", lang))

    new_from = payload.valid_from if payload and payload.valid_from is not None else obj.valid_from
    new_to = payload.valid_to if payload and payload.valid_to is not None else obj.valid_to
    if new_from > new_to:
        raise HTTPException(status_code=422, detail=_t("error.date_invert", lang))

    new_channel_id = obj.channel_id
    ch_code_before = db.query(OTAChannel.code).filter(OTAChannel.id == obj.channel_id).scalar()
    if payload and payload.channel is not None:
        ch = _get_channel_by_code(db, payload.channel, lang)
        new_channel_id = ch.id

    if _has_overlap(db, new_channel_id, new_from, new_to, exclude_id=obj.id):
        raise HTTPException(status_code=409, detail=_t("error.duplicate", lang))

    obj.channel_id = new_channel_id
    obj.valid_from = new_from
    obj.valid_to = new_to
    obj.effective_date = new_from
    if payload and payload.rate is not None:
        obj.rate = (payload.rate or 0.0) / 100.0
    if payload and payload.note is not None:
        obj.note = payload.note

    db.add(obj); db.commit(); db.refresh(obj)

    ch_code_after = db.query(OTAChannel.code).filter(OTAChannel.id == obj.channel_id).scalar()

    write_audit(
        db,
        x_internal_token or "SYSTEM",
        "OTA_COMMISSION_UPDATE",
        f"commission_id={obj.id}",
        {
            "lang": lang,
            "channel_before": ch_code_before,
            "channel_after": ch_code_after,
            "valid_from": str(obj.valid_from),
            "valid_to": str(obj.valid_to),
            "rate_pct": round((obj.rate or 0.0) * 100.0, 4),
            "note": obj.note,
        },
    )
    db.commit()

    return OTACommissionOut(
        id=obj.id,
        channel=ch_code_after,
        valid_from=obj.valid_from,
        valid_to=obj.valid_to,
        rate=round((obj.rate or 0.0) * 100.0, 4),
        note=obj.note,
    )
