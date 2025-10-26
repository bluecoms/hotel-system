# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/models/master_department.py
# Version   : 2025.10-31 · v1.2 (Fix Tablename · SSOT Final Stable)
# Purpose   : Hotel Admin — Master Department Model (부서 기준정보 + 팀장 매핑)
# ----------------------------------------------------------------------------
# 목적:
#   • 호텔 인사/운영 시스템의 부서(Departments) 기준정보 테이블 정의
#   • /api/master/departments CRUD API와 직접 연동
#   • ✅ 부서별 팀장(leader_emp_id) 지정 기능 추가 (employees.id FK)
# ----------------------------------------------------------------------------
# 주요 변경사항(v1.2)
#   ✅ __tablename__ 수정: departments (복수형, 실제 DB 테이블과 일치)
#   ✅ leader_emp_id 컬럼 추가 (employees.id 참조)
#   ✅ 팀장 지정 기능과 RoleAccess 연계 준비
#   ✅ 기존 필드 및 구조 변경 없음 (하위 호환 유지)
# ----------------------------------------------------------------------------
# Naming 규칙 (SSOT 고정)
#   • Model  : app/models/master_department.py     → 단수
#   • Schema : app/schemas/master_departments.py   → 복수
#   • Router : app/routers/master_departments.py   → 복수
# ----------------------------------------------------------------------------
# 관련 테이블:
#   • employees (팀장 지정 대상)
#   • role_access (부서별 권한 제어 연계)
# ============================================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, text
from app.db.base_class import Base


class MasterDepartment(Base):
    """
    부서 기준정보 테이블 정의
    ──────────────────────────────────────
    id              : 기본키 (PK)
    property_code   : 사업장 코드 (예: MOP)
    dept_code       : 부서 코드 (예: FR, HK, FB 등)
    dept_name       : 부서명 (예: 프런트, 하우스키핑)
    parent_code     : 상위 부서 코드
    leader_emp_id   : 팀장(직원) ID — employees.id FK
    is_active       : 활성 여부
    remarks         : 비고
    order_no        : 정렬 순서
    created_at      : 생성일시
    updated_at      : 수정일시
    """

    __tablename__ = "departments"  # ✅ 복수형으로 통일 (SSOT 표준)

    # ─────────────────────────────
    # 기본 식별자 / 코드 정보
    # ─────────────────────────────
    id = Column(Integer, primary_key=True, index=True)
    property_code = Column(String(10), nullable=False, server_default="MOP")
    dept_code = Column(String(50), nullable=False, unique=True, index=True)
    dept_name = Column(String(120), nullable=False)
    parent_code = Column(String(50), nullable=True)

    # ─────────────────────────────
    # 팀장 매핑 (신규)
    # ─────────────────────────────
    leader_emp_id = Column(
        Integer,
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        doc="팀장(직원) ID — employees.id FK",
    )

    # ─────────────────────────────
    # 상태 및 기타 정보
    # ─────────────────────────────
    remarks = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text("1"))
    order_no = Column(Integer, nullable=True, server_default="0")

    # ─────────────────────────────
    # 타임스탬프
    # ─────────────────────────────
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )

    def __repr__(self):
        return f"<MasterDepartment id={self.id} code={self.dept_code} name={self.dept_name}>"
