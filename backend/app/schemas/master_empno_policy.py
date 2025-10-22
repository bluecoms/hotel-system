# -*- coding: utf-8 -*-
# version: 2025-10-18 v1.1 (Master EmpNoPolicy Schema)
"""
Hotel Admin — Master EmpNoPolicy Schema (/api/master/empno-policy)
────────────────────────────────────────────
목적:
  • 호텔 인사 시스템의 사번(직원번호) 정책 관리용 스키마
  • prefix / start_no / auto_increment / memo / updated_at 필드 관리
────────────────────────────────────────────
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


# ─────────────────────────────────────────────
# 공통 필드
# ─────────────────────────────────────────────
class MasterEmpNoPolicyBase(BaseModel):
    """사번 정책 공통 필드"""
    prefix: str = Field("EMP", description="사번 접두어 (예: EMP, HK, FNB)")
    start_no: int = Field(1, description="시작 번호")
    auto_increment: bool = Field(True, description="자동 증가 여부")
    memo: Optional[str] = Field(None, description="비고 / 설명")


# ─────────────────────────────────────────────
# 입력용 (Create / Update)
# ─────────────────────────────────────────────
class MasterEmpNoPolicyIn(MasterEmpNoPolicyBase):
    """입력용 (생성/수정)"""
    pass


# ─────────────────────────────────────────────
# 출력용 (Read)
# ─────────────────────────────────────────────
class MasterEmpNoPolicyOut(MasterEmpNoPolicyBase):
    """출력용 (조회 응답)"""
    id: int = Field(..., description="PK")
    updated_at: Optional[datetime] = Field(None, description="최종 수정일시")

    model_config = ConfigDict(from_attributes=True)
