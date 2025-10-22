# ============================================================================
# File    : app/schemas/role_map.py
# Version : 2025-10-21 · v2.0 (SSOT / Pydantic v2 정비판)
# Purpose : Hotel Admin — User ↔ Role 매핑 스키마 정의
# ----------------------------------------------------------------------------
# 목적:
#   • 사용자(User)와 역할(Role) 간의 매핑(UserRole) 데이터 구조 정의
#   • API 입출력에서 UserRole 테이블의 데이터 계약을 표준화
# ----------------------------------------------------------------------------
# 변경사항 (v2.0)
#   ✅ Pydantic v2 규격 반영 (ConfigDict(from_attributes=True))
#   ✅ 주석 SSOT 규격화
#   ✅ 필드 설명(description) 명확화
# ----------------------------------------------------------------------------
# 연동 라우터:
#   • app/routers/user_roles.py
#   • app/models/role.py (UserRole)
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
        pattern=r"^[A-Za-z0-9_\-\.]+$",
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
    items: List[RoleMapOut] = Field(default_factory=list, description="매핑 리스트")
    total: int = Field(..., description="전체 개수")
