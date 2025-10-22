# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/routers/master_property.py
# Version   : 2025.10-24 · v1.3 (CRUD Full + Global SSOT Stable)
# Purpose   : Hotel Admin — Global Properties Router (/api/properties)
# ----------------------------------------------------------------------------
# 목적:
#   • 지점(호텔) 코드/명칭 등 "전역 기준정보"를 제공하는 API
#   • 시스템 전역에서 공용으로 사용되므로 master 허브 하위가 아닌
#     /api/properties 엔드포인트로 유지한다. (전역화 정책)
# ----------------------------------------------------------------------------
# 기능:
#   • CRUD 전체 지원(GET/POST/PUT/DELETE)
#   • 최소 필드(code, name, is_active) 기반 구조
#   • 추후 확장: 주소/연락처/타임존 등 메타필드 추가 예정
# ----------------------------------------------------------------------------
# 연계:
#   • app/models/master_property.py    → MasterProperty ORM
#   • app/schemas/master_property.py   → PropertyCreate / PropertyOut
#   • app/routers/__init__.py          → include_all_routers(app) 일괄 등록
# ----------------------------------------------------------------------------
# 백엔드 계약:
#   - GET    /api/properties
#   - POST   /api/properties
#   - PUT    /api/properties/{code}
#   - DELETE /api/properties/{code}
# ----------------------------------------------------------------------------
# 사용처:
#   • 프런트엔드 기준정보 → PropertyTable.vue (MasterTable 기반)
#   • 시스템 전역 property_code 선택기(BizDatePicker, Upload 등)
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, Path, Body
from sqlalchemy.orm import Session
from typing import Optional, List
from app.schemas.master_property import PropertyCreate, PropertyOut
from app.models.master_property import MasterProperty
from app.db.session import get_db

# 전역 엔드포인트 유지 (전역화 정책)
router = APIRouter(prefix="/api/properties", tags=["properties"])

# ─────────────────────────────────────────────
# 1️⃣ 지점 목록 조회
# ─────────────────────────────────────────────
@router.get("/", response_model=List[PropertyOut], summary="지점 목록 조회")
def list_properties(db: Session = Depends(get_db)):
    """전 지점(Property) 목록을 반환한다."""
    return db.query(MasterProperty).order_by(MasterProperty.code.asc()).all()

# ─────────────────────────────────────────────
# 2️⃣ 지점 생성
# ─────────────────────────────────────────────
@router.post("/", response_model=PropertyOut, summary="지점 생성")
def create_property(body: PropertyCreate, db: Session = Depends(get_db)):
    """
    신규 지점 등록.
    - code 중복 시 400 반환
    """
    dup = db.query(MasterProperty).filter_by(code=body.code).first()
    if dup:
        raise HTTPException(status_code=400, detail="Property already exists")

    obj = MasterProperty(**body.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

# ─────────────────────────────────────────────
# 3️⃣ 지점 수정 (code 기반)
# ─────────────────────────────────────────────
@router.put("/{code}", response_model=PropertyOut, summary="지점 수정")
def update_property(
    code: str = Path(..., description="지점 코드"),
    body: dict = Body(..., example={"name": "지점명", "is_active": True}),
    db: Session = Depends(get_db),
):
    """
    기존 지점 정보 수정.
    - 존재하지 않으면 404
    - name, is_active 필드만 수정 가능
    """
    row = db.query(MasterProperty).filter_by(code=code).first()
    if not row:
        raise HTTPException(status_code=404, detail="Property not found")

    name: Optional[str] = body.get("name")
    is_active = body.get("is_active")

    if name is not None:
        row.name = str(name)
    if is_active is not None:
        row.is_active = bool(is_active)

    db.commit()
    db.refresh(row)
    return row

# ─────────────────────────────────────────────
# 4️⃣ 지점 삭제 (code 기반)
# ─────────────────────────────────────────────
@router.delete("/{code}", summary="지점 삭제")
def delete_property(
    code: str = Path(..., description="지점 코드"),
    db: Session = Depends(get_db),
):
    """지점 코드로 항목 삭제"""
    row = db.query(MasterProperty).filter_by(code=code).first()
    if not row:
        raise HTTPException(status_code=404, detail="Property not found")
    db.delete(row)
    db.commit()
    return {"ok": True, "deleted_code": code}
