# app/schemas/board.py
# -*- coding: utf-8 -*-
from typing import Optional, Literal, List, Dict
from pydantic import BaseModel, Field, ConfigDict


class ClosingDayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    date: str
    status: Literal["OPEN", "CLOSED"]
    done: int = 0
    total: int = 0
    complete: bool = False


class ClosingCalendarDay(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    date: str
    uploaded: List[str] = Field(default_factory=list)
    counts: Dict[str, int] = Field(default_factory=dict)
    done: int = 0
    total: int = 0
    complete: bool = False
    status: Literal["OPEN", "CLOSED"] = "OPEN"


class ClosingCalendarOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    property_code: str
    month: Optional[str] = None
    timezone: str = "UTC"
    from_: str = Field(alias="from")
    to: str
    required: List[str] = Field(default_factory=list)
    days: List[ClosingCalendarDay] = Field(default_factory=list)


class DayStatusBody(BaseModel):
    date: str
    property_code: str = "MOP"
    status: Literal["OPEN", "CLOSED"]


class RestoreBody(BaseModel):
    dataset: str
    business_date: str
    property_code: str = "MOP"
    version_no: int
