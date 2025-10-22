# app/schemas/closing.py
# -*- coding: utf-8 -*-
from typing import List, Dict, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict


# Calendar/day rows
class ClosingDayRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    date: str
    uploaded: List[str] = Field(default_factory=list)
    counts: Dict[str, int] = Field(default_factory=dict)
    done: int = 0
    total: int = 0
    complete: bool = False
    status: Literal["OPEN", "CLOSED"] = "OPEN"


class ClosingCalendarResp(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    property_code: str
    timezone: str = "UTC"
    month: Optional[str] = None
    from_: str = Field(alias="from")
    to: str
    required: List[str] = Field(default_factory=list)
    days: List[ClosingDayRow] = Field(default_factory=list)


# Day get/set
class DayStatusBody(BaseModel):
    date: str
    property_code: str = "MOP"
    status: Literal["OPEN", "CLOSED"]


# Restore
class RestoreBody(BaseModel):
    dataset: str
    business_date: str
    property_code: str = "MOP"
    version_no: int
