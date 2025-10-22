# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/models/contract.py
# Version   : 2025.10-24 Final Stable (v3.8 · DeptJoin Ready + Index Tuning)
# Purpose   : Hotel Admin — 직원 계약 관리 모델 (EmployeeContract · ORM)
# ----------------------------------------------------------------------------
# 목적:
#   • 직원(Employee)과 연결되는 계약(Contract) 정보를 저장 (append-only 버저닝)
#   • 최신 플래그(is_latest) + 버전(version_no) 정책으로 이력(versions) 관리
#   • 계약 확정/종료 시 Employee 테이블(계약 상태/기간)과 동기화
#   • LEFT JOIN(Employee 기준) + Dept JOIN(부서명) 조회를 고려한 인덱스 튜닝
# ----------------------------------------------------------------------------
# 설계 원칙:
#   • 한 직원(employee_id) 내에서 version_no는 유일 (uq_employee_contract_ver)
#   • 수정은 새 레코드를 삽입, 기존 최신레코드는 is_latest=False 처리
#   • 통화는 KRW 고정(프런트 노출 생략), salary는 정밀도 보장을 위해 Numeric(14,2)
#   • Property(지점)는 Employee.property_code를 상위 레벨에서 필터링 (중복 보관 금지)
# ----------------------------------------------------------------------------
# 라우터/스키마 호환:
#   • Router : app/routers/contracts.py (LEFT JOIN + Dept JOIN)
#   • Schema : app/schemas/contract.py  (ContractOut / ContractListResp 등)
# ----------------------------------------------------------------------------
# 관계:
#   • Employee(1) ↔ EmployeeContract(N)
#     - back_populates="contracts"
#     - lazy="joined" 로 N+1 질의 방지
# ----------------------------------------------------------------------------
# 인덱스/제약 (성능·정합성):
#   • UNIQUE (employee_id, version_no)
#   • INDEX  (employee_id, is_latest)   → 최신 계약 조회
#   • INDEX  (employee_id, start_date)  → 기간 기반 조회/정렬
#   • INDEX  (status)                   → 상태 필터
# ============================================================================

from __future__ import annotations

from datetime import datetime, date
from typing import Optional, Any, Dict

from sqlalchemy import (
    Integer, String, Date, DateTime, Text,
    ForeignKey, Boolean, UniqueConstraint, JSON, Numeric, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class EmployeeContract(Base):
    """직원 계약(EmployeeContract) — Append-only 버저닝 모델"""

    __tablename__ = "employee_contracts"
    __table_args__ = (
        # 한 직원 내에서 버전 번호는 유일
        UniqueConstraint("employee_id", "version_no", name="uq_employee_contract_ver"),
        # 조회 성능 인덱스
        Index("ix_emp_contract_latest", "employee_id", "is_latest"),
        Index("ix_emp_contract_start", "employee_id", "start_date"),
        Index("ix_emp_contract_status", "status"),
        {"extend_existing": True},
    )

    # ──────────────────────────────
    # 기본 키 / 직원 FK
    # ──────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, doc="계약 PK")
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="직원 FK (employees.id)",
    )

    # ──────────────────────────────
    # 계약 기본 정보
    # ──────────────────────────────
    contract_type: Mapped[str] = mapped_column(
        String(60),
        default="MONTHLY",
        nullable=False,
        doc="계약 유형 (예: MONTHLY, HOURLY, FIXED 등)"
    )
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, doc="계약 시작일")
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, doc="계약 종료일")

    pay_type: Mapped[str] = mapped_column(String(20), default="MONTHLY", nullable=False, doc="지급 방식 (MONTHLY/HOURLY)")
    salary: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True, doc="급여 금액 (원화 기준)")
    currency: Mapped[str] = mapped_column(String(10), default="KRW", nullable=False, doc="통화 코드 (기본 KRW)")

    status: Mapped[str] = mapped_column(
        String(20),
        default="draft",
        nullable=False,
        doc="계약 상태 (draft/active/terminated)"
    )
    memo: Mapped[str] = mapped_column(Text, default="", nullable=False, doc="비고/메모")

    # ──────────────────────────────
    # 파일/계약서/부가정보
    # ──────────────────────────────
    file_path: Mapped[str] = mapped_column(String(255), default="", nullable=False, doc="계약서 파일 경로(선택)")
    contract_no: Mapped[Optional[str]] = mapped_column(String(100), default="", nullable=True, doc="계약 번호(선택)")
    meta: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, doc="계약서 스냅샷/양식 메타(JSON)")

    # ──────────────────────────────
    # 버저닝 관리
    # ──────────────────────────────
    version_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False, doc="버전 번호 (append-only)")
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, doc="최신 버전 여부")

    # ──────────────────────────────
    # 생성/수정 메타
    # ──────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        doc="생성 시각 (UTC)"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        doc="수정 시각 (UTC)"
    )

    # ──────────────────────────────
    # 관계 (직원 ↔ 계약)
    # ──────────────────────────────
    employee = relationship(
        "Employee",
        back_populates="contracts",
        lazy="joined",  # joinedload() 기본
    )

    # ──────────────────────────────
    # 리프레젠테이션
    # ──────────────────────────────
    def __repr__(self) -> str:
        return (
            f"<EmployeeContract(id={self.id}, emp_id={self.employee_id}, "
            f"type='{self.contract_type}', status='{self.status}', "
            f"ver={self.version_no}, latest={self.is_latest})>"
        )
