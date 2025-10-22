# ============================================================================
# File      : app/models/master_bank.py
# Version   : 2025.10-24 v1.2 (Upgraded · order_no / metadata / SSOT Align)
# Purpose   : Hotel Admin — Master Banks Model (기준정보)
# ----------------------------------------------------------------------------
# 목적:
#   • 은행코드(Bank Code) 기준정보를 표준화하여 급여·법인계좌 등에서 공통 사용
#   • 기존 구조에서 order_no / country_code / meta 추가
# ----------------------------------------------------------------------------
# 구조:
#   id           → PK
#   code         → 은행 코드 (예: NH, WR, KB, IBK)
#   name         → 은행명 (예: 농협은행, 우리은행 등)
#   alias        → 약칭 (표시용 이름, 예: 농협, 국민)
#   country_code → 국가코드(예: KR), 다국적 확장 대비
#   order_no     → 정렬 우선순위 (낮을수록 상위)
#   is_active    → 활성여부 (False 시 /options에서 제외)
#   meta         → 부가정보(JSON, 예: 로고URL·BIC코드 등)
#   created_at   → 등록일시(UTC)
# ----------------------------------------------------------------------------
# 변경사항(v1.2)
#   ✅ order_no 컬럼 추가 (정렬용)
#   ✅ country_code, meta(JSON) 추가 (국제화·확장성 대비)
#   ✅ __repr__ 단축 표기 개선
# ----------------------------------------------------------------------------
# 연계:
#   • Employee.bank_name  ← MasterBank.code (FK-like 구조)
#   • BankAccount.bank_code ← MasterBank.code
#   • API: /api/master/banks, /api/master/banks/options
# ============================================================================
from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import (
    Integer, String, Boolean, DateTime, UniqueConstraint, JSON
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class MasterBank(Base):
    """은행코드(Bank Code) 기준정보"""

    __tablename__ = "master_banks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False, doc="은행 코드 (예: NH, WR, KB)")
    name: Mapped[str] = mapped_column(String(100), nullable=False, doc="은행명 (예: 농협은행, 국민은행)")
    alias: Mapped[str] = mapped_column(String(50), default="", nullable=False, doc="약칭/표시명 (예: 농협, 국민)")
    country_code: Mapped[str] = mapped_column(String(5), default="KR", nullable=False, doc="국가 코드 (기본 KR)")
    order_no: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True, doc="정렬 우선순위")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, doc="활성 여부")
    meta: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, doc="부가정보(JSON, 예: 로고URL·BIC 등)")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, doc="생성 시각(UTC)")

    __table_args__ = (
        UniqueConstraint("code", name="uq_master_bank_code"),
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<MasterBank {self.code}·{self.name} active={self.is_active}>"
