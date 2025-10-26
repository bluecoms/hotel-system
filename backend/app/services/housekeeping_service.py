# -*- coding: utf-8 -*-
# =============================================================================
# File      : app/services/housekeeping_service.py
# Version   : 2025-11-08 · v2.2 (SQLA 1.4 Fix · staff_name 제거 · Employee FK 기반)
# Purpose   : Hotel Admin — Housekeeping Domain Service (CRUD + Stats)
# -----------------------------------------------------------------------------
# 목적:
#   • 하우스키핑 업무 도메인 서비스 (CRUD + 통계)
#   • ORM(app/models/housekeeping_task.py)의 employee_id + department_code 구조 반영
#   • staff_name 컬럼 제거 → Employee 조인 기반 통계 처리
# -----------------------------------------------------------------------------
# 주요 함수:
#   1️⃣ create_task         : 신규 작업 등록
#   2️⃣ complete_task       : 작업 완료 처리
#   3️⃣ list_tasks          : 일자별 작업 목록 조회
#   4️⃣ stats_units_by_staff: 직원별 유닛 집계 (Employee.name 기준)
#   5️⃣ stats_total_units   : 전체 유닛 합계
# -----------------------------------------------------------------------------
# 주의:
#   • SQLAlchemy 1.4~2.x 호환
#   • case() → sqlalchemy.case 사용 (func.case 불가)
#   • staff_name 필드 제거, employee_id 사용
# =============================================================================

from __future__ import annotations
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, case

from app.models.housekeeping_task import HousekeepingTask
from app.models.employee import Employee  # ✅ 직원 이름 조인용


# -----------------------------------------------------------------------------
# 1️⃣ 신규 작업 생성
# -----------------------------------------------------------------------------
def create_task(db: Session, payload: Dict[str, Any]) -> HousekeepingTask:
    """
    하우스키핑 신규 작업 생성

    Args:
        db (Session): SQLAlchemy 세션
        payload (Dict[str, Any]): 입력 데이터
    Returns:
        HousekeepingTask: 생성된 ORM 객체
    """
    task = HousekeepingTask(
        business_date=payload["business_date"],
        property_code=payload["property_code"],
        room_no=payload["room_no"],
        status_before=payload.get("status_before"),
        status_after=payload.get("status_after"),
        employee_id=payload.get("employee_id"),          # ✅ 직원 FK
        department_code=payload.get("department_code"),  # ✅ 부서 코드
        memo=payload.get("memo"),
        units=float(payload.get("units", 1.0)),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


# -----------------------------------------------------------------------------
# 2️⃣ 작업 완료 처리
# -----------------------------------------------------------------------------
def complete_task(db: Session, task_id: int) -> Optional[HousekeepingTask]:
    """작업 완료 처리 (completed_at, updated_at 갱신)"""
    task = db.query(HousekeepingTask).filter(HousekeepingTask.id == task_id).first()
    if not task:
        return None
    task.completed_at = datetime.utcnow()
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return task


# -----------------------------------------------------------------------------
# 3️⃣ 작업 목록 조회
# -----------------------------------------------------------------------------
def list_tasks(
    db: Session,
    business_date: str,
    property_code: str,
    employee_id: Optional[int] = None,
    room_no: Optional[str] = None,
) -> List[HousekeepingTask]:
    """
    일자별 하우스키핑 작업 목록 조회
      • employee_id, room_no 로 필터 가능
    """
    q = db.query(HousekeepingTask).filter(
        and_(
            HousekeepingTask.business_date == business_date,
            HousekeepingTask.property_code == property_code,
        )
    )
    if employee_id:
        q = q.filter(HousekeepingTask.employee_id == employee_id)
    if room_no:
        q = q.filter(HousekeepingTask.room_no == room_no)

    return q.order_by(HousekeepingTask.room_no.asc(), HousekeepingTask.id.asc()).all()


# -----------------------------------------------------------------------------
# 4️⃣ 직원별 유닛 통계
# -----------------------------------------------------------------------------
def stats_units_by_staff(
    db: Session,
    business_date: str,
    property_code: str,
) -> List[Dict[str, Any]]:
    """
    직원별 유닛 통계 (Employee.name 기준)

    Returns:
        [
          {"staff_name": "이하우스", "units": 12.0, "count": 8, "completed": 6},
          {"staff_name": "김프론트", "units": 9.5,  "count": 7, "completed": 7},
        ]
    """
    q = (
        db.query(
            Employee.name.label("staff_name"),
            func.sum(HousekeepingTask.units).label("units"),
            func.count(HousekeepingTask.id).label("count"),
            func.sum(
                case((HousekeepingTask.completed_at.isnot(None), 1), else_=0)
            ).label("completed"),
        )
        .join(Employee, Employee.id == HousekeepingTask.employee_id)
        .filter(
            and_(
                HousekeepingTask.business_date == business_date,
                HousekeepingTask.property_code == property_code,
            )
        )
        .group_by(Employee.name)
        .order_by(func.sum(HousekeepingTask.units).desc(), Employee.name.asc())
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


# -----------------------------------------------------------------------------
# 5️⃣ 전체 유닛 통계
# -----------------------------------------------------------------------------
def stats_total_units(db: Session, business_date: str, property_code: str) -> Dict[str, Any]:
    """
    전체 유닛 합계 / 작업 수 / 완료 건수 반환
    """
    q = db.query(
        func.sum(HousekeepingTask.units).label("units"),
        func.count(HousekeepingTask.id).label("count"),
        func.sum(
            case((HousekeepingTask.completed_at.isnot(None), 1), else_=0)
        ).label("completed"),
    ).filter(
        and_(
            HousekeepingTask.business_date == business_date,
            HousekeepingTask.property_code == property_code,
        )
    )
    r = q.first()
    return {
        "units": float(r.units or 0.0),
        "count": int(r.count or 0),
        "completed": int(r.completed or 0),
    }
