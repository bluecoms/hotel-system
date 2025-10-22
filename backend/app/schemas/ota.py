# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/schemas/ota.py
# Version   : 2025.10-27 · v2.1 (Add master_id · SSOT Verified)
# Purpose   : Hotel Admin — OTA Schemas (채널·수수료·주문·요약)
# ----------------------------------------------------------------------------
# 목적:
#   • OTA(Online Travel Agency) 도메인의 Pydantic 스키마 정의
#   • 입력용(Create/Update)과 출력용(Out) 분리, v2 from_attributes 적용
# ----------------------------------------------------------------------------
# 연계:
#   • app/models/ota.py               → OTAChannel / OTACommission / OTAOrder
#   • app/routers/ota.py              → /api/ota/*
#   • app/models/master_ota_channel.py→ MasterOtaChannel (FK: master_id)
# ----------------------------------------------------------------------------
# 변경 로그:
#   v2.1 (2025-10-27)
#     ✅ OTAChannelOut에 master_id 추가 (Master 연동 표시)
#     ✅ rate 필드 검증(0~100) 확정
#     ✅ 주문/요약 응답 스키마 보강(실사용 최소셋)
# ============================================================================

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# 1️⃣ 채널 (Channel)
# ============================================================================

class OTAChannelCreate(BaseModel):
    """OTA 채널 생성 입력"""
    code: str = Field(..., description="채널 코드 (대문자 권장)")
    name: str = Field(..., description="채널명 (예: Booking.com)")
    status: Optional[str] = Field("", description="상태값 (선택)")

    @field_validator("code")
    @classmethod
    def _norm_code(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("code is required")
        return v.upper()


class OTAChannelOut(BaseModel):
    """OTA 채널 출력"""
    id: int
    code: str
    name: str
    status: str
    master_id: Optional[int] = Field(None, description="MasterOtaChannel FK")
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# 2️⃣ 수수료 (Commission)
# ============================================================================

class OTACommissionCreate(BaseModel):
    """수수료 생성 입력 (rate: %, 0~100)"""
    channel: str = Field(..., description="채널 코드")
    valid_from: date
    valid_to: date
    rate: float = Field(..., ge=0, le=100, description="수수료율 % (0~100)")
    note: Optional[str] = None

    @field_validator("channel")
    @classmethod
    def _norm_channel(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("channel is required")
        return v.upper()

    @field_validator("valid_to")
    @classmethod
    def _date_order(cls, to: date, info):
        frm: date = info.data.get("valid_from")
        if frm and to < frm:
            raise ValueError("valid_to must be >= valid_from")
        return to


class OTACommissionUpdate(BaseModel):
    """수수료 수정 입력 (모두 선택)"""
    channel: Optional[str] = Field(None, description="채널 코드")
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    rate: Optional[float] = Field(None, ge=0, le=100, description="수수료율 % (0~100)")
    note: Optional[str] = None

    @field_validator("channel")
    @classmethod
    def _norm_channel_opt(cls, v: Optional[str]) -> Optional[str]:
        return v.upper().strip() if isinstance(v, str) and v.strip() else v

    @field_validator("valid_to")
    @classmethod
    def _date_order_opt(cls, to: Optional[date], info):
        frm: Optional[date] = info.data.get("valid_from")
        if to and frm and to < frm:
            raise ValueError("valid_to must be >= valid_from")
        return to


class OTACommissionOut(BaseModel):
    """수수료 출력 (rate: %, 0~100)"""
    id: int
    channel: str
    valid_from: date
    valid_to: date
    rate: float
    note: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# 3️⃣ 주문(예약) (Order)
# ============================================================================

class OTAOrderOut(BaseModel):
    """주문(예약) 목록 출력용 최소 셋"""
    id: int
    channel: str
    order_code: str
    guest_name: str
    check_in: Optional[str] = None     # "YYYY-MM-DD"
    check_out: Optional[str] = None
    status: Optional[str] = None       # CONFIRMED / CANCELLED / PENDING
    amount: int
    currency: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# 4️⃣ 요약 (Summary)
# ============================================================================

class OTASummaryItem(BaseModel):
    channel: str
    gross: int
    fee_pct: float
    fee_amount: float
    net: float
    count: int


class OTASummaryOut(BaseModel):
    ok: bool
    business_date: str
    items: List[OTASummaryItem]
    total: dict
