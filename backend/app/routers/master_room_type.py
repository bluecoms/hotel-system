# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/routers/master_room_type.py
# Version   : 2025-11-09 · v1.1 (SSOT Stable · CRUD + Filter)
# Purpose   : Hotel Admin — 객실 타입 기준정보 API
# ----------------------------------------------------------------------------
# 목적:
#   • 객실 타입(RoomType) 기준정보 CRUD 제공
#   • /api/master/room-types
# ----------------------------------------------------------------------------
# 설계 원칙:
#   • MasterTable(SSOT) 규약 준수
#   • code 는 유니크 키 (예: STD, DLX, SUITE 등)
#   • name 은 사용자 표시명 (예: 스탠다드, 디럭스)
#   • is_active 로 사용 여부 제어
# ----------------------------------------------------------------------------
# 엔드포인트:
#   ✅ GET    /api/master/room-types        → 전체 목록 조회
#   ✅ POST   /api/master/room-types        → 신규 등록
#   ✅ PUT    /api/master/room-types/{code} → 수정
#   ✅ DELETE /api/master/room-types/{code} → 삭제
# ----------------------------------------------------------------------------
# 연계 구조:
#   • models.master_room_type.MasterRoomType
#   • schemas.master_room_type.{RoomTypeCreate, RoomTypeUpdate, RoomTypeOut}
#   • 프런트엔드 MasterData.vue > “운영 기준정보” 탭에서 관리됨
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.master_room_type import MasterRoomType
from app.schemas.master_room_type import RoomTypeCreate, RoomTypeUpdate, RoomTypeOut

# ─────────────────────────────────────────────
# Router 정의
# ─────────────────────────────────────────────
router = APIRouter(
    prefix="/api/master/room-types",
    tags=["master-room-types"],
)

# ============================================================================
# 1️⃣ 목록 조회 (필터 포함)
# ============================================================================
@router.get("", response_model=List[RoomTypeOut])
def list_room_types(
    is_active: bool = Query(None, description="활성 여부 필터 (True/False)"),
    db: Session = Depends(get_db),
):
    """
    객실 타입 기준정보 전체 조회  
    예: /api/master/room-types?is_active=true
    """
    q = db.query(MasterRoomType)
    if is_active is not None:
        q = q.filter(MasterRoomType.is_active == is_active)
    return q.order_by(MasterRoomType.order_no.asc(), MasterRoomType.id.asc()).all()


# ============================================================================
# 2️⃣ 신규 등록
# ============================================================================
@router.post("", response_model=RoomTypeOut)
def create_room_type(body: RoomTypeCreate, db: Session = Depends(get_db)):
    """
    신규 객실 타입 등록
    - code 중복 시 400 반환
    """
    if db.query(MasterRoomType).filter(MasterRoomType.code == body.code).first():
        raise HTTPException(status_code=400, detail="이미 존재하는 객실 타입 코드입니다.")

    obj = MasterRoomType(**body.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ============================================================================
# 3️⃣ 수정
# ============================================================================
@router.put("/{code}", response_model=RoomTypeOut)
def update_room_type(code: str, body: RoomTypeUpdate, db: Session = Depends(get_db)):
    """
    기존 객실 타입 수정
    - 존재하지 않으면 404 반환
    """
    obj = db.query(MasterRoomType).filter(MasterRoomType.code == code).first()
    if not obj:
        raise HTTPException(status_code=404, detail="해당 객실 타입을 찾을 수 없습니다.")

    for k, v in body.dict(exclude_unset=True).items():
        setattr(obj, k, v)

    db.commit()
    db.refresh(obj)
    return obj


# ============================================================================
# 4️⃣ 삭제
# ============================================================================
@router.delete("/{code}")
def delete_room_type(code: str, db: Session = Depends(get_db)):
    """
    객실 타입 삭제
    - 존재하지 않으면 404 반환
    """
    obj = db.query(MasterRoomType).filter(MasterRoomType.code == code).first()
    if not obj:
        raise HTTPException(status_code=404, detail="해당 객실 타입을 찾을 수 없습니다.")

    db.delete(obj)
    db.commit()
    return {"ok": True, "deleted_code": code}


# ============================================================================
# ✅ EOF — app/routers/master_room_type.py (v1.1 · SSOT Stable)
# ============================================================================
