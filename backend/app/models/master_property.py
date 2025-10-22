# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/models/master_property.py
# Version   : 2025.10-24 · v1.3 (CRUD Ready + Audit Fields · SSOT Stable)
# Purpose   : Hotel Admin — MasterProperty ORM (전역 지점 정보)
# ----------------------------------------------------------------------------
# 목적:
#   • 호텔/지점(Property) 기준정보 테이블 정의
#   • 시스템 전역에서 공용 참조 (property_code FK)
#   • Master 계열이지만 전역화된 엔드포인트(/api/properties)를 사용
# ----------------------------------------------------------------------------
# 주요 변경(v1.3):
#   ✅ updated_at 필드 추가 (수정 이력 추적)
#   ✅ repr 문자열 확장 (생성·수정일 표시)
# ----------------------------------------------------------------------------
# 구조:
#   • code        : 지점 코드 (예: MOP)
#   • name        : 지점명 (예: 목포오션호텔)
#   • is_active   : 사용 여부
#   • created_at  : 등록일시
#   • updated_at  : 수정일시
# ----------------------------------------------------------------------------
# 연계:
#   • app/schemas/master_property.py → PropertyBase / PropertyOut / PropertyUpdate
#   • app/routers/master_property.py → /api/properties CRUD
#   • 참조 예시: employees.property_code, bank_accounts.property_code 등
# ============================================================================

from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime, UniqueConstraint, Index, event
)
from app.db.base_class import Base


class MasterProperty(Base):
    """지점(Property) 기준정보 테이블"""

    __tablename__ = "properties"

    code = Column(String(20), primary_key=True, index=True, comment="지점 코드 (예: MOP)")
    name = Column(String(100), nullable=False, comment="지점명 (예: 목포오션호텔)")
    is_active = Column(Boolean, default=True, nullable=False, comment="사용 여부")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="등록일시")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="수정일시"
    )

    __table_args__ = (
        UniqueConstraint("code", name="uq_properties_code"),
        Index("ix_properties_name", "name"),
        {"extend_existing": True},
    )

    def __repr__(self):
        return (
            f"<MasterProperty(code={self.code}, name={self.name}, active={self.is_active}, "
            f"created_at={self.created_at}, updated_at={self.updated_at})>"
        )


# ─────────────────────────────────────────────
#  이벤트 훅: 수정 시 updated_at 자동 갱신
# ─────────────────────────────────────────────
@event.listens_for(MasterProperty, "before_update", propagate=True)
def receive_before_update(mapper, connection, target):
    """update 전 updated_at 자동 설정"""
    target.updated_at = datetime.utcnow()
