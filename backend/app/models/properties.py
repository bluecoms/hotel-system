# ============================================================================
# File      : app/models/property.py
# Version   : 2025.10-31 v1.1 (Stable · extend_existing Fix)
# Purpose   : Hotel Admin — Property(지점) 마스터 모델 (SQLAlchemy ORM)
# ----------------------------------------------------------------------------
# 목적:
#   • 호텔 지점(Property) 기본 정보 저장
#   • 직원(Employee), 계약(Contract), 업로드 등 주요 도메인의 상위 식별자 역할
# ----------------------------------------------------------------------------
# 설계 원칙:
#   • code(PK) 는 문자열 기반 (예: MOP, SEO, BUS 등)
#   • name 은 사람이 읽을 수 있는 호텔명
#   • is_active 는 활성 여부
#   • created_at / updated_at 은 UTC 기준 자동 기록
# ----------------------------------------------------------------------------
# 연관 테이블:
#   • employees.property_code (FK)
#   • contracts.property_code (FK)
# ----------------------------------------------------------------------------
# Note:
#   • 기본 지점은 Mokpo Ocean Hotel (code='MOP')
#   • 데이터는 마스터 테이블로 관리되며 프런트 Property Selector 에 노출됨
# ----------------------------------------------------------------------------
# 추가 설명 (v1.1):
#   ✅ Alembic/AutoLoader 중복 로드 시 "Table 'properties' is already defined" 경고 방지
#   ✅ __table_args__ = {'extend_existing': True} 지정 → 동일 Base.metadata 내 재등록 허용
#   ✅ DB 스키마나 데이터에 영향 없음 (경고만 억제)
# ============================================================================
from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base


class Property(Base):
    """호텔 지점(Property) 마스터"""

    __tablename__ = "properties"
    __table_args__ = {"extend_existing": True}  # ✅ 중복 테이블 정의 허용 (경고 억제)

    # ─────────────────────────────
    # 기본 컬럼
    # ─────────────────────────────
    code: Mapped[str] = mapped_column(
        String(10),
        primary_key=True,
        doc="지점 코드 (예: MOP)",
    )
    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        doc="지점명 (예: Mokpo Ocean Hotel)",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="활성 여부",
    )

    # ─────────────────────────────
    # 타임스탬프
    # ─────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        doc="생성일시(UTC)",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        doc="수정일시(UTC)",
    )

    # ─────────────────────────────
    # 표현식 (디버깅용)
    # ─────────────────────────────
    def __repr__(self) -> str:
        return f"<Property(code='{self.code}', name='{self.name}', active={self.is_active})>"
