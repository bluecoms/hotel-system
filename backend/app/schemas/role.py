# -*- coding: utf-8 -*-
# ============================================================================
# File    : app/schemas/role.py
# Version : 2025-10-31 · v3.5 (SSOT Phase 3.5 Final · DeptAccess Unified)
# Purpose : Hotel Admin — Role / DeptAccess Schema Definitions
# ----------------------------------------------------------------------------
# 목적:
#   • 역할(Role) 및 부서별 접근권한(DeptAccess) 스키마를 SSOT 기준으로 정의.
#   • DeptAccess는 권한 체계의 단일 소스(SSOT)로 사용됨.
# ----------------------------------------------------------------------------
# 변경사항 (v3.5)
#   ✅ RoleAccess / UserRole 구조 완전 폐기
#   ✅ DeptAccess 스키마 확정 (route_name + access_scope)
#   ✅ EffectiveAccessOut → /api/roles/access/effective 스펙 통일
#   ✅ Pydantic v2 / Python 3.8+ 완전 호환
# ----------------------------------------------------------------------------
# 연동 모듈:
#   • app/models/role.py           → Role
#   • app/models/roles_access.py   → DeptAccess
#   • app/routers/roles.py         → /api/roles
#   • app/routers/roles_access.py  → /api/roles/access
#   • src/services/auth.ts         → getEffectiveDeptAccess()
#   • src/stores/auth.ts           → bootstrap() 권한맵 계산
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
    code: str = Field(..., description="역할 코드 (대문자)", example="ADMIN")
    name: Optional[str] = Field("", description="역할명", example="관리자")
    is_active: bool = Field(True, description="활성 여부", example=True)


class RoleOut(BaseModel):
    """역할 출력"""
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="PK")
    code: str = Field(..., description="역할 코드 (대문자)")
    name: str = Field(..., description="역할명")
    is_active: bool = Field(..., description="활성 여부")
    created_at: datetime = Field(..., description="생성일시(UTC)")

# ============================================================================
# 부서별 접근권한 (DeptAccess)
# ============================================================================
class DeptAccessIn(BaseModel):
    """DeptAccess 생성/수정 입력"""
    route_name: str = Field(..., description="라우트 이름 (예: dashboard-kpi)")
    access_scope: List[str] = Field(
        default_factory=list,
        description="접근 허용 부서코드 리스트 (예: ['ALL_VIEW','FR','HK'])",
    )


class DeptAccessOut(BaseModel):
    """DeptAccess 출력"""
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="PK")
    route_name: str = Field(..., description="라우트 이름 (예: dashboard-kpi)")
    access_scope: List[str] = Field(
        default_factory=list,
        description="접근 허용 부서코드 리스트 (예: ['ALL_VIEW','FR','HK'])",
    )
    created_at: Optional[datetime] = Field(None, description="생성일시(UTC)")

# ============================================================================
# Role + DeptAccess 묶음형
# ============================================================================
class RoleWithAccessOut(BaseModel):
    """역할 + 접근권한 리스트 묶음"""
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="역할 PK")
    code: str = Field(..., description="역할 코드")
    name: str = Field(..., description="역할명")
    is_active: bool = Field(..., description="활성 여부")
    created_at: datetime = Field(..., description="생성일시(UTC)")
    access: List[DeptAccessOut] = Field(default_factory=list, description="해당 역할에 연결된 DeptAccess 리스트")

# ============================================================================
# Effective DeptAccess (실효 접근권한)
# ============================================================================
class EffectiveAccessOut(BaseModel):
    """
    실효 접근 결과
    ─────────────────────────────────────────────
    dept   : 기본 부서 코드 (예: MOP)
    access : { route_name: ["ALL_EDIT","FR"] }
    """
    dept: Optional[str] = Field(None, description="기준 부서 코드", example="MOP")
    access: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="라우트별 접근가능 부서코드 매핑",
        example={"hr/employees": ["ALL_EDIT", "FR"], "dashboard-kpi": ["ALL_VIEW"]},
    )

# ============================================================================
# End of File — app/schemas/role.py
# ============================================================================
