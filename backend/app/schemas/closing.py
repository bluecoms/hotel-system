# app/schemas/closing.py
from typing import List
from pydantic import BaseModel

class ClosingItem(BaseModel):
    date: str
    status: str
    # ... 기타 필드

class ClosingCalendarResp(BaseModel):
    ok: bool = True
    property_code: str
    date_from: str
    date_to: str
    items: List[ClosingItem] = []  # 항상 존재, 기본값 []
