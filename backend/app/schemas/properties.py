# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/schemas/property.py
# Version   : 2025.10-26 · v2.0 (SSOT Final · 운영용 조회 전용)
# Purpose   : Hotel Admin — Property(지점) 운영용 조회 스키마 (/api/properties)
# ----------------------------------------------------------------------------
# 목적:
#   • 운영 시스템 전역에서 사용하는 Property(지점) 조회 스키마
#   • /api/properties 엔드포인트에서만 사용 (조회 전용)
#   • SSOT 구조에 따라 생성/수정은 /api/master/properties 에서만 수행
# ----------------------------------------------------------------------------
# 설계 원칙:
#   • from_attributes=True → ORM 객체 자동 매핑
#   • extra="ignore" → 안전한 확장 허용
# ----------------------------------------------------------------------------
# 구성:
#   • PropertyOut : 조회/응답용 (운영 전용)
# ----------------------------------------------------------------------------
# 연계:
#   • app/models/property.py     → Property ORM
#   • app/routers/properties.py  → /api/properties (GET 전용)
# ============================================================================
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# ─────────────────────────────────────────────
# 조회/응답 스키마 (운영 전용)
# ─────────────────────────────────────────────
class PropertyOut(BaseModel):
    """운영용 Property 조회 스키마"""
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    code: str = Field(..., description="지점 코드 (예: MOP)")
    name: str = Field(..., description="지점명 (예: Mokpo Ocean Hotel)")
    is_active: bool = Field(..., description="활성 여부")
    created_at: Optional[datetime] = Field(None, description="생성일시(UTC)")
    updated_at: Optional[datetime] = Field(None, description="수정일시(UTC)")
