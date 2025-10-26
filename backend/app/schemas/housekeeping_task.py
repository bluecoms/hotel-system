# -*- coding: utf-8 -*-
# =============================================================================
# File      : app/schemas/housekeeping_task.py
# Version   : 2025-10-31 · v2 (DeptAccess Unified · Employee FK 적용)
# Purpose   : Housekeeping Task Pydantic Schemas
# -----------------------------------------------------------------------------
# 목적:
#   • 하우스키핑 일자별 객실 작업(청소/점검/상태변경) 스키마 정의
#   • ORM(app/models/housekeeping_task.py)과 완전 매핑
#   • DeptAccess 구조에 맞춰 employee_id + department_code 사용
# -----------------------------------------------------------------------------
# 변경사항 (v2):
#   ✅ staff_name 제거 → employee_id + department_code 로 통합
#   ✅ ORM 필드와 동일한 구조 유지
#   ✅ from_attributes=True (Pydantic v2 호환)
# -----------------------------------------------------------------------------
# 주의:
#   • Python 3.8 호환 (typing.Optional / ConfigDict 미사용)
#   • FastAPI response_model, CRUD DTO 모두 동일 구조 사용
# =============================================================================

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# 1️⃣ Base Schema
# ──────────────────────────────────────────────
class HousekeepingTaskBase(BaseModel):
    business_date: str = Field(..., description="업무 일자 (YYYY-MM-DD)")
    property_code: str = Field(..., description="호텔 코드 (예: MOP)")
    room_no: str = Field(..., description="객실 번호")
    status_before: Optional[str] = Field(None, description="변경 전 상태")
    status_after: Optional[str] = Field(None, description="변경 후 상태")
    employee_id: Optional[int] = Field(None, description="담당 직원 ID (employees.id)")
    department_code: Optional[str] = Field(None, description="부서 코드 (예: HK)")
    memo: Optional[str] = Field(None, description="메모")
    units: float = Field(1.0, description="작업 유닛(가중치)")


# ──────────────────────────────────────────────
# 2️⃣ Create Schema
# ──────────────────────────────────────────────
class HousekeepingTaskCreate(HousekeepingTaskBase):
    """신규 하우스키핑 작업 생성 요청용"""
    pass


# ──────────────────────────────────────────────
# 3️⃣ Update Schema
# ──────────────────────────────────────────────
class HousekeepingTaskUpdate(BaseModel):
    """하우스키핑 작업 수정 요청용"""
    status_after: Optional[str] = Field(None, description="변경 후 상태")
    employee_id: Optional[int] = Field(None, description="담당 직원 ID (employees.id)")
    department_code: Optional[str] = Field(None, description="부서 코드 (예: HK)")
    memo: Optional[str] = Field(None, description="메모")
    units: Optional[float] = Field(None, description="작업 유닛(가중치)")


# ──────────────────────────────────────────────
# 4️⃣ Out Schema (Response)
# ──────────────────────────────────────────────
class HousekeepingTaskOut(HousekeepingTaskBase):
    """하우스키핑 작업 응답 스키마"""
    id: int = Field(..., description="작업 ID (PK)")
    completed_at: Optional[str] = Field(None, description="완료 시각 (ISO 형식)")
    created_at: Optional[str] = Field(None, description="생성 시각 (ISO 형식)")
    updated_at: Optional[str] = Field(None, description="수정 시각 (ISO 형식)")

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
# 5️⃣ (선택) 통계용 스키마
# ──────────────────────────────────────────────
class HousekeepingStatsOut(BaseModel):
    """하우스키핑 통계 응답 (직원별 유닛 합계 등)"""
    staff_name: Optional[str] = Field(None, description="직원 이름")
    employee_id: Optional[int] = Field(None, description="직원 ID")
    department_code: Optional[str] = Field(None, description="부서 코드 (예: HK)")
    units: float = Field(..., description="유닛 합계")
    count: int = Field(..., description="작업 건수")
    completed: int = Field(..., description="완료 건수")

    class Config:
        from_attributes = True
