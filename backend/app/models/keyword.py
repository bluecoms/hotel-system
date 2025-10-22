# app/models/keyword.py
from sqlalchemy import Integer, String, Boolean, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.db.base_class import Base

class Keyword(Base):
    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_name: Mapped[str] = mapped_column(String(50), index=True, default="default")
    k: Mapped[str] = mapped_column(String(100))
    v: Mapped[str] = mapped_column(String(255), default="")
    weight: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("group_name", "k", name="uq_keyword_group_key"),
        Index("ix_keywords_active_weight", "is_active", "weight"),
    )
