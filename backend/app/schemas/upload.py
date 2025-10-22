# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/schemas/upload.py
# Version   : 2025-10-31 · v3.6 (SSOT Stable · SoftDelete + allow_extra)
# Purpose   : Upload Schemas — upload_sessions / uploaded_files 대응
# ----------------------------------------------------------------------------
# 변경 요약:
#   ✅ is_active 필드 추가 (soft-delete 상태)
#   ✅ remarks 기본값 보장
#   ✅ extra='allow' 설정 (Pydantic v2)
#   ✅ from_attributes=True 유지 (ORM 변환)
# ============================================================================

from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class UploadedFileOut(BaseModel):
    """단일 업로드 파일 이력"""
    model_config = ConfigDict(from_attributes=True, extra="allow")

    version_no: int
    filename: str
    size: int
    uploaded_at: datetime
    part_key: Optional[str] = ""
    remarks: Optional[str] = ""
    is_active: bool = True   # ✅ 추가: soft-delete 상태 표시


class UploadVersionList(BaseModel):
    """업로드 이력 목록 응답"""
    model_config = ConfigDict(from_attributes=True, extra="allow")

    items: List[UploadedFileOut] = []
