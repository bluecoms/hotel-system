# -*- coding: utf-8 -*-
# version: 2025-10-18 v1.0 (Master Ranks Schema)
"""
Hotel Admin — Master Ranks Schema (/api/master/ranks)
────────────────────────────────────────────
목적:
  • 직급(Ranks) 기준정보용 Pydantic 스키마 정의
  • /api/master/ranks 라우터와 연동
  • order_no / base_salary / is_active / created_at 필드 포함
────────────────────────────────────────────
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ─────────────────────────────────────────────
# 기본형 (공통)
# ─────────────────────────────────────────────
class MasterRankBase(BaseModel):
    """직급 기준정보 공통 필드"""
    code: str = Field(..., description="직급 코드 (unique)")
    name: str = Field(..., description="직급명 (예: 대리, 과장, 부장)")
    base_salary: Optional[int] = Field(0, description="직급별 기본급 (단위: 원)")
    order_no: Optional[int] = Field(None, description="정렬 순서")
    is_active: bool = Field(True, description="활성 여부")


# ─────────────────────────────────────────────
# 입력용 (Create / Update)
# ─────────────────────────────────────────────
class MasterRankIn(MasterRankBase):
    """직급 생성/수정 입력 스키마"""
    pass


# ─────────────────────────────────────────────
# 출력용 (조회)
# ─────────────────────────────────────────────
class MasterRankOut(MasterRankBase):
    """직급 조회/응답 스키마"""
    id: int = Field(..., description="PK")
    created_at: datetime = Field(..., description="생성일시")

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# 재정렬(Reorder) 요청용
# ─────────────────────────────────────────────
class MasterRankReorderIn(BaseModel):
    """직급 순서 재정렬 항목"""
    id: int = Field(..., description="직급 ID")
    order_no: int = Field(..., description="정렬 순서")


class MasterRankReorderBody(BaseModel):
    """직급 일괄 재정렬 요청"""
    items: List[MasterRankReorderIn]
