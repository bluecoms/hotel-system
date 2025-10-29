# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/schemas/master_room_type.py
# Version   : 2025-11-09 · v1.1 (SSOT Stable · Pydantic v2)
# Purpose   : Hotel Admin — MasterRoomType Pydantic 스키마
# ----------------------------------------------------------------------------
# 목적:
#   • 객실 타입(RoomType) 기준정보의 입력/출력/검증 정의
#   • 하우스키핑 유닛 계산 및 객실관리의 기본 단위로 사용
# ----------------------------------------------------------------------------
# 구성:
#   • RoomTypeBase   → 공통 필드 정의
#   • RoomTypeCreate → 신규 등록용
#   • RoomTypeUpdate → 수정용 (부분 업데이트)
#   • RoomTypeOut    → 출력용 (ORM 직렬화)
# ----------------------------------------------------------------------------
# 필드 설명:
#   - code        : 객실 타입 코드 (예: STD, DLX, SUITE)
#   - name        : 표시명 (예: 스탠다드, 디럭스)
#   - unit_value  : 하우스키핑 계산 단위 (기본 1.0)
#   - description : 설명(옵션)
#   - is_active   : 활성 여부
#   - created_at / updated_at : ORM → 응답 직렬화
# ----------------------------------------------------------------------------
# 연계:
#   • models.master_room_type.MasterRoomType
#   • routers.master_room_type (CRUD)
#   • 프런트 MasterData.vue > 운영 기준정보 탭
# ============================================================================

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# ─────────────────────────────────────────────
# 공통 필드 (Base)
# ─────────────────────────────────────────────
class RoomTypeBase(BaseModel):
    """공통 필드 — 입력/출력 공용"""

    model_config = ConfigDict(extra="ignore")

    code: str = Field(..., description="객실 타입 코드 (예: STD, DLX, SUITE)")
    name: str = Field(..., description="객실 타입명 (예: 스탠다드, 디럭스)")
    unit_value: float = Field(1.0, description="유닛 계산값 (예: 1.0)")
    description: Optional[str] = Field(None, description="설명 (옵션)")
    is_active: bool = Field(True, description="활성 여부")


# ─────────────────────────────────────────────
# 신규 등록용 (POST)
# ─────────────────────────────────────────────
class RoomTypeCreate(RoomTypeBase):
    """신규 등록 입력용"""
    pass


# ─────────────────────────────────────────────
# 수정용 (PATCH/PUT)
# ─────────────────────────────────────────────
class RoomTypeUpdate(BaseModel):
    """부분 수정 입력용"""

    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = Field(None, description="객실 타입명")
    unit_value: Optional[float] = Field(None, description="유닛 계산값")
    description: Optional[str] = Field(None, description="설명")
    is_active: Optional[bool] = Field(None, description="활성 여부")


# ─────────────────────────────────────────────
# 출력용 (GET 응답)
# ─────────────────────────────────────────────
class RoomTypeOut(RoomTypeBase):
    """조회/출력용"""

    id: int = Field(..., description="고유 ID")
    created_at: datetime = Field(..., description="생성일시 (UTC)")
    updated_at: datetime = Field(..., description="수정일시 (UTC)")

    model_config = ConfigDict(from_attributes=True, extra="ignore")


# ============================================================================
# ✅ EOF — app/schemas/master_room_type.py (v1.1 · SSOT Stable)
# ============================================================================
