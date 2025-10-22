# ============================================================================
# File    : app/schemas/role_map.py
# Version : 2025-10-31 · v2.2 (Pydantic v2 Fix · SSOT Final Stable)
# Purpose : Hotel Admin — User ↔ Role 매핑 스키마 정의
# ----------------------------------------------------------------------------
# 목적:
#   • 사용자(User)와 역할(Role) 간 매핑(UserRole) 데이터 구조 정의
#   • API 입출력 계약 표준화 (입력/출력 스키마 일관성)
# ----------------------------------------------------------------------------
# 변경사항 (v2.2)
#   ✅ Pydantic v2 대응 (regex → pattern 변경)
#   ✅ Python 3.8 완전 호환 (Optional/List 기반 유지)
#   ✅ total 기본값 0 지정 (누락 시 안전)
#   ✅ SSOT 주석 규격 유지
# ============================================================================
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

# ============================================================================
# 입력 (IN)
# ============================================================================
class RoleMapIn(BaseModel):
    """사용자-역할 매핑 생성 입력"""
    user_id: int = Field(..., description="대상 사용자 ID")
    role_code: str = Field(
        ...,
        description="부여할 역할 코드 (대문자 권장)",
        min_length=1,
        pattern=r"^[A-Za-z0-9_\-\.]+$",  # ✅ regex → pattern (Pydantic v2)
    )

# ============================================================================
# 출력 (OUT)
# ============================================================================
class RoleMapOut(BaseModel):
    """단일 매핑 출력"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    role_code: str
    created_at: Optional[datetime] = None


class RoleMapListOut(BaseModel):
    """매핑 목록 출력"""
    model_config = ConfigDict(from_attributes=True)

    items: List[RoleMapOut] = Field(default_factory=list, description="매핑 리스트")
    total: int = Field(default=0, description="전체 개수")
