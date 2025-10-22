# ============================================================================
# File      : app/schemas/property.py
# Version   : 2025.10-22 v1.0 (Stable / Property Schema)
# Purpose   : Hotel Admin — Property(지점) Pydantic 스키마
# ----------------------------------------------------------------------------
# 목적:
#   • Property(지점) 데이터의 입출력 검증 및 직렬화 정의
#   • 프런트엔드 Property Selector 및 관리자 페이지에서 사용
# ----------------------------------------------------------------------------
# 설계 원칙:
#   • from_attributes=True → ORM 객체 자동 매핑 지원
#   • extra="ignore" → 안전한 확장
# ----------------------------------------------------------------------------
# 구성:
#   • PropertyIn     → 신규 등록 입력용
#   • PropertyOut    → 목록/조회 출력용
# ============================================================================
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# ─────────────────────────────────────────────
# 입력용 (POST body)
# ─────────────────────────────────────────────
class PropertyIn(BaseModel):
    """신규 Property 등록 입력"""
    model_config = ConfigDict(extra="ignore")

    code: str = Field(..., description="지점 코드 (예: MOP)")
    name: str = Field(..., description="지점명 (예: Mokpo Ocean Hotel)")
    is_active: bool = Field(default=True, description="활성 여부")


# ─────────────────────────────────────────────
# 출력용 (GET 응답)
# ─────────────────────────────────────────────
class PropertyOut(BaseModel):
    """Property 출력용 스키마"""
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    code: str = Field(..., description="지점 코드")
    name: str = Field(..., description="지점명")
    is_active: bool = Field(..., description="활성 여부")
    created_at: Optional[datetime] = Field(None, description="생성일시(UTC)")
    updated_at: Optional[datetime] = Field(None, description="수정일시(UTC)")
