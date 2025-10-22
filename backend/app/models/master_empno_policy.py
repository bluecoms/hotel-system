# -*- coding: utf-8 -*-
# version: 2025-10-18 v1.1 (Master EmpNoPolicy Model)
"""
Hotel Admin — Master EmpNoPolicy Model (사번 정책)
────────────────────────────────────────────
개선사항 (v1.1)
  ✅ Boolean server_default → text("1") 로 안전화
  ✅ updated_at 자동 갱신(onupdate)
────────────────────────────────────────────
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, text
from app.db.base_class import Base


class MasterEmpNoPolicy(Base):
    """
    사번 정책 테이블 정의
    ──────────────────────────────────────
    id             : 기본키 (PK)
    prefix         : 사번 접두어 (예: EMP, HK, FNB)
    start_no       : 시작 번호
    auto_increment : 자동증가 여부
    memo           : 메모
    updated_at     : 최종 수정일시 (자동 갱신)
    """
    __tablename__ = "empno_policy"

    id = Column(Integer, primary_key=True, index=True)
    prefix = Column(String(20), nullable=False, server_default="EMP")
    start_no = Column(Integer, nullable=False, server_default="1")
    auto_increment = Column(Boolean, nullable=False, server_default=text("1"))
    memo = Column(String(255), nullable=True)

    # 최종 수정일시 (INSERT/UPDATE 자동 기록)
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )
