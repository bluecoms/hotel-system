# app/services/housekeeping_service.py
# =============================================================================
# File      : app/services/housekeeping_service.py
# Version   : 2025-10-23 v1
# Purpose   : Housekeeping domain service (CRUD + Stats)
# =============================================================================

from __future__ import annotations
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.housekeeping_task import HousekeepingTask


def create_task(db: Session, payload: Dict[str, Any]) -> HousekeepingTask:
    task = HousekeepingTask(
        business_date=payload["business_date"],
        property_code=payload["property_code"],
        room_no=payload["room_no"],
        status_before=payload.get("status_before"),
        status_after=payload.get("status_after"),
        staff_name=payload.get("staff_name"),
        memo=payload.get("memo"),
        units=float(payload.get("units", 1.0)),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def complete_task(db: Session, task_id: int) -> Optional[HousekeepingTask]:
    task = db.query(HousekeepingTask).filter(HousekeepingTask.id == task_id).first()
    if not task:
        return None
    task.completed_at = datetime.utcnow()
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return task


def list_tasks(
    db: Session,
    business_date: str,
    property_code: str,
    staff_name: Optional[str] = None,
    room_no: Optional[str] = None,
) -> List[HousekeepingTask]:
    q = db.query(HousekeepingTask).filter(
        and_(
            HousekeepingTask.business_date == business_date,
            HousekeepingTask.property_code == property_code,
        )
    )
    if staff_name:
        q = q.filter(HousekeepingTask.staff_name == staff_name)
    if room_no:
        q = q.filter(HousekeepingTask.room_no == room_no)
    return q.order_by(HousekeepingTask.room_no.asc(), HousekeepingTask.id.asc()).all()


def stats_units_by_staff(
    db: Session,
    business_date: str,
    property_code: str,
) -> List[Dict[str, Any]]:
    q = (
        db.query(
            HousekeepingTask.staff_name.label("staff_name"),
            func.sum(HousekeepingTask.units).label("units"),
            func.count(HousekeepingTask.id).label("count"),
            func.sum(func.case((HousekeepingTask.completed_at.isnot(None), 1), else_=0)).label("completed"),
        )
        .filter(
            and_(
                HousekeepingTask.business_date == business_date,
                HousekeepingTask.property_code == property_code,
            )
        )
        .group_by(HousekeepingTask.staff_name)
        .order_by(func.sum(HousekeepingTask.units).desc(), HousekeepingTask.staff_name.asc())
    )
    rows = q.all()
    return [
        {
            "staff_name": r.staff_name or "",
            "units": float(r.units or 0.0),
            "count": int(r.count or 0),
            "completed": int(r.completed or 0),
        }
        for r in rows
    ]


def stats_total_units(db: Session, business_date: str, property_code: str) -> Dict[str, Any]:
    q = db.query(
        func.sum(HousekeepingTask.units).label("units"),
        func.count(HousekeepingTask.id).label("count"),
        func.sum(func.case((HousekeepingTask.completed_at.isnot(None), 1), else_=0)).label("completed"),
    ).filter(
        and_(
            HousekeepingTask.business_date == business_date,
            HousekeepingTask.property_code == property_code,
        )
    )
    r = q.first()
    return {
        "units": float((r.units or 0.0)),
        "count": int(r.count or 0),
        "completed": int(r.completed or 0),
    }
