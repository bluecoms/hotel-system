from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class ClosingDay(Base):
    __tablename__ = "closing_days"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_code: Mapped[str] = mapped_column(String(20), default="MOP")
    business_date: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20), default="OPEN")

    __table_args__ = (
        UniqueConstraint("property_code", "business_date", name="uq_closing_day"),
    )
