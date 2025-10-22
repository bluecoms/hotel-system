# -*- coding: utf-8 -*-
# ============================================================================
# File    : app/schemas/users.py
# Version : 2025-10-31 · v3.5 (SSOT Phase 3.5 Final · Role Mapping Removed)
# Purpose : Hotel Admin — 사용자(User) 생성·조회·활성화 스키마 정의
# ----------------------------------------------------------------------------
# 목적:
#   • 사용자 등록(UserCreate) / 목록(UserListOut) / 활성화(UserActivateIn)
#     / 사원기반 생성(CreateFromEmployeeIn) 요청·응답 구조 정의
# ----------------------------------------------------------------------------
# 변경사항 (v3.5)
#   ✅ UserRole / RoleAccess 관계 완전 제거 (DeptAccess 구조로 전환)
#   ✅ UserListOut.employee_id 유지 (사원 연결용)
#   ✅ password 필드 Optional (없으면 기본값 hotel1234)
#   ✅ Pydantic v2 호환 (ConfigDict + from_attributes=True)
# ----------------------------------------------------------------------------
# 연동 라우터:
#   • app/routers/users.py
#   • POST /api/users
#   • POST /api/users/from-employee
# ----------------------------------------------------------------------------
# 주의:
#   • 사용자 권한은 DeptAccess(roles_access.py) 기반으로 통합 관리됨
#   • UserRole / user_roles 테이블은 완전히 폐기됨
# ============================================================================

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict, Field

# ============================================================================
# 1️⃣ 신규 사용자 등록 (SUPERADMIN)
# ============================================================================
class UserCreate(BaseModel):
    """신규 사용자 등록 요청 스키마"""
    name: str = Field(..., description="사용자 이름")
    email: EmailStr = Field(..., description="이메일 주소 (로그인 ID)")
    password: Optional[str] = Field(
        None,
        description="초기 비밀번호 (선택, 없으면 기본 hotel1234)",
        example="hotel1234",
    )
    is_active: bool = Field(True, description="활성 여부 (기본값: True)", example=True)

# ============================================================================
# 2️⃣ 사용자 목록 출력
# ============================================================================
class UserListOut(BaseModel):
    """사용자 목록 조회 응답 스키마"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="사용자 ID")
    name: str = Field(..., description="이름")
    email: EmailStr = Field(..., description="이메일 (로그인 ID)")
    is_active: bool = Field(..., description="활성 여부")
    employee_id: Optional[int] = Field(
        None, description="연결된 사원 ID (없으면 None)", example=None
    )

# ============================================================================
# 3️⃣ 사용자 활성화/비활성화 요청
# ============================================================================
class UserActivateIn(BaseModel):
    """사용자 활성화/비활성화 입력"""
    is_active: bool = Field(
        True,
        description="활성 여부 (True=활성, False=비활성)",
        example=True,
    )

# ============================================================================
# 4️⃣ 사원으로부터 사용자 생성 요청 (HRADMIN+)
# ============================================================================
class CreateFromEmployeeIn(BaseModel):
    """사원(Employee)으로부터 사용자 자동 생성 요청"""
    employee_id: int = Field(..., description="대상 사원 ID")
    email: EmailStr = Field(..., description="등록할 이메일 주소 (없으면 사원정보 기반 자동)")
    is_active: bool = Field(True, description="활성 여부 (기본 True)", example=True)

# ============================================================================
# End of File — app/schemas/users.py
# ============================================================================
