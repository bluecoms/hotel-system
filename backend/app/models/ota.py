# app/models/ota.py
# -*- coding: utf-8 -*-
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, ForeignKey, Date, Float, Text, DateTime, Index,
    UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class OTAChannel(Base):
    __tablename__ = "ota_channels"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(16), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    commissions = relationship(
        "OTACommission",
        back_populates="channel",
        cascade="all, delete-orphan",
    )

class OTACommission(Base):
    __tablename__ = "ota_commissions"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("ota_channels.id", ondelete="CASCADE"),
                        nullable=False, index=True)

    # 기간 설계: [valid_from, valid_to] 사이 유효. rate는 0.0~1.0 저장(예: 0.15 == 15%)
    valid_from = Column(Date, nullable=False, index=True)
    valid_to   = Column(Date, nullable=False, index=True)
    rate       = Column(Float, nullable=False)

    # 구 설계 호환용(테이블에 NOT NULL 존재) — 읽기는 사용 안 함, 쓰기 시 동기화
    effective_date = Column(Date, nullable=False, index=True)

    note = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    channel = relationship("OTAChannel", back_populates="commissions")

# 교차 기간 인덱스(조회/중복검사 최적화)
Index(
    "ix_ota_commissions_channel_period",
    OTACommission.channel_id, OTACommission.valid_from, OTACommission.valid_to
)

# ===== 신규: OTA 주문 스텁 =====
class OTAOrder(Base):
    __tablename__ = "ota_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # 엔드포인트에서 문자열 비교를 사용하므로 FK 대신 문자열 보관
    channel = Column(String(40), nullable=False, index=True)
    order_code = Column(String(80), nullable=False, index=True)
    guest_name = Column(String(120), default="")

    # 조회/필터를 문자열(YYYY-MM-DD) 비교로 처리하므로 String(10) 사용
    check_in = Column(String(10), index=True)    # "2025-09-30"
    check_out = Column(String(10), index=True)   # "2025-10-02"

    status = Column(String(20), index=True)      # e.g. CONFIRMED / CANCELLED / PENDING
    amount = Column(Integer, default=0)          # KRW 정수 금액
    currency = Column(String(8), default="KRW")

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        UniqueConstraint("order_code", name="uq_ota_orders_order_code"),
        Index("ix_ota_orders_channel_status_created", "channel", "status", "created_at"),
    )
