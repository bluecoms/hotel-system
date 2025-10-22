# -*- coding: utf-8 -*-
# version: 2025-10-18 v1.0 (Master Ranks Router)
"""
Hotel Admin — Master Ranks Router (/api/master/ranks)
────────────────────────────────────────────
목적:
  • 직급(Ranks) 기준정보 CRUD
  • /api/master 네임스페이스 내 통합 관리
────────────────────────────────────────────
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models import MasterRank
from app.schemas import MasterRankIn, MasterRankOut
from app.core.auth import require_roles, require_token_local

# ─────────────────────────────────────────────
# Router 설정
# ─────────────────────────────────────────────
router = APIRouter(
    prefix="/api/master/ranks",
    tags=["master-ranks"],
    dependencies=[
        Depends(require_token_local),
        Depends(require_roles(["ADMIN", "SUPERADMIN"]))
    ],
)

# ─────────────────────────────────────────────
# 목록 조회
# ─────────────────────────────────────────────
@router.get("", response_model=dict, summary="직급 목록 조회")
def list_ranks(db: Session = Depends(get_db)):
    """전체 직급 목록"""
    items = (
        db.query(MasterRank)
        .order_by(MasterRank.order_no.asc().nulls_last(), MasterRank.name.asc())
        .all()
    )
    return {"ok": True, "items": [MasterRankOut.model_validate(x) for x in items]}


# ─────────────────────────────────────────────
# 생성
# ─────────────────────────────────────────────
@router.post("", response_model=MasterRankOut, summary="직급 생성")
def create_rank(body: MasterRankIn, db: Session = Depends(get_db)):
    """직급 신규 생성"""
    exists = db.query(MasterRank).filter(MasterRank.code == body.code).first()
    if exists:
        raise HTTPException(status_code=409, detail=f"이미 존재하는 코드: {body.code}")
    rank = MasterRank(**body.dict())
    db.add(rank)
    db.commit()
    db.refresh(rank)
    return rank


# ─────────────────────────────────────────────
# 수정
# ─────────────────────────────────────────────
@router.patch("/{rid}", response_model=MasterRankOut, summary="직급 수정")
def update_rank(rid: int, body: MasterRankIn, db: Session = Depends(get_db)):
    """직급 정보 수정"""
    rank = db.query(MasterRank).get(rid)
    if not rank:
        raise HTTPException(status_code=404, detail="Rank not found")
    for k, v in body.dict().items():
        setattr(rank, k, v)
    db.commit()
    db.refresh(rank)
    return rank


# ─────────────────────────────────────────────
# 삭제
# ─────────────────────────────────────────────
@router.delete("/{rid}", summary="직급 삭제")
def delete_rank(rid: int, db: Session = Depends(get_db)):
    """직급 삭제"""
    rank = db.query(MasterRank).get(rid)
    if not rank:
        raise HTTPException(status_code=404, detail="Rank not found")
    db.delete(rank)
    db.commit()
    return {"ok": True}
