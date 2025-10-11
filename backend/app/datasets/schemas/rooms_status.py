# app/datasets/schemas/rooms_status.py
# -*- coding: utf-8 -*-
# version: 2025-10-11 Phase 2 (schemas)

from pydantic import BaseModel, Field


class RoomsStatusRow(BaseModel):
    """
    Rooms Status (객실 상태) 데이터 단위 행 스키마
    - 어댑터(rooms_status.py)에서 normalize/parse 후 표준화된 구조
    - status: CLEAN / DIRTY / OOO 등
    """
    business_date: str = Field(..., description="업무 일자 (YYYY-MM-DD)")
    property_code: str = Field(..., description="호텔 코드 (예: MOP)")
    room_no: str = Field(..., description="객실 번호")
    status: str = Field(..., description="상태 (예: CLEAN, DIRTY, OOO)")
    note: str = Field("", description="비고 (선택)")

    class Config:
        from_attributes = True
        orm_mode = True
