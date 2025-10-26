# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/models/master_property.py
# Version   : 2025.10-26 · v2.0 (SSOT Final · MasterProperty 전용)
# Purpose   : Hotel Admin — MasterProperty ORM (지점 기준정보 · SSOT 관리 테이블)
# ----------------------------------------------------------------------------
# 목적:
#   • 호텔/지점(Property) 기준정보의 **단일 진실 원천(SSOT)** 테이블
#   • 관리자가 /api/master/properties 에서 직접 CRUD 수행
#   • 수정 시 운영용 Property 테이블(app/models/property.py)로 자동 동기화
# ----------------------------------------------------------------------------
# 설계 원칙:
#   • MasterProperty는 관리용, Property는 운영용
#   • MasterProperty → Property 단방향 싱크 구조
#   • Property는 모든 운영 도메인의 FK 기준 (employees, contracts 등)
# ----------------------------------------------------------------------------
# 스키마 구조:
#   • code        : 지점 코드 (예: MOP)
#   • name        : 지점명 (예: 목포오션호텔)
#   • is_active   : 사용 여부
#   • created_at  : 등록일시
#   • updated_at  : 수정일시 (자동 갱신)
# ----------------------------------------------------------------------------
# 연계:
#   • app/schemas/master_property.py → MasterPropertyCreate / MasterPropertyOut
#   • app/routers/master_property.py → /api/master/properties (CRUD)
#   • app/models/property.py         → 운영용 참조 테이블
# ----------------------------------------------------------------------------
# 변경이력(v2.0):
#   ✅ SSOT 구조 확립 (Master ↔ Property 분리)
#   ✅ 주석 및 연계 관계 최신화
#   ✅ updated_at 자동 갱신 유지
# ============================================================================

from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime, UniqueConstraint, Index, event
)
from app.db.base_class import Base


class MasterProperty(Base):
    """지점(Property) 기준정보 — SSOT 관리 테이블"""

    __tablename__ = "master_property"

    code = Column(String(20), primary_key=True, index=True, comment="지점 코드 (예: MOP)")
    name = Column(String(100), nullable=False, comment="지점명 (예: 목포오션호텔)")
    is_active = Column(Boolean, default=True, nullable=False, comment="사용 여부")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="등록일시")
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="수정일시"
    )

    __table_args__ = (
        UniqueConstraint("code", name="uq_master_property_code"),
        Index("ix_master_property_name", "name"),
        {"extend_existing": True},
    )

    def __repr__(self):
        return (
            f"<MasterProperty(code={self.code}, name={self.name}, active={self.is_active}, "
            f"created_at={self.created_at}, updated_at={self.updated_at})>"
        )


# ─────────────────────────────────────────────
# 이벤트 훅: 수정 시 updated_at 자동 갱신
# ─────────────────────────────────────────────
@event.listens_for(MasterProperty, "before_update", propagate=True)
def receive_before_update(mapper, connection, target):
    """update 전 updated_at 자동 설정"""
    target.updated_at = datetime.utcnow()
