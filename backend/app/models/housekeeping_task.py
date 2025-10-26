# -*- coding: utf-8 -*-
# =============================================================================
# File      : app/models/housekeeping_task.py
# Version   : 2025-10-31 · v2 (DeptAccess Unified · Employee FK 적용)
# Purpose   : Housekeeping Task ORM (객실 단위 작업 기록)
# -----------------------------------------------------------------------------
# 목적:
#   • 하우스키핑 일자별 객실 작업(청소/점검/상태변경) 기록을 저장
#   • 기존 Employee / DeptAccess 체계와 직접 연동
#   • 객실별 작업상태·담당자·유닛가중치 등을 관리
# -----------------------------------------------------------------------------
# 변경 사항 (v2):
#   ✅ staff_name 필드 제거 → employee_id(FK) + department_code 로 통합
#   ✅ DeptAccess 코드(HK 등)로 필터링 가능
#   ✅ ORM-level index 및 timestamp 기본값 정비
# -----------------------------------------------------------------------------
# 주의:
#   • Python 3.8 호환 (typing.Optional / datetime.utcnow 기본)
#   • Alembic 단일 head 정책 가정
#   • models/__init__.py 에 명시 등록되어야 자동 export 됨
# =============================================================================

from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Index,
)
from app.db.base_class import Base  # 프로젝트 공통 Base (단일 소스)


class HousekeepingTask(Base):
    __tablename__ = "housekeeping_tasks"

    # 기본 키
    id = Column(Integer, primary_key=True, index=True)

    # 업무 기본 정보
    business_date = Column(String, nullable=False, index=True)   # YYYY-MM-DD
    property_code = Column(String, nullable=False, index=True)
    room_no = Column(String, nullable=False, index=True)

    # 상태 변화
    status_before = Column(String, nullable=True)
    status_after = Column(String, nullable=True)

    # 담당자 / 부서
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    department_code = Column(String, nullable=True)  # 예: HK, FNB 등
    memo = Column(String, nullable=True)

    # 유닛(작업 가중치): 객실=1.0, 재실=0.3, 층이동=0.2 등
    units = Column(Float, nullable=False, default=1.0)

    # 완료 시각(없으면 미완료로 간주)
    completed_at = Column(DateTime, nullable=True)

    # 생성/수정 시각
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index(
            "ix_hk_task_date_prop_room",
            "business_date",
            "property_code",
            "room_no",
        ),
    )

    # ──────────────────────────────────────────────
    # 유틸 메서드
    # ──────────────────────────────────────────────
    def mark_completed(self) -> None:
        """작업 완료시각 업데이트"""
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
