# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/schemas/master_property.py
# Version   : 2025.10-26 · v2.0 (SSOT Final · MasterProperty 전용)
# Purpose   : Hotel Admin — MasterProperty Schemas (/api/master/properties)
# ----------------------------------------------------------------------------
# 목적:
#   • 호텔/지점(Property) 기준정보(SSOT)용 Pydantic 스키마 정의
#   • 관리자 전용 /api/master/properties CRUD에 사용
#   • Python 3.9 + Pydantic v2 완전 호환 (ClassVar + ConfigDict)
# ----------------------------------------------------------------------------
# 구성:
#   • MasterPropertyBase   : 공통 필드(code, name, is_active)
#   • MasterPropertyCreate : 생성 입력용
#   • MasterPropertyUpdate : 수정 입력용
#   • MasterPropertyOut    : 조회/응답용 (ORM 변환 지원)
# ----------------------------------------------------------------------------
# 연계:
#   • app/models/master_property.py → MasterProperty ORM
#   • app/routers/master_property.py → /api/master/properties CRUD
#   • app/models/property.py         → 운영용 테이블 (동기화 대상)
# ============================================================================
from typing import Optional, ClassVar
from pydantic import BaseModel, ConfigDict

# ─────────────────────────────────────────────
# 1️⃣ 공통 베이스 (기준정보 기본 필드)
# ─────────────────────────────────────────────
class MasterPropertyBase(BaseModel):
    """기준정보 공통 필드 정의"""
    code: str                      # 지점 코드 (예: MOP)
    name: str                      # 지점명 (예: 목포오션호텔)
    is_active: bool = True         # 사용 여부


# ─────────────────────────────────────────────
# 2️⃣ 생성 입력 스키마
# ─────────────────────────────────────────────
class MasterPropertyCreate(MasterPropertyBase):
    """신규 지점 등록용 입력 스키마"""
    pass


# ─────────────────────────────────────────────
# 3️⃣ 수정 입력 스키마 (PUT /master/properties/{code})
# ─────────────────────────────────────────────
class MasterPropertyUpdate(BaseModel):
    """지점 수정용 스키마 (선택 필드만 허용)"""
    name: Optional[str] = None
    is_active: Optional[bool] = None


# ─────────────────────────────────────────────
# 4️⃣ 출력/응답 스키마
# ─────────────────────────────────────────────
class MasterPropertyOut(MasterPropertyBase):
    """조회 응답용 스키마"""
    # ✅ Python 3.9 + Pydantic v2 완전 호환 (ORM 변환 지원)
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)
