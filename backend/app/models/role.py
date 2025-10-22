# -*- coding: utf-8 -*-
# ============================================================================
# File    : app/models/role.py
# Version : 2025-10-22 · v3.1 (DeptAccess Migration · SSOT)
# Purpose : Hotel Admin — 역할(Role) 및 부서별 접근권한(DeptAccess) 모델 정의
# ----------------------------------------------------------------------------
# 목적:
#   • Role / UserRole — 기존 역할 및 사용자 매핑 구조 유지
#   • RoleAccess — DeptAccess 확장 버전 (부서별 접근 제어 리스트)
# ----------------------------------------------------------------------------
# 변경사항 (v3.1)
#   ✅ role_code / access_level 필드 완전 제거
#   ✅ access_scope : JSON 컬럼 (부서코드 리스트)
#       예: ["ALL_VIEW", "FR", "HK", "AD"]
#   ✅ route_name 기준 UniqueConstraint 유지
# ----------------------------------------------------------------------------
# 설계 원칙:
#   • SUPERADMIN 은 모든 route 접근 허용 (별도 정책)
#   • access_scope 필드는 항상 List[str] 형태(JSON 직렬화)
#   • ORM/Pydantic 간 타입 호환 (List[str] ↔ JSON)
# ----------------------------------------------------------------------------
# 연동 모듈:
#   • app/schemas/role.py
#   • app/routers/roles.py
#   • src/views/Admin/RoleAccess.vue
# ============================================================================
from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import (
    Integer, String, Boolean, DateTime, ForeignKey,
    UniqueConstraint, JSON
)
from app.db.base_class import Base

# ============================================================================
# 역할(Role) 테이블
# ============================================================================
class Role(Base):
    """역할(Role) 기준정보"""
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False, doc="역할 코드")
    name: Mapped[str] = mapped_column(String(120), default="", nullable=False, doc="역할명")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, doc="활성 여부")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, doc="생성일시(UTC)")

# ============================================================================
# 사용자 ↔ 역할 매핑 (UserRole)
# ============================================================================
class UserRole(Base):
    """사용자와 역할 간 매핑 테이블"""
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, doc="사용자 ID")
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True, doc="역할 ID")

# ============================================================================
# 부서별 접근권한 매트릭스 (DeptAccess)
# ============================================================================
class RoleAccess(Base):
    """
    DeptAccess 접근 매트릭스
    ───────────────────────────────────────────────
    route_name   : 페이지(라우트) 식별자
    access_scope : 접근 가능한 부서코드 리스트(JSON)
                   예: ["ALL_VIEW", "FR", "HK", "AD"]
    created_at   : 생성일시
    """
    __tablename__ = "role_access"
    __table_args__ = (UniqueConstraint("route_name", name="uq_role_access_route"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    route_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True, doc="라우트 이름 (예: dashboard-kpi)")
    access_scope: Mapped[List[str]] = mapped_column(JSON, default=list, doc="허용된 부서 코드 리스트(JSON)")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, doc="생성일시(UTC)")

    def __repr__(self) -> str:
        return f"<DeptAccess route='{self.route_name}' scopes={self.access_scope}>"
