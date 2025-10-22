# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/models/ota.py
# Version   : 2025.10-31 · v3.8 (SQLAlchemy 2.x 완전 적용 · SSOT Final)
# Purpose   : Hotel Admin — OTA Domain Models (채널·수수료·주문)
# ----------------------------------------------------------------------------
# 변경 요약:
#   ✅ SQLAlchemy 2.x 타입힌트 (Mapped / mapped_column)
#   ✅ Pydantic v2 및 ORM 연동 정합성 검증 완료
#   ✅ 관계 역참조 · Index · Unique 제약 정비
#   ✅ __repr__ 표준화 (간결 + 식별 가능)
# ----------------------------------------------------------------------------
from __future__ import annotations
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    Integer, String, ForeignKey, Date, Float, Text, DateTime,
    Index, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


# ============================================================================
# 1️⃣ OTAChannel — OTA 채널 정보 (운영 데이터)
# ============================================================================
class OTAChannel(Base):
    """OTA 채널 정보 (운영 데이터)"""
    __tablename__ = "ota_channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # ✅ Master 기준정보 연동 FK
    master_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("master_ota_channels.id", ondelete="SET NULL"),
        index=True,
    )

    status: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 관계 설정
    commissions: Mapped[List["OTACommission"]] = relationship(
        back_populates="channel", cascade="all, delete-orphan"
    )
    master_channel: Mapped[Optional["MasterOtaChannel"]] = relationship(
        "MasterOtaChannel", backref="ota_channels", lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<OTAChannel id={self.id} code='{self.code}' master_id={self.master_id}>"



# ============================================================================
# 2️⃣ OTACommission — OTA 수수료 이력
# ============================================================================
class OTACommission(Base):
    """OTA 수수료 이력 (rate : 0.0 ~ 1.0 저장, 예 0.15 == 15 %)"""
    __tablename__ = "ota_commissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    channel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ota_channels.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    valid_from: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    valid_to: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    rate: Mapped[float] = mapped_column(Float, nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 역관계
    channel: Mapped["OTAChannel"] = relationship(back_populates="commissions")

    __table_args__ = (
        Index("ix_ota_commissions_channel_period", "channel_id", "valid_from", "valid_to"),
    )

    def __repr__(self) -> str:
        return (
            f"<OTACommission id={self.id} channel_id={self.channel_id} "
            f"rate={self.rate:.2f} valid={self.valid_from}→{self.valid_to}>"
        )



# ============================================================================
# 3️⃣ OTAOrder — OTA 예약 / 주문 내역
# ============================================================================
class OTAOrder(Base):
    """OTA 예약 / 주문 내역 (단순 운영 데이터)"""
    __tablename__ = "ota_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    order_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    guest_name: Mapped[str] = mapped_column(String(120), default="")

    check_in: Mapped[Optional[str]] = mapped_column(String(10), index=True)   # YYYY-MM-DD
    check_out: Mapped[Optional[str]] = mapped_column(String(10), index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)               # CONFIRMED/...
    amount: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(8), default="KRW")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        UniqueConstraint("order_code", name="uq_ota_orders_order_code"),
        Index("ix_ota_orders_channel_status_created", "channel", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<OTAOrder id={self.id} order_code='{self.order_code}' channel='{self.channel}'>"
