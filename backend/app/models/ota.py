# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/models/ota.py
# Version   : 2025.10-27 · v3.6 (Add Master FK · SSOT Verified)
# Purpose   : Hotel Admin — OTA Domain Models (채널·수수료·주문)
# ----------------------------------------------------------------------------
# 목적:
#   • OTA(Online Travel Agency) 관련 운영 데이터 모델 정의
#   • OTA 채널, 수수료, 주문 데이터 구조 관리
#   • MasterOtaChannel 과 master_id(FK) 연동 — SSOT 기준정보 일원화
# ----------------------------------------------------------------------------
# 구조:
#   OTAChannel    → OTA 채널 정보 (운영 데이터)
#   OTACommission → OTA 수수료 이력
#   OTAOrder      → OTA 예약/주문 내역
# ----------------------------------------------------------------------------
# 연계:
#   • app/models/master_ota_channel.py → MasterOtaChannel
#   • app/routers/ota.py               → /api/ota/*
#   • app/schemas/ota.py               → OTAChannelIn/Out 등
# ----------------------------------------------------------------------------
# 변경 로그:
#   v3.6 (2025-10-27)
#     ✅ master_id(FK → master_ota_channels.id) 추가
#     ✅ 주석/인덱스/관계 구조 SSOT 표준화
# ============================================================================

from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Date, Float, Text, DateTime, Index,
    UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.db.base_class import Base


# ============================================================================
# 1️⃣ OTAChannel — OTA 채널 정보 (운영 데이터)
# ----------------------------------------------------------------------------
# • MasterOtaChannel 과 FK(master_id)로 연동 (기준정보 참조)
# • code 는 유니크(대문자), name 은 표시용
# ============================================================================
class OTAChannel(Base):
    __tablename__ = "ota_channels"

    id = Column(Integer, primary_key=True, index=True)

    # ex) "BOOKING", "AGODA"
    code = Column(String(16), unique=True, nullable=False, index=True)

    # ex) "Booking.com"
    name = Column(String(100), nullable=False)

    # ✅ Master 기준정보 연동 FK
    master_id = Column(Integer, ForeignKey("master_ota_channels.id", ondelete="SET NULL"), nullable=True, index=True)

    # 선택 필드(있으면 사용)
    status = Column(String(20), default="", nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 수수료(Commission) 관계
    commissions = relationship(
        "OTACommission",
        back_populates="channel",
        cascade="all, delete-orphan",
    )

    # Master 채널 관계
    master_channel = relationship("MasterOtaChannel", backref="ota_channels", lazy="joined")

    def __repr__(self):
        return f"<OTAChannel id={self.id} code={self.code!r} master_id={self.master_id}>"


# ============================================================================
# 2️⃣ OTACommission — OTA 수수료 이력
# ----------------------------------------------------------------------------
# • 채널별 수수료율(%)의 기간별 변동 관리
# • rate: 0.0~1.0 저장 (예: 0.15 == 15%)
# ============================================================================
class OTACommission(Base):
    __tablename__ = "ota_commissions"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(
        Integer,
        ForeignKey("ota_channels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    valid_from = Column(Date, nullable=False, index=True)
    valid_to   = Column(Date, nullable=False, index=True)
    rate       = Column(Float, nullable=False)  # 저장 시 0.0~1.0

    effective_date = Column(Date, nullable=False, index=True)
    note = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    channel = relationship("OTAChannel", back_populates="commissions")

    def __repr__(self):
        return f"<OTACommission id={self.id} channel_id={self.channel_id} rate={self.rate}>"

# 복합 인덱스 (채널+기간)
Index(
    "ix_ota_commissions_channel_period",
    OTACommission.channel_id, OTACommission.valid_from, OTACommission.valid_to
)


# ============================================================================
# 3️⃣ OTAOrder — OTA 예약 / 주문 내역
# ----------------------------------------------------------------------------
# • OTA 예약(주문) 데이터 관리
# • 채널명은 문자열로 직접 저장 (FK 아님, 기록 추적용)
# ============================================================================
class OTAOrder(Base):
    __tablename__ = "ota_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel = Column(String(40), nullable=False, index=True)   # 문자열 보관
    order_code = Column(String(80), nullable=False, index=True)
    guest_name = Column(String(120), default="")

    check_in  = Column(String(10), index=True)  # "YYYY-MM-DD"
    check_out = Column(String(10), index=True)

    status = Column(String(20), index=True)     # CONFIRMED / CANCELLED / PENDING
    amount = Column(Integer, default=0)
    currency = Column(String(8), default="KRW")

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        UniqueConstraint("order_code", name="uq_ota_orders_order_code"),
        Index("ix_ota_orders_channel_status_created", "channel", "status", "created_at"),
    )

    def __repr__(self):
        return f"<OTAOrder id={self.id} order_code={self.order_code!r} channel={self.channel!r}>"
