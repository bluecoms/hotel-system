# backend/app/models/employee_file.py
# -*- coding: utf-8 -*-
# version: 2025-10-12  v2.5
"""
직원 파일(EmployeeFiles)
────────────────────────────────────────────
- append-only 버저닝 구조
- 직원별 문서/스캔파일 관리
────────────────────────────────────────────
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, String, Text, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base


class EmployeeFile(Base):
    __tablename__ = "employee_files"
    __table_args__ = (UniqueConstraint("employee_id", "version_no", name="uq_employee_file_ver"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(80), default="document")  # document/image/pdf
    file_path: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_latest: Mapped[bool] = mapped_column(default=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
