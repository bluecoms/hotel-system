# -*- coding: utf-8 -*-
# ============================================================================
# File    : app/models/user.py
# Version : 2025-10-31 · v3.5 (SSOT Phase 3.5 Final · User Simplified)
# Purpose : Hotel Admin — 사용자(User) ORM 모델 정의 (역할 매핑 제거)
# ----------------------------------------------------------------------------
# 목적:
#   • 사용자 계정 및 인증 관련 기본 테이블(users) 정의
#   • password_hash 기반 로그인 인증
#   • UserRole 테이블 및 roles 관계는 Phase 3.5 이후 완전히 폐기됨
# ----------------------------------------------------------------------------
# 변경사항 (v3.5)
#   ✅ user_roles / Role 관계 완전 제거 (DeptAccess 구조로 전환)
#   ✅ password_hash 필드 유지 (bcrypt 해시 저장용)
#   ✅ created_at 기본값 UTC 기준 통일
#   ✅ 최소 필드 구성으로 단순화
# ----------------------------------------------------------------------------
# 연동 스키마:
#   • app/schemas/users.py
#   • app/routers/users.py
# ----------------------------------------------------------------------------
# 주의:
#   • password는 평문 저장 금지 (hash만 보관)
#   • bcrypt.hash(password) 형태로 처리
#   • 역할/권한은 DeptAccess(roles_access.py) 기반으로 통합 관리됨
# ============================================================================

from __future__ import annotations
from typing import Optional
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, DateTime

from app.db.base_class import Base

# ============================================================================
# 사용자(User) 테이블
# ============================================================================
class User(Base):
    """사용자 계정 / 로그인 엔터티"""
    __tablename__ = "users"

    # 기본 식별자
    id: Mapped[int] = mapped_column(Integer, primary_key=True, doc="PK (자동증가)")

    # 로그인/식별 정보
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False, doc="로그인 이메일")
    name: Mapped[str] = mapped_column(String(120), default="", nullable=False, doc="사용자 이름")

    # 인증 관련
    password_hash: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="비밀번호 해시 (bcrypt)"
    )

    # 상태 및 생성일
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, doc="활성 여부")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, doc="생성일시(UTC)")

    def __repr__(self) -> str:
        return f"<User email='{self.email}' active={self.is_active}>"

# ============================================================================
# End of File — app/models/user.py
# ============================================================================
