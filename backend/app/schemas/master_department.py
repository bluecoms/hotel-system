# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/schemas/master_departments.py
# Version   : 2025.10-31 · v1.2 (SSOT Final · Options/Reorder Stable)
# Purpose   : Hotel Admin — Master Departments Schema (/api/master/departments)
# ----------------------------------------------------------------------------
# 목적:
#   • 부서(Departments) 기준정보용 Pydantic 스키마 정의
#   • property_code / dept_code / dept_name / parent_code / order_no / is_active 등 관리
#   • /options (v-select용 title/value 구조) 및 재정렬 스키마 포함
# ----------------------------------------------------------------------------
# 구성:
#   • MasterDepartmentBase       : 공통 필드
#   • MasterDepartmentIn         : 생성/수정 입력용
#   • MasterDepartmentOut        : 조회/응답용 (ORM 변환 지원)
#   • MasterDepartmentOption     : v-select 옵션(title/value)
#   • MasterDepartmentReorderIn  : 재정렬 단일 항목
#   • MasterDepartmentReorderBody: 일괄 재정렬 요청
# ----------------------------------------------------------------------------
# Naming 규칙 (SSOT 고정)
#   • Model  : app/models/master_department.py     → 단수
#   • Schema : app/schemas/master_departments.py   → 복수
#   • Router : app/routers/master_departments.py   → 복수
# ============================================================================

from datetime import datetime
from typing import Optional, List, ClassVar
from pydantic import BaseModel, Field, ConfigDict


# ─────────────────────────────────────────────
# 1️⃣ 공통 필드
# ─────────────────────────────────────────────
class MasterDepartmentBase(BaseModel):
    """부서 공통 필드"""
    property_code: str = Field("MOP", description="사업장 코드 (기본값 MOP)")
    dept_code: str = Field(..., description="부서 코드 (예: FR, HK, FB)")
    dept_name: str = Field(..., description="부서명 (한글)")
    parent_code: Optional[str] = Field(None, description="상위 부서 코드")
    order_no: Optional[int] = Field(0, description="정렬 순서 (낮을수록 우선)")
    is_active: bool = Field(True, description="활성 여부")
    remarks: Optional[str] = Field(None, description="비고 (선택)")


# ─────────────────────────────────────────────
# 2️⃣ 입력용 (Create / Update)
# ─────────────────────────────────────────────
class MasterDepartmentIn(MasterDepartmentBase):
    """부서 생성/수정 입력 스키마"""
    pass


# ─────────────────────────────────────────────
# 3️⃣ 출력용 (조회)
# ─────────────────────────────────────────────
class MasterDepartmentOut(MasterDepartmentBase):
    """부서 조회/응답 스키마"""
    id: int = Field(..., description="PK")
    created_at: Optional[datetime] = Field(None, description="생성일시 (UTC)")
    updated_at: Optional[datetime] = Field(None, description="수정일시 (UTC)")

    # ✅ ORM 변환 지원
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────
# 4️⃣ 옵션 목록용 (v-select 등)
# ─────────────────────────────────────────────
class MasterDepartmentOption(BaseModel):
    """부서 선택 옵션 (v-select용 title/value 구조)"""
    title: str = Field(..., description="부서명 (한글)")
    value: str = Field(..., description="부서 코드")

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────
# 5️⃣ 재정렬용 (drag reorder)
# ─────────────────────────────────────────────
class MasterDepartmentReorderIn(BaseModel):
    """부서 순서 재정렬 단일 항목"""
    id: int = Field(..., description="부서 ID")
    order_no: int = Field(..., description="정렬 순서")


class MasterDepartmentReorderBody(BaseModel):
    """부서 순서 재정렬 요청 바디"""
    items: List[MasterDepartmentReorderIn] = Field(..., description="부서 재정렬 항목 목록")
