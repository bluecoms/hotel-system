# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/routers/master_positions.py
# Version   : 2025.10-31 · v1.1 (3.8 Safe OR · Pydantic v2 · SSOT Stable)
# Purpose   : Hotel Admin — Master Position Router (/api/master/positions)
# ----------------------------------------------------------------------------
# 목적:
#   • 직위(Position) 기준정보 관리용 CRUD API
#   • MasterPosition 모델 + Pydantic 스키마 기반
#   • /options 엔드포인트 제공 → 프런트 v-select 선택지
# ----------------------------------------------------------------------------
# 구성:
#   • GET    /api/master/positions           → 목록 조회(부분검색: code/name)
#   • POST   /api/master/positions           → 신규 생성
#   • PUT    /api/master/positions/{id}      → 수정(전체 업데이트)
#   • DELETE /api/master/positions/{id}      → 삭제(비활성 처리)
#   • GET    /api/master/positions/options   → 옵션 목록 (활성만)
# ----------------------------------------------------------------------------
# 연계:
#   • Model : app.models.master_position.MasterPosition
#   • Schema: app.schemas.master_position.{MasterPositionIn, MasterPositionOut, MasterPositionOption}
#   • Front : DialogEmployeeForm.vue → 직위(v-select)
# ============================================================================
from __future__ import annotations

from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

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
    dependencies=[Depends(require_user)],  # 내부 토큰/세션 인증 공통
)

# ─────────────────────────────────────────────
# 1️⃣ 목록 조회 (부분검색: code/name)
# ─────────────────────────────────────────────
@router.get("", response_model=List[MasterPositionOut])
def list_positions(
    q: str = Query("", description="검색어 (code/name 부분일치)"),
    db: Session = Depends(get_db),
):
    """
    직위 목록 조회
    - q가 주어지면 code/name ILIKE 부분일치 검색
    - order_no, name 기준 정렬
    """
    query = db.query(MasterPosition)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                MasterPosition.code.ilike(like),
                MasterPosition.name.ilike(like),
            )
        )
    rows = (
        query.order_by(MasterPosition.order_no.asc(), MasterPosition.name.asc())
        .all()
    )
    return rows

# ─────────────────────────────────────────────
# 2️⃣ 신규 생성
# ─────────────────────────────────────────────
@router.post(
    "",
    response_model=MasterPositionOut,
    dependencies=[Depends(require_roles(["SUPERADMIN"]))],
)
def create_position(data: MasterPositionIn, db: Session = Depends(get_db)):
    """
    직위 신규 등록
    - code 중복 금지
    """
    exists = db.query(MasterPosition).filter(MasterPosition.code == data.code).first()
    if exists:
        raise HTTPException(status_code=400, detail="직위 코드가 이미 존재합니다.")

    # Pydantic v2: model_dump() 사용
    obj = MasterPosition(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

# ─────────────────────────────────────────────
# 3️⃣ 수정 (전체 업데이트)
# ─────────────────────────────────────────────
@router.put(
    "/{pid}",
    response_model=MasterPositionOut,
    dependencies=[Depends(require_roles(["SUPERADMIN"]))],
)
def update_position(pid: int, data: MasterPositionIn, db: Session = Depends(get_db)):
    """
    직위 정보 수정 (전체 필드 업데이트)
    - 존재하지 않으면 404
    """
    obj = db.get(MasterPosition, pid)
    if not obj:
        raise HTTPException(status_code=404, detail="직위를 찾을 수 없습니다.")

    payload = data.model_dump()
    for k, v in payload.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

# ─────────────────────────────────────────────
# 4️⃣ 삭제(비활성)
# ─────────────────────────────────────────────
@router.delete("/{pid}", dependencies=[Depends(require_roles(["SUPERADMIN"]))])
def delete_position(pid: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    직위 삭제(비활성화 처리)
    - 실제 삭제 대신 is_active=False
    """
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
    """
    활성 직위 목록 (v-select 옵션)
    - value: code
    - title: name
    """
    rows = (
        db.query(MasterPosition)
        .filter(MasterPosition.is_active.is_(True))
        .order_by(MasterPosition.order_no.asc(), MasterPosition.name.asc())
        .all()
    )
    return [{"value": r.code, "title": r.name} for r in rows]
