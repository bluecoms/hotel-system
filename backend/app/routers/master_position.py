# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/routers/master_positions.py
# Version   : 2025.10-28 · v1.0 (Initial Create · SSOT Stable)
# Purpose   : Hotel Admin — Master Position Router (/api/master/positions)
# ----------------------------------------------------------------------------
# 목적:
#   • 직위(Position) 기준정보 관리용 CRUD API
#   • MasterPosition 모델 + Pydantic 스키마 기반
#   • /options 엔드포인트 제공 → 프런트 v-select 선택지
# ----------------------------------------------------------------------------
# 구성:
#   • GET    /api/master/positions           → 목록 조회
#   • POST   /api/master/positions           → 신규 생성
#   • PUT    /api/master/positions/{id}      → 수정
#   • DELETE /api/master/positions/{id}      → 삭제(비활성)
#   • GET    /api/master/positions/options   → 옵션 목록 (활성만)
# ----------------------------------------------------------------------------
# 연계:
#   • Model : app.models.master_position.MasterPosition
#   • Schema: app.schemas.master_position.*
#   • Front : DialogEmployeeForm.vue → 직위(v-select)
# ============================================================================
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.core.auth import require_user, require_roles
from app.models.master_position import MasterPosition
from app.schemas.master_position import (
    MasterPositionIn,
    MasterPositionOut,
    MasterPositionOption,
)

router = APIRouter(
    prefix="/api/master/positions",
    tags=["master-positions"],
    dependencies=[Depends(require_user)],
)

# ─────────────────────────────────────────────
# 1️⃣ 목록 조회
# ─────────────────────────────────────────────
@router.get("", response_model=List[MasterPositionOut])
def list_positions(
    q: str = Query("", description="검색어 (code/name 부분일치)"),
    db: Session = Depends(get_db),
):
    """직위 목록 조회"""
    query = db.query(MasterPosition)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (MasterPosition.code.ilike(like)) | (MasterPosition.name.ilike(like))
        )
    rows = query.order_by(MasterPosition.order_no.asc(), MasterPosition.name.asc()).all()
    return rows


# ─────────────────────────────────────────────
# 2️⃣ 신규 생성
# ─────────────────────────────────────────────
@router.post("", response_model=MasterPositionOut, dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def create_position(data: MasterPositionIn, db: Session = Depends(get_db)):
    """직위 신규 등록"""
    exists = db.query(MasterPosition).filter(MasterPosition.code == data.code).first()
    if exists:
        raise HTTPException(status_code=400, detail="직위 코드가 이미 존재합니다.")

    obj = MasterPosition(**data.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ─────────────────────────────────────────────
# 3️⃣ 수정
# ─────────────────────────────────────────────
@router.put("/{pid}", response_model=MasterPositionOut, dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def update_position(pid: int, data: MasterPositionIn, db: Session = Depends(get_db)):
    """직위 정보 수정"""
    obj = db.get(MasterPosition, pid)
    if not obj:
        raise HTTPException(status_code=404, detail="직위를 찾을 수 없습니다.")

    for k, v in data.dict().items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


# ─────────────────────────────────────────────
# 4️⃣ 삭제(비활성)
# ─────────────────────────────────────────────
@router.delete("/{pid}", dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def delete_position(pid: int, db: Session = Depends(get_db)):
    """직위 삭제(비활성화 처리)"""
    obj = db.get(MasterPosition, pid)
    if not obj:
        raise HTTPException(status_code=404, detail="직위를 찾을 수 없습니다.")
    obj.is_active = False
    db.commit()
    return {"ok": True, "disabled": pid}


# ─────────────────────────────────────────────
# 5️⃣ 옵션 목록 (활성만)
# ─────────────────────────────────────────────
@router.get("/options", response_model=List[MasterPositionOption])
def position_options(db: Session = Depends(get_db)):
    """활성 직위 목록 (v-select용)"""
    rows = (
        db.query(MasterPosition)
        .filter(MasterPosition.is_active.is_(True))
        .order_by(MasterPosition.order_no.asc(), MasterPosition.name.asc())
        .all()
    )
    return [{"value": r.code, "title": r.name} for r in rows]
