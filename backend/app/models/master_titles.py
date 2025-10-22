# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/models/master_title.py
# Version   : 2025.10-30 · v3.1 (SSOT Final · Hotel Admin Stable)
# Purpose   : Hotel Admin — Master Titles Model (직책 기준정보)
# ----------------------------------------------------------------------------
# 목적:
#   • 호텔 인사/조직 관리용 “직책(Titles)” 기준정보 테이블 정의
#   • 급여등급(master_ranks) 및 직위(master_positions)와 병행 사용
#   • DB 실제 구조(master_titles)에 맞춰 ORM 필드 완전 일치
# ----------------------------------------------------------------------------
# 주요 필드:
#   • code       : 직책 코드 (예: T01, MGR)
#   • name       : 직책명 (예: 리셉셔니스트, 하우스키퍼)
#   • salary     : 직책별 기본급 (Numeric 12,2)
#   • order_no   : 정렬 순서 (UI 정렬용)
#   • is_active  : 사용 여부
#   • created_at : 생성일시 (UTC 기준 자동 기록)
# ----------------------------------------------------------------------------
# 연동:
#   • 스키마 : app/schemas/master_title.py (MasterTitleIn / MasterTitleOut)
#   • 라우터 : app/routers/master_title.py (/api/master/titles)
#   • 프런트 : src/services/master.ts (listTitles / createTitle 등)
# ----------------------------------------------------------------------------
# 참고:
#   • 테이블명은 DB 실제 구조에 맞춰 "master_titles" 로 고정.
#   • Alembic은 stamp head 이후 수동 테이블을 그대로 사용.
# ============================================================================

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Integer, String, Boolean, Numeric, DateTime, UniqueConstraint, text
)
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base


# ============================================================================
# 직책 기준정보 테이블 정의
# ============================================================================
class MasterTitle(Base):
    """호텔 어드민 — 직책 기준정보 (Master Titles)"""

    __tablename__ = "master_titles"  # ✅ DB 실제 테이블명 고정

    # ─────────────────────────────
    # 기본키 / 코드 / 명칭
    # ─────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, doc="PK")
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, doc="직책 코드 (예: T01, MGR)")
    name: Mapped[str] = mapped_column(String(100), nullable=False, doc="직책명 (예: 리셉셔니스트, 하우스키퍼)")

    # ─────────────────────────────
    # 급여 / 정렬 / 상태
    # ─────────────────────────────
    salary: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True, doc="직책 기본급 (월)")
    order_no: Mapped[int] = mapped_column(Integer, default=0, nullable=False, doc="정렬 순서")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, doc="사용 여부")

    # ─────────────────────────────
    # 생성일시 (UTC)
    # ─────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        doc="생성 시각 (UTC)"
    )

    # ─────────────────────────────
    # 제약조건
    # ─────────────────────────────
    __table_args__ = (
        UniqueConstraint("code", name="uq_master_titles_code"),
        {"extend_existing": True},
    )

    # ─────────────────────────────
    # 표현식
    # ─────────────────────────────
    def __repr__(self):
        return f"<MasterTitle id={self.id}, code={self.code}, name={self.name}, active={self.is_active}>"
