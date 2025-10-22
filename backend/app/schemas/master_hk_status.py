# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/schemas/master_hk_status.py
# Version   : 2025.10-25 · v1.2 (Py39 Compatible · ConfigDict Fix)
# Purpose   : Hotel Admin — MasterHkStatus Schemas (/api/master/hk-status)
# ----------------------------------------------------------------------------
# 목적:
#   • 하우스키핑(Housekeeping) 상태 기준정보용 스키마 정의
#   • Python 3.9 및 Pydantic v2 완전 호환 (ConfigDict → ClassVar 처리)
# ----------------------------------------------------------------------------
# 구성:
#   • MasterHkStatusBase : 공통 필드
#   • MasterHkStatusIn   : 생성/수정 입력용
#   • MasterHkStatusOut  : 조회/응답용 (ORM 변환 지원)
# ============================================================================
from datetime import datetime
from typing import Optional, ClassVar
from pydantic import BaseModel, ConfigDict

# ─────────────────────────────────────────────
# 1️⃣ 공통 스키마
# ─────────────────────────────────────────────
class MasterHkStatusBase(BaseModel):
    """하우스키핑 상태 기본 필드"""
    code: str
    name: str
    is_active: bool = True


# ─────────────────────────────────────────────
# 2️⃣ 입력 스키마
# ─────────────────────────────────────────────
class MasterHkStatusIn(MasterHkStatusBase):
    """신규/수정 입력용 스키마"""
    pass


# ─────────────────────────────────────────────
# 3️⃣ 출력 스키마 (ORM 변환 지원)
# ─────────────────────────────────────────────
class MasterHkStatusOut(MasterHkStatusBase):
    """조회 응답용 스키마"""
    id: int
    created_at: datetime

    # ✅ ClassVar로 명시 (Pydantic이 필드로 인식하지 않음)
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)
