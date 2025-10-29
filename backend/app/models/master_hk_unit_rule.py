# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/models/master_hk_unit_rule.py
# Version   : 2025-11-09 · v1.2 (order_no 확장 · SSOT 완전판)
# Purpose   : Hotel Admin — 하우스키핑 유닛 계산 규칙 마스터
# ----------------------------------------------------------------------------
# 목적:
#   • 하우스키핑 업무 단위(유닛) 계산 규칙을 관리하는 기준정보 테이블
#   • 룸타입(MasterRoomType)과 별도로 조건 기반 가중치 제공
#   • 예: BASE=1.0 / OCCUPIED=0.3 / MOVED=0.2 등
# ----------------------------------------------------------------------------
# 확장 포인트(v1.2):
#   ✅ order_no 필드 추가 → MasterTable 드래그 정렬 기능 지원
#   ✅ 기존 모델과 완전 하위 호환 (Alembic auto-generate 가능)
# ----------------------------------------------------------------------------
# 연계:
#   • schemas.master_hk_unit_rule
#   • routers.master_hk_unit_rule
#   • housekeeping_service (유닛 계산 로직 참조)
#   • 프런트 MasterData.vue → “운영 기준정보 > 하우스키핑 단위규칙”
# ============================================================================

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    UniqueConstraint,
)
from app.db.base_class import Base


class MasterHkUnitRule(Base):
    """하우스키핑 유닛 계산 규칙 마스터 (Housekeeping Unit Rule Master)"""

    __tablename__ = "master_hk_unit_rules"

    # ─────────────────────────────────────────────
    # 기본 필드
    # ─────────────────────────────────────────────
    id = Column(Integer, primary_key=True, index=True)
    condition_code = Column(
        String(30),
        unique=True,
        nullable=False,
        comment="조건 코드 (예: BASE, OCCUPIED, MOVED, VIP)",
    )
    description = Column(String(255), nullable=False, comment="조건 설명 (예: 기본 청소, 재실, 층 이동 등)")
    unit_value = Column(
        Float,
        default=1.0,
        nullable=False,
        comment="유닛 값 (가중치, 예: 1.0=기본, 0.3=재실)",
    )
    order_no = Column(
        Integer,
        default=0,
        nullable=False,
        comment="정렬 순서 (MasterTable 드래그용)",
    )
    is_active = Column(Boolean, default=True, nullable=False, comment="활성 여부")

    # ─────────────────────────────────────────────
    # 생성·갱신 정보
    # ─────────────────────────────────────────────
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="생성일시 (UTC)",
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="수정일시 (UTC)",
    )

    # ─────────────────────────────────────────────
    # 제약조건
    # ─────────────────────────────────────────────
    __table_args__ = (
        UniqueConstraint("condition_code", name="uq_hk_unit_rule_code"),
    )

    # ─────────────────────────────────────────────
    # 문자열 표현
    # ─────────────────────────────────────────────
    def __repr__(self) -> str:
        return f"<MasterHkUnitRule(code='{self.condition_code}', unit={self.unit_value}, order={self.order_no})>"


# ============================================================================
# ✅ EOF — app/models/master_hk_unit_rule.py (v1.2 · SSOT 완전판)
# ============================================================================
