# app/models/ota.py
from sqlalchemy import Integer, String, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.db.base_class import Base

class OTAOrder(Base):
    __tablename__ = "ota_orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel: Mapped[str] = mapped_column(String(50), index=True)
    order_code: Mapped[str] = mapped_column(String(80))
    guest_name: Mapped[str] = mapped_column(String(120), default="")
    check_in: Mapped[str] = mapped_column(String(10))
    check_out: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20), default="CONFIRMED")
    amount: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(10), default="KRW")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        UniqueConstraint("channel", "order_code", name="uq_ota_channel_code"),
        Index("ix_ota_created", "created_at"),
    )
