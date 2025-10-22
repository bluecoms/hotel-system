# app/schemas/upload.py
# -*- coding: utf-8 -*-
# version: 2025-10-18 Phase 3 Stable

"""
Upload Schemas (Phase 3 SSOT)
──────────────────────────────────────────────
- upload_sessions, uploaded_files 테이블 대응
- 업로드 이력 조회(/api/upload/versions) 응답 구조
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional

class UploadedFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    version_no: int
    filename: str
    size: int
    uploaded_at: datetime
    part_key: Optional[str] = ""
    remarks: Optional[str] = None

class UploadVersionList(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    items: list[UploadedFileOut] = []
