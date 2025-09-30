# app/models/employee.py
from __future__ import annotations

from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    Integer, String, UniqueConstraint, ForeignKey,
    Date, DateTime, Text
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base
from app.models.mixins import SoftDeleteMixin


class Employee(Base, SoftDeleteMixin):
    __tablename__ = "employees"

    id: Mapped[int]        = mapped_column(Integer, primary_key=True)
    emp_no: Mapped[str]    = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str]      = mapped_column(String(120), nullable=False)

    # 기본 조직 필드
    dept: Mapped[str]      = mapped_column(String(120), default="", nullable=False)
    title: Mapped[str]     = mapped_column(String(120), default="", nullable=False)  # 직책(기존)
    position: Mapped[str]  = mapped_column(String(80),  default="", nullable=False)  # 직위
    rank: Mapped[str]      = mapped_column(String(80),  default="", nullable=False)  # 필요시 별도 운용

    # 연락/개인
    phone: Mapped[str]     = mapped_column(String(40),  default="", nullable=False)
    email: Mapped[str]     = mapped_column(String(120), default="", nullable=False)
    address: Mapped[str]   = mapped_column(String(255), default="", nullable=False)

    # 고용
    hire_date:  Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    leave_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # 민감정보(마스킹만 저장)
    rrn_mask: Mapped[str]      = mapped_column(String(20), default="", nullable=False)  # 예: 801125-1**
    bank_name: Mapped[str]     = mapped_column(String(60), default="", nullable=False)  # 예: 농협/국민 등
    account_mask: Mapped[str]  = mapped_column(String(60), default="", nullable=False)  # ***-***-1234
    account_last4: Mapped[str] = mapped_column(String(8),  default="", nullable=False)  # 검색/대조용

    # 기타
    memo: Mapped[str] = mapped_column(Text, default="", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow,
                                                 onupdate=datetime.utcnow, nullable=False)


class UserEmployeeMap(Base):
    __tablename__ = "user_employee_map"

    id: Mapped[int]        = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int]   = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    employee_id: Mapped[int]= mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_single_map"),
    )
