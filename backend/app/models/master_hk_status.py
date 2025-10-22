# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/models/master_hk_status.py
# Version   : 2025.10-25 · v1.0 (Initial Create · SSOT Stable)
# Purpose   : Hotel Admin — MasterHkStatus ORM (하우스키핑 상태 기준정보)
# ----------------------------------------------------------------------------
# 목적:
#   • 객실 하우스키핑 상태(청소/점검/비가용 등)를 코드 단위로 관리
#   • 상태코드(code), 이름(name), 활성여부(is_active) 구조 유지
# ----------------------------------------------------------------------------
# 연계:
#   • app/schemas/master_hk_status.py → MasterHkStatusIn / MasterHkStatusOut
#   • app/routers/master_hk_status.py → /api/master/hk-status
# ============================================================================
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, UniqueConstraint, Index
from app.db.base_class import Base

class MasterHkStatus(Base):
    """하우스키핑 상태 기준정보"""

    __tablename__ = "master_hk_status"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), nullable=False, unique=True, comment="상태 코드 (예: CLEAN, DIRTY, OOO)")
    name = Column(String(100), nullable=False, comment="상태명 (예: 청소완료, 미청소, 비가용 등)")
    is_active = Column(Boolean, default=True, nullable=False, comment="활성 여부")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="등록일시")

    __table_args__ = (
        UniqueConstraint("code", name="uq_hk_status_code"),
        Index("ix_hk_status_name", "name"),
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<MasterHkStatus(code={self.code}, name={self.name}, active={self.is_active})>"
