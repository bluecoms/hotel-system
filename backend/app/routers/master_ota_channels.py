# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/routers/master_ota_channels.py
# Version   : 2025.10-31 · v1.3 (Prefix/Imports Final · SSOT Stable)
# Purpose   : Hotel Admin — Master OTA Channel Router (/api/master/ota-channels)
# ----------------------------------------------------------------------------
# 목적:
#   • OTA 채널(Booking.com, Agoda, Expedia 등) 기준정보 관리 API
#   • OTA 연동 및 수수료(commission) 테이블의 기준 채널 데이터로 사용
# ----------------------------------------------------------------------------
# 기능:
#   • CRUD 전체 지원 (GET / POST / PUT / DELETE)
#   • code, name, is_active 필드 중심 단순 구조
#   • OTA 커미션(/api/ota/commissions)에서 참조
# ----------------------------------------------------------------------------
# 연계:
#   • app/models/master_ota_channel.py   → MasterOtaChannel ORM
#   • app/schemas/master_ota_channel.py  → MasterOtaChannelIn / MasterOtaChannelOut
#   • app/routers/__init__.py            → include_all_routers(app)
# ----------------------------------------------------------------------------
# 변경 이력:
#   v1.0 · 2025-10-25 : 최초 작성
#   v1.1 · 2025-10-31 : '/api' 제거 (중복 방지)
#   v1.2 · 2025-10-31 : prefix 이중 중복 제거
#   v1.3 · 2025-10-31 : ✅ SSOT 네이밍 통합 및 주석 구조 정비
# ----------------------------------------------------------------------------
# Naming 규칙 (SSOT 고정)
#   • Model  : app/models/master_ota_channel.py     → 단수
#   • Schema : app/schemas/master_ota_channel.py    → 단수
#   • Router : app/routers/master_ota_channels.py   → 복수
# ============================================================================
from fastapi import APIRouter, Depends, HTTPException, Path, Body
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.master_ota_channel import MasterOtaChannel
from app.schemas.master_ota_channel import MasterOtaChannelIn, MasterOtaChannelOut
from app.core.auth import require_roles, require_token_local

# ============================================================================
# Router 선언
# ============================================================================
router = APIRouter(
    prefix="/api/master/ota-channels",  # ✅ '/api/master/ota-channels' 로 정확히 매핑
    tags=["master-ota-channels"],
    dependencies=[
        Depends(require_token_local),
        Depends(require_roles(["ADMIN", "SUPERADMIN"])),
    ],
)

# ============================================================================
# 1️⃣ 목록 조회
# ============================================================================
@router.get(
    "",
    response_model=List[MasterOtaChannelOut],
    summary="OTA 채널 목록 조회",
)
def list_ota_channels(db: Session = Depends(get_db)):
    """OTA 채널 전체 목록 조회"""
    return db.query(MasterOtaChannel).order_by(MasterOtaChannel.order_no.asc()).all()

# ============================================================================
# 2️⃣ 채널 등록
# ============================================================================
@router.post(
    "",
    response_model=MasterOtaChannelOut,
    summary="OTA 채널 등록",
)
def create_ota_channel(body: MasterOtaChannelIn, db: Session = Depends(get_db)):
    """신규 OTA 채널 등록 — code 중복 방지"""
    dup = db.query(MasterOtaChannel).filter_by(code=body.code).first()
    if dup:
        raise HTTPException(status_code=409, detail="이미 존재하는 코드입니다.")
    row = MasterOtaChannel(**body.dict())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

# ============================================================================
# 3️⃣ 채널 수정
# ============================================================================
@router.put(
    "/{id}",
    response_model=MasterOtaChannelOut,
    summary="OTA 채널 수정",
)
def update_ota_channel(
    id: int = Path(..., description="채널 ID"),
    body: MasterOtaChannelIn = Body(...),
    db: Session = Depends(get_db),
):
    """기존 OTA 채널 수정"""
    row = db.get(MasterOtaChannel, id)
    if not row:
        raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
    for k, v in body.dict(exclude_unset=True).items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row

# ============================================================================
# 4️⃣ 채널 삭제
# ============================================================================
@router.delete(
    "/{id}",
    summary="OTA 채널 삭제",
)
def delete_ota_channel(
    id: int = Path(..., description="채널 ID"),
    db: Session = Depends(get_db),
):
    """OTA 채널 삭제"""
    row = db.get(MasterOtaChannel, id)
    if not row:
        raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
    db.delete(row)
    db.commit()
    return {"ok": True, "deleted_id": id}
