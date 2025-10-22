# backend/app/schemas/reports.py
# Python 3.8+ / Pydantic v2
from pydantic import BaseModel, Field, ConfigDict
from typing import List

class PosItemRow(BaseModel):
    dept: str
    item: str
    qty: int = Field(0, ge=0)
    amount: int = Field(0, ge=0)
    currency: str = "KRW"

class SalesTagsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    property_code: str
    business_date: str  # YYYY-MM-DD
    room_only_amount: int = 0
    package_amount: int = 0
    other_amount: int = 0
    pos_items: List[PosItemRow] = Field(default_factory=list)

class DashboardKPIOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    property_code: str
    business_date: str
    # 기존 KPI 필드(예: rev, occ, adr) + 확장 3값
    rev: int = 0
    occ: float = 0.0
    adr: int = 0
    room_only_amount: int = 0
    package_amount: int = 0
    other_amount: int = 0
    currency: str = "KRW"

