# -*- coding: utf-8 -*-
# version: 2025-10-18 v2.3 (Master Ranks Model)
"""
Hotel Admin — Master Rank Model (직급 기준정보)
────────────────────────────────────────────
목적:
  • 호텔 인사/조직 관리용 "직급(Ranks)" 기준정보 테이블 정의
  • /api/master/ranks CRUD API와 직접 연동
  • 기존 master_ranks → ranks 로 통합 완료

특징:
  • code: 직급 코드 (예: AST, MGR, DIR)
  • name: 직급명 (예: 사원, 대리, 과장, 부장)
  • base_salary: 직급별 기본급 (원)
  • order_no: 정렬순번 (드래그 정렬 대응)
  • is_active: 사용 여부
  • created_at: 생성일시 (자동 기록)
────────────────────────────────────────────
연동:
  • 스키마: app/schemas/master_ranks.py (MasterRankIn/Out)
  • 라우터: app/routers/master_ranks.py (/api/master/ranks)
  • 프런트: src/services/master.ts (listRanks / createRank 등)
────────────────────────────────────────────
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, text
from app.db.base_class import Base


class MasterRank(Base):
    """
    마스터 직급 테이블 정의
    ──────────────────────────────────────
    id          : 기본키 (PK)
    code        : 직급 코드
    name        : 직급명
    base_salary : 기본급 (원)
    order_no    : 정렬 순서
    is_active   : 사용 여부
    created_at  : 생성일시
    """
    __tablename__ = "ranks"

    # 기본키 / 코드 / 명칭
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(120), nullable=False)

    # 추가 필드
    base_salary = Column(Integer, nullable=True, server_default="0")
    order_no = Column(Integer, nullable=True, server_default="0")

    # 상태 / 메타
    is_active = Column(Boolean, nullable=False, server_default="1")
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
