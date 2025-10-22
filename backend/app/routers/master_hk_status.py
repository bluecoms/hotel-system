# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/routers/master_hk_status.py
# Version   : 2025.10-25 · v1.1 (Add OperationID · SSOT Stable)
# Purpose   : Hotel Admin — Master Housekeeping Status Router (/api/master/hk-status)
# ----------------------------------------------------------------------------
# 목적:
#   • 하우스키핑(Housekeeping) 상태코드 기준정보 관리
#   • 객실 상태(청소/점검/비가용 등)를 코드 기반으로 표준화
# ----------------------------------------------------------------------------
# 기능:
#   • CRUD 전체 지원 (GET / POST / PUT / DELETE)
#   • code, name, is_active 필드 기반 간결한 구조
#   • 향후 하우스키핑 태스크(Task) 및 상태전이(Transition) 로직과 연계 예정
# ----------------------------------------------------------------------------
# 연계:
#   • app/models/master_hk_status.py   → MasterHkStatus ORM
#   • app/schemas/master_hk_status.py  → MasterHkStatusIn / MasterHkStatusOut
#   • app/routers/__init__.py          → include_all_routers(app) 일괄 등록
#   • 프런트엔드: HkStatusTable.vue (MasterTable 기반)
# ----------------------------------------------------------------------------
# 백엔드 계약:
#   - GET    /api/master/hk-status
#   - POST   /api/master/hk-status
#   - PUT    /api/master/hk-status/{id}
#   - DELETE /api/master/hk-status/{id}
# ============================================================================
from fastapi import APIRouter, Depends, HTTPException, Path, Body
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.master_hk_status import MasterHkStatus
from app.schemas.master_hk_status import MasterHkStatusIn, MasterHkStatusOut
from app.core.auth import require_roles, require_token_local

# ─────────────────────────────────────────────
# Router 선언
# ─────────────────────────────────────────────
router = APIRouter(
    prefix="/api/master/hk-status",
    tags=["master-hk-status"],
    dependencies=[
        Depends(require_token_local),
        Depends(require_roles(["ADMIN", "SUPERADMIN"])),
    ],
)

# ─────────────────────────────────────────────
# 1️⃣ 목록 조회
# ─────────────────────────────────────────────
@router.get(
    "",
    response_model=List[MasterHkStatusOut],
    summary="하우스키핑 상태 목록 조회",
    operation_id="list_master_hk_status",
)
def list_hk_status(db: Session = Depends(get_db)):
    """하우스키핑 상태 전체 목록 조회"""
    return db.query(MasterHkStatus).order_by(MasterHkStatus.code.asc()).all()


# ─────────────────────────────────────────────
# 2️⃣ 상태 생성
# ─────────────────────────────────────────────
@router.post(
    "",
    response_model=MasterHkStatusOut,
    summary="하우스키핑 상태 등록",
    operation_id="create_master_hk_status",
)
def create_hk_status(body: MasterHkStatusIn, db: Session = Depends(get_db)):
    """신규 상태코드 등록 — code 중복 방지"""
    dup = db.query(MasterHkStatus).filter_by(code=body.code).first()
    if dup:
        raise HTTPException(status_code=409, detail="이미 존재하는 코드입니다.")
    row = MasterHkStatus(**body.dict())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# ─────────────────────────────────────────────
# 3️⃣ 상태 수정
# ─────────────────────────────────────────────
@router.put(
    "/{id}",
    response_model=MasterHkStatusOut,
    summary="하우스키핑 상태 수정",
    operation_id="update_master_hk_status",
)
def update_hk_status(
    id: int = Path(..., description="상태 ID"),
    body: MasterHkStatusIn = Body(...),
    db: Session = Depends(get_db),
):
    """기존 상태코드 수정"""
    row = db.query(MasterHkStatus).get(id)
    if not row:
        raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
    for k, v in body.dict().items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


# ─────────────────────────────────────────────
# 4️⃣ 상태 삭제
# ─────────────────────────────────────────────
@router.delete(
    "/{id}",
    summary="하우스키핑 상태 삭제",
    operation_id="delete_master_hk_status",
)
def delete_hk_status(
    id: int = Path(..., description="상태 ID"),
    db: Session = Depends(get_db),
):
    """하우스키핑 상태코드 삭제"""
    row = db.query(MasterHkStatus).get(id)
    if not row:
        raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
    db.delete(row)
    db.commit()
    return {"ok": True, "deleted_id": id}
