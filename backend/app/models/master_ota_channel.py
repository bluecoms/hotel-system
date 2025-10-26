# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/models/master_ota_channel.py
# Version   : 2025.10-31 · v1.0 (Initial · SSOT Standard)
# Purpose   : Hotel Admin — Master OTA Channel Model
# ----------------------------------------------------------------------------
# 목적:
#   • OTA 채널(Booking.com, Agoda, Expedia 등) 기준정보의 단일 소스(SSOT)
#   • 커미션(수수료), OTA 주문/요약 등에서 참조되는 기준 테이블
# ----------------------------------------------------------------------------
# 필드:
#   - id         : PK
#   - code       : 채널 코드(고유, 대문자 권장) ex) BOOKING, AGODA, EXPEDIA
#   - name       : 채널 표시명                  ex) "Booking.com"
#   - is_active  : 사용 여부(기본 True)
#   - order_no   : 정렬용 (선택)
#   - created_at : 생성 시각
#   - updated_at : 수정 시각
# ----------------------------------------------------------------------------
# 참고:
#   • 실제 테이블 생성은 Alembic 마이그레이션에서 처리합니다 (모델만 정의)
#   • 스키마(Pydantic)와 라우터는 별도 파일에서 관리합니다.
# ----------------------------------------------------------------------------
# Naming 규칙 (SSOT 고정)
#   • Model  : app/models/master_ota_channel.py     → 단수
#   • Schema : app/schemas/master_ota_channels.py   → 복수
#   • Router : app/routers/master_ota_channels.py   → 복수
# ============================================================================

from __future__ import annotations
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    func,
    UniqueConstraint,
    Index,
)
from app.db.base_class import Base


class MasterOtaChannel(Base):
    """
    OTA 채널 기준정보 (SSOT)
    - code 는 고유(unique)하며 대문자 사용 권장
    - name 은 표시용 이름
    """

    __tablename__ = "master_ota_channels"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(50), nullable=False, unique=True, index=True)  # ex) "BOOKING"
    name = Column(String(100), nullable=False)  # ex) "Booking.com"
    is_active = Column(Boolean, nullable=False, server_default="1", default=True)
    order_no = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("code", name="uq_master_ota_channels_code"),
        Index("ix_master_ota_channels_active_order", "is_active", "order_no"),
    )

    def __repr__(self) -> str:
        return f"<MasterOtaChannel id={self.id} code={self.code!r} name={self.name!r} active={self.is_active}>"
