# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/models/property.py
# Version   : 2025.10-26 · v2.0 (SSOT Final · 운영용 ORM)
# Purpose   : Hotel Admin — Property(지점) 운영 테이블 ORM
# ----------------------------------------------------------------------------
# 목적:
#   • 호텔 시스템 전역에서 사용하는 "운영용 지점(Property)" 테이블
#   • MasterProperty(SSOT 관리 테이블)에서 자동 동기화됨
#   • 직원(Employee), 계약(Contract), 마감(Closing), 업로드(Upload) 등
#     모든 도메인의 상위 식별자(FK)로 사용된다.
# ----------------------------------------------------------------------------
# 설계 원칙:
#   • code(PK) : 문자열 기반 (예: MOP, SEO, BUS 등)
#   • name     : 사람이 읽을 수 있는 호텔명
#   • is_active: 활성 여부
#   • created_at / updated_at : UTC 기준 자동 기록
# ----------------------------------------------------------------------------
# 연관 관계:
#   • MasterProperty → Property (단방향 싱크)
#   • Employees.property_code (FK)
#   • Contracts.property_code (FK)
#   • Closing, Upload, Reports 등 모든 도메인 참조
# ----------------------------------------------------------------------------
# 운영 정책:
#   • CRUD 불가 (조회 전용)
#   • 데이터 생성/수정은 /api/master/properties 에서만 수행
# ----------------------------------------------------------------------------
# 변경 이력(v2.0):
#   ✅ SSOT 구조 반영 (Master → Property 일방향 싱크)
#   ✅ 주석/용어 정비 (운영용 ORM으로 명확화)
#   ✅ Alembic extend_existing 설정 유지 (중복 정의 경고 억제)
# ============================================================================
from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base


class Property(Base):
    """호텔 지점(Property) — 운영용 ORM"""

    __tablename__ = "properties"
    __table_args__ = {"extend_existing": True}  # Alembic 중복 경고 억제용

    # ─────────────────────────────
    # 기본 컬럼
    # ─────────────────────────────
    code: Mapped[str] = mapped_column(
        String(10),
        primary_key=True,
        doc="지점 코드 (예: MOP)",
    )
    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        doc="지점명 (예: Mokpo Ocean Hotel)",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="활성 여부",
    )

    # ─────────────────────────────
    # 타임스탬프
    # ─────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        doc="생성일시(UTC)",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        doc="수정일시(UTC)",
    )

    # ─────────────────────────────
    # 표현식 (디버깅용)
    # ─────────────────────────────
    def __repr__(self) -> str:
        return f"<Property(code='{self.code}', name='{self.name}', active={self.is_active})>"
