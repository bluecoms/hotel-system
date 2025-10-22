# -*- coding: utf-8 -*-
# ============================================================================
# File    : app/models/user.py
# Version : 2025-10-23 · v3.1 (Stable / PasswordHash + Role Mapping)
# Purpose : Hotel Admin — 사용자(User) ORM 모델 정의
# ----------------------------------------------------------------------------
# 목적:
#   • 사용자 계정 및 인증 관련 기본 테이블(users) 정의
#   • password_hash 기반 로그인 인증
#   • 역할(Role) 관계는 user_roles 테이블을 통해 Many-to-Many 매핑
# ----------------------------------------------------------------------------
# 변경사항 (v3.1)
#   ✅ password_hash 필드 유지 (nullable=True → 기존 해시 보관용)
#   ✅ created_at 기본값 UTC로 통일
#   ✅ roles 관계 명시 (Role과 selectin 방식)
# ----------------------------------------------------------------------------
# 연동 스키마:
#   • app/schemas/users.py
#   • app/routers/users.py
# ----------------------------------------------------------------------------
# 주의:
#   • password는 평문 저장 금지 (hash만 보관)
#   • bcrypt.hash(password) 형태로 처리
# ============================================================================
from __future__ import annotations
from typing import Optional, List
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey

from app.db.base_class import Base

# ============================================================================
# 사용자(User) 테이블
# ============================================================================
class User(Base):
    """사용자 계정 / 로그인 엔터티"""
    __tablename__ = "users"

    # 기본 식별자
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # 로그인/식별 정보
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), default="", nullable=False)

    # 인증 관련
    password_hash: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="비밀번호 해시 (bcrypt)"
    )

    # 상태 및 생성일
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # ─────────────────────────────────────────────
    # 관계 설정 (Role 테이블과 Many-to-Many)
    # ─────────────────────────────────────────────
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary="user_roles",              # 연결 테이블 (user_roles)
        primaryjoin="User.id==UserRole.user_id",
        secondaryjoin="Role.id==UserRole.role_id",
        viewonly=True,                       # 읽기 전용 (직접 수정은 user_roles 통해)
        lazy="selectin",                     # N+1 방지
        doc="사용자와 역할(Role) 간의 관계 (Many-to-Many)"
    )

# ============================================================================
# END OF FILE · app/models/user.py
# ============================================================================
