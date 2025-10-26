# app/routers/housekeeping_task.py
# =============================================================================
# File      : app/routers/housekeeping_task.py
# Version   : 2025-10-23 v1
# Purpose   : Housekeeping API Router
# Auth      : X-Internal-Token + (ADMIN/SUPERADMIN)
# =============================================================================

from __future__ import annotations
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import require_roles, require_token_local
from app.db.session import get_db
from app.schemas.housekeeping_task import (
    HousekeepingTaskCreate,
    HousekeepingTaskUpdate,
    HousekeepingTaskOut,
)
from app.services.housekeeping_service import (
    create_task,
    complete_task,
    list_tasks,
    stats_units_by_staff,
    stats_total_units,
)

router = APIRouter(
    prefix="/api/housekeeping",
    tags=["housekeeping"],
    dependencies=[Depends(require_token_local), Depends(require_roles(["ADMIN", "SUPERADMIN"]))],
)

@router.get("/tasks", response_model=List[HousekeepingTaskOut])
def get_tasks(
    business_date: str = Query(..., description="YYYY-MM-DD"),
    property_code: str = Query("MOP"),
    staff_name: Optional[str] = None,
    room_no: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return list_tasks(db, business_date, property_code, staff_name, room_no)


@router.post("/task", response_model=HousekeepingTaskOut)
def post_task(
    payload: HousekeepingTaskCreate,
    db: Session = Depends(get_db),
):
    return create_task(db, payload.dict())


@router.post("/task/{task_id}/complete", response_model=HousekeepingTaskOut)
def post_complete_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    t = complete_task(db, task_id)
    if not t:
        raise HTTPException(status_code=404, detail="housekeeping_task.not_found")
    return t


@router.get("/stats/units", response_model=Dict[str, Any])
def get_stats_units(
    business_date: str = Query(..., description="YYYY-MM-DD"),
    property_code: str = Query("MOP"),
    db: Session = Depends(get_db),
):
    by_staff = stats_units_by_staff(db, business_date, property_code)
    total = stats_total_units(db, business_date, property_code)
    return {"by_staff": by_staff, "total": total}
