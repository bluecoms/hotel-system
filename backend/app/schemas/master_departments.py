# -*- coding: utf-8 -*-
# version: 2025-10-18 v1.0 (Master Departments Schema)
"""
Hotel Admin — Master Departments Schema (/api/master/departments)
────────────────────────────────────────────
목적:
  • 부서(Departments) 기준정보용 Pydantic 스키마 정의
  • property_code / dept_code / dept_name / parent_code / order_no / is_active 등 관리
────────────────────────────────────────────
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# ─────────────────────────────────────────────
# 공통 필드
# ─────────────────────────────────────────────
class MasterDepartmentBase(BaseModel):
    """부서 공통 필드"""
    property_code: str = Field("MOP", description="사업장 코드")
    dept_code: str = Field(..., description="부서 코드")
    dept_name: str = Field(..., description="부서명")
    parent_code: Optional[str] = Field(None, description="상위 부서 코드")
    order_no: Optional[int] = Field(0, description="정렬 순서")
    is_active: bool = Field(True, description="활성 여부")
    remarks: Optional[str] = Field(None, description="비고")


# ─────────────────────────────────────────────
# 입력용 (Create / Update)
# ─────────────────────────────────────────────
class MasterDepartmentIn(MasterDepartmentBase):
    """입력용 (생성/수정)"""
    pass


# ─────────────────────────────────────────────
# 출력용 (조회)
# ─────────────────────────────────────────────
class MasterDepartmentOut(MasterDepartmentBase):
    """출력용"""
    id: int = Field(..., description="PK")
    created_at: Optional[datetime] = Field(None, description="생성일시")
    updated_at: Optional[datetime] = Field(None, description="수정일시")

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────
# 옵션 목록용 (selectbox 등)
# ─────────────────────────────────────────────
class MasterDepartmentOption(BaseModel):
    """부서 선택 옵션"""
    title: str
    value: str


# ─────────────────────────────────────────────
# 재정렬용 (drag reorder)
# ─────────────────────────────────────────────
class MasterDepartmentReorderIn(BaseModel):
    id: int
    order_no: int


class MasterDepartmentReorderBody(BaseModel):
    items: List[MasterDepartmentReorderIn]
