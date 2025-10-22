# app/schemas/hr.py
# -*- coding: utf-8 -*-
# version: 2025-10-15  v1.0 (Bridge Stub)
"""
인사관리(HR) 스키마 — Bridge 용 기본형
────────────────────────────────────────────
- /api/hr/* 라우터 대응용
- 실제 데이터는 employees.py / users.py 스키마 재활용
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class HRBase(BaseModel):
    employee_id: int
    action: str
    note: Optional[str] = ""
    created_at: Optional[datetime] = None


class HRPolicyIn(BaseModel):
    name: str
    value: str


class HRPolicyOut(HRPolicyIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    updated_at: Optional[datetime] = None
