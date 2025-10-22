# -*- coding: utf-8 -*-
# ============================================================================
# File    : app/models/role.py
# Version : 2025-10-31 · v3.5 (SSOT Phase 3.5 Final · DeptAccess Unified)
# Purpose : Hotel Admin — 역할(Role) 기준정보 모델
# ----------------------------------------------------------------------------
# 목적:
#   • 역할(Role) 기준정보를 단일 테이블로 유지.
#   • UserRole / RoleAccess 는 폐기되었으며, DeptAccess 는 별도 모델로 분리.
# ----------------------------------------------------------------------------
# 변경사항 (v3.5)
#   ✅ UserRole / RoleAccess 클래스 완전 삭제
#   ✅ DeptAccess 는 app/models/roles_access.py 로 이동
#   ✅ 코드 구조 단순화 (SSOT 일관성)
# ----------------------------------------------------------------------------
# 연동 모듈:
#   • app/schemas/role.py
#   • app/routers/roles.py
#   • src/views/Admin/RoleAccess.vue
# ============================================================================
from __future__ import annotations
from datetime import datetime
from sqlalchemy import Integer, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base

# ============================================================================
# 역할(Role) 테이블
# ============================================================================
class Role(Base):
    """역할(Role) 기준정보"""
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, doc="PK (자동증가)"
    )
    code: Mapped[str] = mapped_column(
        String(80), unique=True, index=True, nullable=False, doc="역할 코드 (예: ADMIN)"
    )
    name: Mapped[str] = mapped_column(
        String(120), default="", nullable=False, doc="역할명"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, doc="활성 여부"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, doc="생성일시(UTC)"
    )

    def __repr__(self) -> str:
        return f"<Role code='{self.code}' active={self.is_active}>"

# ============================================================================
# End of File — app/models/role.py
# ============================================================================
