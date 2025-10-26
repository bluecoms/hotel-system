# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/routers/master_property.py
# Version   : 2025.10-26 · v2.0 (SSOT 정합판 · Master CRUD 전용)
# Purpose   : Hotel Admin — MasterProperty Router (/api/master/properties)
# ----------------------------------------------------------------------------
# 목적:
#   • 관리자가 지점(호텔) 코드/명칭 등 "기준정보(SSOT)"를 관리하는 전용 API
#   • 운영용 Property 테이블(app/models/property.py)과는 구분된다.
#   • 마스터에서 등록/수정된 데이터는 운영 Property로 자동 싱크된다.
# ----------------------------------------------------------------------------
# 기능:
#   ✅ CRUD 전체 지원(GET/POST/PUT/DELETE)
#   ✅ 코드(code) 중복 방지 및 활성화 플래그 관리
#   ✅ 추후 확장: 주소/연락처/타임존 등 메타필드 추가 가능
# ----------------------------------------------------------------------------
# 연계:
#   • app/models/master_property.py    → MasterProperty ORM (관리자용)
#   • app/schemas/master_property.py   → MasterPropertyCreate / MasterPropertyOut
#   • app/models/property.py           → Property ORM (운영용)
#   • app/routers/properties.py        → /api/properties (운영 조회 전용)
# ----------------------------------------------------------------------------
# 정책:
#   - 관리자만 접근 가능 (X-Internal-Token 기반 인증)
#   - /api/master/properties 경로는 SSOT 관리 전용으로 유지
#   - 운영 API는 /api/properties 로 분리 (직접 접근 금지)
# ----------------------------------------------------------------------------
# 백엔드 계약:
#   - GET    /api/master/properties
#   - POST   /api/master/properties
#   - PUT    /api/master/properties/{code}
#   - DELETE /api/master/properties/{code}
# ----------------------------------------------------------------------------
# 사용처:
#   • Docs Admin / 기준정보 관리 페이지
#   • 운영 Property 테이블 동기화 파이프라인
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, Path, Body
from sqlalchemy.orm import Session
from typing import Optional, List
from app.schemas.master_property import MasterPropertyCreate, MasterPropertyOut
from app.models.master_property import MasterProperty
from app.models.property import Property
from app.db.session import get_db

router = APIRouter(prefix="/api/master/properties", tags=["master-properties"])

# ─────────────────────────────────────────────
# 1️⃣ 마스터 지점 목록 조회
# ─────────────────────────────────────────────
@router.get("", response_model=List[MasterPropertyOut], summary="마스터 지점 목록 조회")
def list_master_properties(db: Session = Depends(get_db)):
    """모든 마스터 지점(Property) 정보를 반환한다."""
    return db.query(MasterProperty).order_by(MasterProperty.code.asc()).all()


# ─────────────────────────────────────────────
# 2️⃣ 마스터 지점 생성
# ─────────────────────────────────────────────
@router.post("/", response_model=MasterPropertyOut, summary="마스터 지점 생성")
def create_master_property(body: MasterPropertyCreate, db: Session = Depends(get_db)):
    """
    신규 지점 등록.
    - code 중복 시 400 반환
    - 등록 후 운영 Property 테이블에 자동 반영
    """
    dup = db.query(MasterProperty).filter_by(code=body.code).first()
    if dup:
        raise HTTPException(status_code=400, detail="Property code already exists")

    obj = MasterProperty(**body.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)

    # 운영 Property 테이블에 동기화
    sync_property_to_operating(obj, db)
    return obj


# ─────────────────────────────────────────────
# 3️⃣ 마스터 지점 수정 (code 기반)
# ─────────────────────────────────────────────
@router.put("/{code}", response_model=MasterPropertyOut, summary="마스터 지점 수정")
def update_master_property(
    code: str = Path(..., description="지점 코드"),
    body: dict = Body(..., example={"name": "지점명", "is_active": True}),
    db: Session = Depends(get_db),
):
    """
    기존 마스터 지점 정보 수정.
    - 존재하지 않으면 404
    - 수정 후 운영 Property에도 반영
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

    # 동기화
    sync_property_to_operating(row, db)
    return row


# ─────────────────────────────────────────────
# 4️⃣ 마스터 지점 삭제 (code 기반)
# ─────────────────────────────────────────────
@router.delete("/{code}", summary="마스터 지점 삭제")
def delete_master_property(
    code: str = Path(..., description="지점 코드"),
    db: Session = Depends(get_db),
):
    """
    지점 코드로 마스터 항목 삭제.
    - 삭제 후 운영 Property 테이블에서도 삭제 처리
    """
    row = db.query(MasterProperty).filter_by(code=code).first()
    if not row:
        raise HTTPException(status_code=404, detail="Property not found")

    # 운영 Property 삭제
    db.query(Property).filter_by(code=code).delete()

    db.delete(row)
    db.commit()
    return {"ok": True, "deleted_code": code}


# ─────────────────────────────────────────────
# ⚙️ 헬퍼: 운영 Property 테이블로 동기화
# ─────────────────────────────────────────────
def sync_property_to_operating(master_obj: MasterProperty, db: Session):
    """
    MasterProperty → Property 테이블 동기화.
    - 존재 시 업데이트, 없으면 신규 생성
    """
    prop = db.query(Property).filter_by(code=master_obj.code).first()
    if prop:
        prop.name = master_obj.name
        prop.is_active = master_obj.is_active
    else:
        prop = Property(
            code=master_obj.code,
            name=master_obj.name,
            is_active=master_obj.is_active,
        )
        db.add(prop)
    db.commit()
