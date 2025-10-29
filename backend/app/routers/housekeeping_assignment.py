# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/routers/housekeeping_assignment.py
# Version   : 2025-11-11 · v1.0 (CRUD · SSOT 규격)
# ============================================================================
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.db.session import get_db
from app.core.auth import require_token_local, require_roles
from app.schemas.housekeeping_assignment import AssignmentOut, AssignmentCreate
from app.services.housekeeping_assignment_service import upsert_assignments, list_assignments

router = APIRouter(
    prefix="/api/housekeeping/assignments",
    tags=["housekeeping-assignments"],
    dependencies=[Depends(require_token_local), Depends(require_roles(["ADMIN", "SUPERADMIN", "HK"]))],
)

@router.get("", response_model=List[AssignmentOut])
def get_assignments(
    business_date: str = Query(...),
    property_code: str = Query("MOP"),
    db: Session = Depends(get_db),
):
    """업무일자별 객실 배정 목록"""
    return list_assignments(db, business_date, property_code)


@router.post("/bulk", response_model=Dict[str, Any])
def post_bulk_assignments(
    body: List[AssignmentCreate] = Body(..., description="객실 배정 목록"),
    db: Session = Depends(get_db),
):
    """여러 객실 배정 일괄 저장"""
    count = upsert_assignments(db, [b.dict() for b in body])
    return {"ok": True, "updated": count}
