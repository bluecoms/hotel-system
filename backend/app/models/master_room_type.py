# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/models/master_room_type.py
# Version   : 2025-11-09 · v1.2 (Add order_no · SSOT Final Stable)
# Purpose   : Hotel Admin — 객실 타입 기준정보 마스터
# ----------------------------------------------------------------------------
# 목적:
#   • 호텔 객실 유형(STD, DLX, STE 등)을 기준정보로 관리
#   • 하우스키핑, 예약, 매출 등 전 도메인 공통 참조
#   • 기본 유닛(unit_value) + 정렬 순서(order_no) 포함
# ----------------------------------------------------------------------------
# 설계 원칙:
#   ✅ 단일 소스(SSOT) — 중복 정의 금지
#   ✅ UTC 타임스탬프 사용
#   ✅ Alembic autogen 호환성 보장
# ----------------------------------------------------------------------------
# 연계:
#   • schemas.master_room_type
#   • routers.master_room_type
#   • housekeeping_service / closing 모듈 참조
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


class MasterRoomType(Base):
    """객실 타입 기준정보 (Room Type Master)"""

    __tablename__ = "master_room_types"

    # ─────────────────────────────────────────────
    # 기본 필드
    # ─────────────────────────────────────────────
    id = Column(Integer, primary_key=True, index=True)
    code = Column(
        String(20),
        unique=True,
        nullable=False,
        comment="객실 타입 코드 (예: STD, DLX, SUITE)",
    )
    name = Column(String(100), nullable=False, comment="객실 타입명 (예: 스탠다드, 디럭스)")
    unit_value = Column(
        Float,
        nullable=False,
        default=1.0,
        comment="하우스키핑 기준 유닛값 (예: 기본=1.0)",
    )
    description = Column(String(255), nullable=True, comment="설명 또는 비고")
    is_active = Column(Boolean, default=True, nullable=False, comment="활성 여부")
    order_no = Column(Integer, default=0, nullable=False, comment="정렬 순서")  # ✅ 추가됨

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
        UniqueConstraint("code", name="uq_master_room_type_code"),
    )

    # ─────────────────────────────────────────────
    # 문자열 표현
    # ─────────────────────────────────────────────
    def __repr__(self) -> str:
        return f"<MasterRoomType(code='{self.code}', order_no={self.order_no}, unit={self.unit_value})>"


# ============================================================================
# ✅ EOF — app/models/master_room_type.py (v1.2 · SSOT Final Stable)
# ============================================================================
