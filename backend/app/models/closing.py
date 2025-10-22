# app/models/closing.py
# -*- coding: utf-8 -*-
"""
Hotel Admin — Closing / Upload Models
──────────────────────────────────────────────
Version : SSOT Phase 3 Stable v2.9 (2025-10-18)
Author  : Platform Backend Team
──────────────────────────────────────────────
목적:
  • 일자별 마감(ClosingDay) 및 업로드 이력(UploadSession, UploadedFile) 관리
  • SSOT 기반 통합 업로드 구조와 직접 연동
  • UploadSession ↔ UploadedFile 관계는 1:N, CASCADE 삭제 보장
──────────────────────────────────────────────
테이블 구성:
  • closing_days        : 일자별 마감 상태
  • upload_sessions     : 업로드 세션 (dataset/property_code/date)
  • uploaded_files      : 업로드 파일 버전 이력 (session_id + version_no)
──────────────────────────────────────────────
수정 로그:
  ✅ (2025-10-18) UploadedFile.updated_at 컬럼 추가 (DB 구조 일치)
  ✅ UniqueConstraint 및 Index 정비
"""

from datetime import datetime
from sqlalchemy import (
    Integer,
    String,
    UniqueConstraint,
    ForeignKey,
    DateTime,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base_class import Base


# ──────────────────────────────────────────────
# 마감 일자 (ClosingDay)
# ──────────────────────────────────────────────
class ClosingDay(Base):
    __tablename__ = "closing_days"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_code: Mapped[str] = mapped_column(String(20), index=True, default="MOP")
    business_date: Mapped[str] = mapped_column(String(10), index=True)  # YYYY-MM-DD
    status: Mapped[str] = mapped_column(String(20), default="OPEN")

    __table_args__ = (
        UniqueConstraint("property_code", "business_date", name="uq_closing_day"),
        {"extend_existing": True},
    )


# ──────────────────────────────────────────────
# 업로드 세션 (UploadSession)
# ──────────────────────────────────────────────
class UploadSession(Base):
    __tablename__ = "upload_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset: Mapped[str] = mapped_column(String(40), index=True)
    property_code: Mapped[str] = mapped_column(String(20), index=True, default="MOP")
    business_date: Mapped[str] = mapped_column(String(10), index=True)  # YYYY-MM-DD
    status: Mapped[str] = mapped_column(String(20), default="UPLOADED")

    # 관계
    files = relationship("UploadedFile", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_upload_sessions_key", "dataset", "property_code", "business_date"),
        {"extend_existing": True},
    )


# ──────────────────────────────────────────────
# 업로드 파일 (UploadedFile)
# ──────────────────────────────────────────────
class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("upload_sessions.id", ondelete="CASCADE"), index=True
    )
    version_no: Mapped[int] = mapped_column(Integer, index=True)
    filename: Mapped[str] = mapped_column(String(255), default="")
    size: Mapped[int] = mapped_column(Integer, default=0)
    mime: Mapped[str] = mapped_column(String(64), default="text/csv")
    stored_path: Mapped[str] = mapped_column(String(512), default="")
    part_key: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # ✅ DB 구조 반영: updated_at 컬럼 추가
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # 관계
    session = relationship("UploadSession", back_populates="files")

    __table_args__ = (
        Index("ix_uploaded_files_session_ver", "session_id", "version_no"),
        {"extend_existing": True},
    )
