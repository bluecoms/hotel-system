# -*- coding: utf-8 -*-
# version: 2025-10-18 v1.1 (Master Salary Grades Model — Final)
"""
Hotel Admin — Master Salary Grades Model
────────────────────────────────────────────
목적:
  • 호텔 인사관리 및 급여정책의 기준 “급여 등급(Salary Grades)” 정의 테이블
  • 직급(Master Ranks)과는 별도로, 연봉·기본급 기준 구간을 관리
────────────────────────────────────────────
필드 구성:
  id           : PK
  code         : 등급 코드 (고유)
  name         : 등급명 (예: 대표이사, 부장, 과장 등)
  master_salary_grades  : 기본급 (정수, 단위 KRW)
  is_active    : 사용 여부 (1=사용, 0=비활성)
  order_no     : 정렬 순서 (프런트 Drag 정렬용)
  created_at   : 생성 일시 (자동기록)
────────────────────────────────────────────
연동:
  • 스키마 : app/schemas/master_salary_grade.py (MasterSalaryGradeIn/Out)
  • 라우터 : app/routers/master_salary_grade.py (/api/master/salary-grades)
  • 프런트 : src/services/master.ts (급여등급 관리 화면)
────────────────────────────────────────────
"""

from __future__ import annotations
from datetime import datetime
from sqlalchemy import (
    Integer,
    String,
    Boolean,
    DateTime,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base_class import Base


class MasterSalaryGrade(Base):
    """
    마스터 급여 등급 테이블 정의
    ──────────────────────────────────────
    인사관리(HR)에서 직급별 급여 정책을 관리하기 위한
    기준정보 테이블. 각 등급별 연봉, 정렬순서, 활성 여부 등을 관리한다.
    """

    __tablename__ = "master_salary_grades"

    # ──────────────────────────────────────
    # 주요 컬럼
    # ──────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="등급 코드 (unique)"
    )
    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        doc="등급명 (예: 대표이사, 부장, 과장 등)"
    )

    # ──────────────────────────────────────
    # 급여 관련 — annual_salary 단일 기준
    # ──────────────────────────────────────
    annual_salary: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="연봉 (세전, 단위: 원, KRW)"
    )

    # ──────────────────────────────────────
    # 상태 / 정렬
    # ──────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="활성 여부 (True=사용)"
    )
    order_no: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="정렬 순서 (드래그 정렬용)"
    )

    # ──────────────────────────────────────
    # 메타
    # ──────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        doc="생성 일시 (UTC)"
    )