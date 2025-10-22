# app/routers/keywords.py
# -*- coding: utf-8 -*-
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, Body, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.core.locale import set_lang
from app.core.auth import require_roles, require_token_local
from app.db.session import get_db
from app.models.keyword import Keyword
from app.schemas.keywords import KeywordIn, KeywordOut

router = APIRouter(
    prefix="/api/keywords",
    tags=["keywords"],
    dependencies=[
        Depends(set_lang),
        Depends(require_token_local),
        Depends(require_roles(["ADMIN", "SUPERADMIN"])),
    ],
)

@router.get("", response_model=Dict[str, Any])
def list_keywords(
    q: str = "",
    group_name: str = "",
    active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    page = max(1, page)
    size = max(1, min(200, size))

    base = db.query(Keyword)
    if q:
        like = f"%{q}%"
        base = base.filter(or_(Keyword.k.ilike(like), Keyword.v.ilike(like)))
    if group_name:
        base = base.filter(Keyword.group_name == group_name)
    if active is not None:
        base = base.filter(Keyword.is_active == bool(active))

    total = base.count()
    rows = (
        base.order_by(Keyword.group_name.asc(), Keyword.weight.desc(), Keyword.k.asc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
    )

    items = [
        {
            "id": r.id,
            "group_name": r.group_name,
            "k": r.k,
            "v": r.v,
            "weight": r.weight,
            "is_active": r.is_active,
            "created_at": r.created_at,
        }
        for r in rows
    ]
    return {"total": int(total), "page": page, "size": size, "items": items}

@router.post("", response_model=Dict[str, Any])
def create_keyword(
    body: KeywordIn = Body(...),
    db: Session = Depends(get_db),
):
    has = (
        db.query(Keyword)
        .filter(Keyword.group_name == body.group_name, Keyword.k == body.k)
        .first()
    )
    if has:
        raise HTTPException(400, "exists")

    obj = Keyword(
        group_name=body.group_name,
        k=body.k,
        v=body.v,
        weight=int(body.weight or 0),
        is_active=bool(body.is_active),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return {"ok": True, "id": obj.id}

@router.put("/{kid}", response_model=Dict[str, Any])
def update_keyword(
    kid: int,
    body: KeywordIn = Body(...),
    db: Session = Depends(get_db),
):
    r = db.get(Keyword, kid)
    if not r:
        raise HTTPException(404, "not-found")

    conflict = (
        db.query(Keyword)
        .filter(Keyword.group_name == body.group_name, Keyword.k == body.k, Keyword.id != kid)
        .first()
    )
    if conflict:
        raise HTTPException(400, "exists")

    r.group_name = body.group_name
    r.k = body.k
    r.v = body.v
    r.weight = int(body.weight or 0)
    r.is_active = bool(body.is_active)
    db.commit()
    return {"ok": True}

@router.delete("/{kid}", response_model=Dict[str, Any])
def delete_keyword(
    kid: int,
    db: Session = Depends(get_db),
):
    r = db.get(Keyword, kid)
    if not r:
        raise HTTPException(404, "not-found")
    db.delete(r)
    db.commit()
    return {"ok": True}

# === OTA 관련 유틸 (기존 main.py 기능 보존) ===
def load_ota_alias_and_fee(db: Session):
    """
    - sales.channel.alias: k(패턴, 파이프 구분) → v(표준 채널명-대문자)
    - sales.channel.fee  : k(표준 채널명) → v(수수료 %, float)
    """
    # alias
    alias_rows = (
        db.query(Keyword)
        .filter(Keyword.group_name == "sales.channel.alias", Keyword.is_active.is_(True))
        .all()
    )
    alias_map: dict[str, str] = {}
    for r in alias_rows:
        canonical = (r.v or "").strip().upper()
        for piece in (r.k or "").split("|"):
            piece = piece.strip().lower()
            if piece and canonical:
                alias_map[piece] = canonical

    # fee
    fee_rows = (
        db.query(Keyword)
        .filter(Keyword.group_name == "sales.channel.fee", Keyword.is_active.is_(True))
        .all()
    )
    fee_map: dict[str, float] = {}
    for r in fee_rows:
        key = (r.k or "").strip().upper()
        try:
            fee_map[key] = float((r.v or "0").strip())
        except Exception:
            fee_map[key] = 0.0

    return alias_map, fee_map
