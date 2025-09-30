# app/models/upload.py
from datetime import datetime
from sqlalchemy import (
    String, Integer, DateTime, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base

class UploadSession(Base):
    __tablename__ = "upload_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset: Mapped[str] = mapped_column(String(50), index=True)
    property_code: Mapped[str] = mapped_column(String(20), default="MOP")
    business_date: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(30), default="UPLOADED")
    __table_args__ = (UniqueConstraint("dataset", "property_code", "business_date", name="uq_upload_key"),)

class UploadedFile(Base):
    __tablename__ = "upload_files"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("upload_sessions.id"))
    version_no: Mapped[int] = mapped_column(Integer, default=1)
    filename: Mapped[str] = mapped_column(String(255))
    size: Mapped[int] = mapped_column(Integer, default=0)
    mime: Mapped[str] = mapped_column(String(100), default="text/csv")
    stored_path: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    part_key: Mapped[str] = mapped_column(String(120), default="", index=True)

    __table_args__ = (UniqueConstraint("session_id", "version_no", name="uq_session_version"),)
