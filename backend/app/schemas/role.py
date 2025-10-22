# ============================================================================
# File    : app/schemas/role.py
# Version : 2025-10-21 · v3.0 (DeptAccess Migration · SSOT)
# Purpose : Hotel Admin — Role / DeptAccess Schema Definitions
# ----------------------------------------------------------------------------
# 목적:
#   • 역할(Role) 및 부서별 접근권한(DeptAccess) 스키마 정의
# ----------------------------------------------------------------------------
# 변경사항 (v3.0)
#   ✅ RoleAccess → DeptAccess 구조 전환
#   ✅ access_scope : List[str]  (예: ["ALL_VIEW","FR","HK"])
#   ✅ role_code, access_level 제거
#   ✅ Pydantic v2 표준 (from_attributes=True) 반영
# ----------------------------------------------------------------------------
# 연동 모듈:
#   • app/models/role.py
#   • app/routers/roles.py
#   • src/views/Admin/RoleAccess.vue
# ============================================================================
from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# 역할 (Role)
# ============================================================================
class RoleIn(BaseModel):
    """역할 생성/수정 입력"""
    code: str = Field(..., description="역할 코드 (대문자)")
    name: Optional[str] = Field("", description="역할명")
    is_active: bool = Field(True, description="활성 여부")


class RoleOut(BaseModel):
    """역할 출력"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    is_active: bool
    created_at: datetime

# ============================================================================
# 부서별 접근권한 (DeptAccess)
# ============================================================================
class DeptAccessIn(BaseModel):
    """DeptAccess 생성/수정 입력"""
    route_name: str = Field(..., description="라우트 이름 (예: dashboard-kpi)")
    access_scope: List[str] = Field(default_factory=list, description="접근 허용 부서코드 리스트")


class DeptAccessOut(BaseModel):
    """DeptAccess 출력"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    route_name: str
    access_scope: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None

# ============================================================================
# Role + DeptAccess 묶음형
# ============================================================================
class RoleWithAccessOut(BaseModel):
    """역할 + 접근권한 리스트 묶음"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    is_active: bool
    created_at: datetime
    access: List[DeptAccessOut] = Field(default_factory=list)

# ============================================================================
# Effective DeptAccess (실효 접근권한)
# ============================================================================
class EffectiveAccessOut(BaseModel):
    """사용자 기준 실효 접근 결과"""
    dept: Optional[str] = Field(None, description="사용자 부서 코드")
    access: Dict[str, List[str]] = Field(default_factory=dict, description="라우트별 접근가능 부서코드 매핑")
