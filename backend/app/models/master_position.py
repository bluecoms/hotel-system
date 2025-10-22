# ============================================================================
# File      : app/models/master_position.py
# Version   : 2025.10-24 · Initial Stable
# Purpose   : Hotel Admin — 마스터 직위(Position) 정보 모델
# ----------------------------------------------------------------------------
# 목적:
#   • 인사/조직관리에서 사용하는 '직위' 기준정보 관리
#   • 예: 대표이사, 본부장, 부장, 과장, 대리, 사원 등
#   • 직원(Employee) 등록 시 선택지로 제공
# ----------------------------------------------------------------------------
# 설계 원칙:
#   • code는 내부 식별자(UNIQUE), name은 표시용 한글명
#   • is_active=False 시 선택 리스트에서 제외
#   • order_no 로 정렬 우선순위 지정
# ----------------------------------------------------------------------------
# 연계:
#   • MasterPosition ↔ Employees (직원등록폼의 선택지)
#   • API: /api/master/positions, /api/master/positions/options
# ============================================================================
from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class MasterPosition(Base):
    """마스터 직위(Position) 기준정보"""

    __tablename__ = "master_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, doc="PK")
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, doc="직위 코드 (예: DIR, MGR)")
    name: Mapped[str] = mapped_column(String(120), nullable=False, doc="직위명 (예: 부장, 과장)")
    order_no: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True, doc="정렬 순서 (낮을수록 위)")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, doc="활성 여부")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, doc="생성 시각(UTC)")

    def __repr__(self) -> str:
        return f"<MasterPosition code={self.code} name={self.name} active={self.is_active}>"
