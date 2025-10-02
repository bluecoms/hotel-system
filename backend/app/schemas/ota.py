# app/schemas/ota.py
# -*- coding: utf-8 -*-
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, field_validator

# ─────────────────────────────────────────────────────────────────────────────
# Channels

class OTAChannelCreate(BaseModel):
    code: str
    name: str

class OTAChannelOut(BaseModel):
    id: int
    code: str
    name: str
    created_at: datetime

    class Config:
        from_attributes = True

# ─────────────────────────────────────────────────────────────────────────────
# Commissions
# 입력은 rate(%) 0~100, 저장은 0~1, 응답은 다시 0~100 로 사용

class OTACommissionCreate(BaseModel):
    channel: str                 # 채널 코드(예: BKG)
    valid_from: date
    valid_to: date
    rate: float                  # 0~100 (%)
    note: Optional[str] = None

    @field_validator("rate")
    @classmethod
    def _rate_range(cls, v: float):
        if v < 0 or v > 100:
            raise ValueError("rate must be between 0 and 100")
        return v

class OTACommissionUpdate(BaseModel):
    channel: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    rate: Optional[float] = None  # 0~100 (%)
    note: Optional[str] = None

    @field_validator("rate")
    @classmethod
    def _rate_range_opt(cls, v: Optional[float]):
        if v is None:
            return v
        if v < 0 or v > 100:
            raise ValueError("rate must be between 0 and 100")
        return v

class OTACommissionOut(BaseModel):
    id: int
    channel: str                 # 채널 코드
    valid_from: date
    valid_to: date
    rate: float                  # 0~100 (%)
    note: Optional[str] = None

    class Config:
        from_attributes = True
