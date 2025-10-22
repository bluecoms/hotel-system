# backend/app/schemas/employee_file.py
# -*- coding: utf-8 -*-
# version: 2025-10-12  v2.5
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class EmployeeFileIn(BaseModel):
    employee_id: int = Field(..., description="직원 ID")
    file_name: str = Field(..., description="파일 이름")
    file_type: str = Field("document", description="파일 유형(document/image/pdf)")
    file_path: Optional[str] = Field("", description="저장 경로")
    description: Optional[str] = Field("", description="파일 설명")


class EmployeeFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: int
    file_name: str
    file_type: str
    file_path: str
    version_no: int
    is_latest: bool
    description: str
    created_at: datetime
    updated_at: datetime


class EmployeeFileListOut(BaseModel):
    items: List[EmployeeFileOut]
    total: int


class EmployeeFileHistoryOut(BaseModel):
    employee_id: int
    items: List[EmployeeFileOut]
