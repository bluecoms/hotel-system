# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/schemas/master_property.py
# Version   : 2025.10-24 · v1.5 (ClassVar ConfigDict · Py39 Stable · SSOT Final)
# Purpose   : Hotel Admin — Global Property Schemas (/api/properties)
# ----------------------------------------------------------------------------
# 목적:
#   • 호텔/지점(Property) 기준정보용 Pydantic 스키마 정의
#   • Python 3.9 + Pydantic v2 완전 호환 (ClassVar + ConfigDict)
#   • /api/properties 전역 엔드포인트에서 사용 (Master 전역화 대상)
# ----------------------------------------------------------------------------
# 구성:
#   • PropertyBase   : 공통 필드(code, name, is_active)
#   • PropertyCreate : 생성 입력용 (추후 확장 대비)
#   • PropertyUpdate : 수정 입력용 (MasterTable PUT 대응)
#   • PropertyOut    : 조회/응답용 (ORM 변환 지원)
# ----------------------------------------------------------------------------
# 연계:
#   • app/models/master_property.py → MasterProperty ORM
#   • app/routers/master_property.py → /api/properties CRUD API
#   • 프런트엔드: PropertyTable.vue (MasterTable 기반)
# ============================================================================
from typing import Optional, ClassVar
from pydantic import BaseModel, ConfigDict

# ─────────────────────────────────────────────
# 1️⃣ 공통 베이스 (기준정보 기본 필드)
# ─────────────────────────────────────────────
class PropertyBase(BaseModel):
    """공통 필드 정의"""
    code: str                      # 지점 코드 (예: MOP)
    name: str                      # 지점명 (예: 목포오션호텔)
    is_active: bool = True         # 사용 여부


# ─────────────────────────────────────────────
# 2️⃣ 생성 입력 스키마
# ─────────────────────────────────────────────
class PropertyCreate(PropertyBase):
    """신규 지점 등록용 입력 스키마"""
    pass


# ─────────────────────────────────────────────
# 3️⃣ 수정 입력 스키마 (PUT /properties/{code})
# ─────────────────────────────────────────────
class PropertyUpdate(BaseModel):
    """지점 수정용 스키마 (선택 필드)"""
    name: Optional[str] = None
    is_active: Optional[bool] = None


# ─────────────────────────────────────────────
# 4️⃣ 출력/응답 스키마
# ─────────────────────────────────────────────
class PropertyOut(PropertyBase):
    """조회 응답용 스키마"""
    # ✅ Python 3.9 + Pydantic v2 완전 호환 (ClassVar 명시)
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)
