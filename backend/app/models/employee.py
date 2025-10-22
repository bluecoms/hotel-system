# ============================================================================
# File      : app/models/employee.py
# Version   : 2025.10-22 v3.5 (Final Stable / HR Employees Model — Property & Contract Sync)
# Purpose   : Hotel Admin — HR Employees Model (SQLAlchemy ORM)
# ----------------------------------------------------------------------------
# 목적:
#   • 직원(사원) 기본 정보 및 사용자 매핑(UserEmployeeMap) 테이블 정의
#   • 각 직원은 반드시 Property(호텔 코드)에 종속 (property_code)
#   • 계약(EmployeeContract)과 양방향 관계(back_populates) 연결
#   • 개인정보 및 급여계좌는 반드시 ‘마스킹된 값’만 저장 (원문 금지)
# ----------------------------------------------------------------------------
# 설계 원칙:
#   • SoftDeleteMixin 적용 → deleted_at 기반 안전 삭제
#   • emp_no(사번) 유니크 인덱스, 검색 효율 최적화
#   • created_at / updated_at UTC 기준 자동 갱신
#   • property_code 로 모든 하위 도메인(계약·급여·근태 등) 연계
# ----------------------------------------------------------------------------
# 보안 정책:
#   ⚠ 주민등록번호, 계좌번호 원문 절대 금지
#   ⚙ rrn_mask, account_mask, account_last4 만 저장
#   ⚙ bank_name 은 급여계좌 은행명만 저장 (예: 신한, 국민)
# ----------------------------------------------------------------------------
# 관계 정의:
#   ✅ user_map   : UserEmployeeMap (1:1)
#   ✅ contracts  : EmployeeContract (1:N)
# ============================================================================

from __future__ import annotations
from datetime import datetime, date
from typing import Optional, TYPE_CHECKING, List

from sqlalchemy import (
    Integer, String, UniqueConstraint, ForeignKey,
    Date, DateTime, Text
)
from sqlalchemy.orm import (
    Mapped, mapped_column, relationship
)

from app.db.base_class import Base
from app.models.mixins import SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.contract import EmployeeContract


# ============================================================================
# 직원(사원) 기본정보 테이블
# ============================================================================
class Employee(Base, SoftDeleteMixin):
    """직원(사원) 기본 정보 테이블"""

    __tablename__ = "employees"

    # ─────────────────────────────
    # 기본 식별자
    # ─────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, doc="직원 PK")
    emp_no: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False, doc="사번(유니크)"
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False, doc="성명")

    # ✅ 프로퍼티 코드 (지점/호텔)
    property_code: Mapped[str] = mapped_column(
        String(10), index=True, nullable=False, default="MOP",
        doc="소속 호텔 코드 (예: MOP, ICN 등)"
    )

    # ─────────────────────────────
    # 조직 / 직무 계층
    # ─────────────────────────────
    dept: Mapped[str] = mapped_column(String(120), default="", nullable=False, doc="부서명 또는 코드 (예: 관리팀)")
    title: Mapped[str] = mapped_column(String(120), default="", nullable=False, doc="직책 (예: 팀장, 매니저)")
    position: Mapped[str] = mapped_column(String(80), default="", nullable=False, doc="직위 (예: 과장, 대리)")
    rank: Mapped[str] = mapped_column(String(80), default="", nullable=False, doc="직급 (예: 4급, 5급 등)")

    # ─────────────────────────────
    # 연락 / 개인정보
    # ─────────────────────────────
    phone: Mapped[str] = mapped_column(String(40), default="", nullable=False, doc="연락처")
    email: Mapped[str] = mapped_column(String(120), default="", nullable=False, doc="이메일")
    address: Mapped[str] = mapped_column(String(255), default="", nullable=False, doc="주소")

    # ─────────────────────────────
    # 고용정보
    # ─────────────────────────────
    hire_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, doc="입사일")
    leave_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, doc="퇴사일")
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, doc="생년월일 (선택 저장)")

    # ─────────────────────────────
    # 민감정보 (마스킹 저장 전용)
    # ─────────────────────────────
    rrn_mask: Mapped[str] = mapped_column(String(20), default="", nullable=False, doc="주민등록번호 마스킹")
    bank_name: Mapped[str] = mapped_column(String(60), default="", nullable=False, doc="급여계좌 은행명")
    account_mask: Mapped[str] = mapped_column(String(60), default="", nullable=False, doc="급여계좌번호 마스킹")
    account_last4: Mapped[str] = mapped_column(String(8), default="", nullable=False, doc="급여계좌 끝 4자리")

    # ─────────────────────────────
    # 기타 / 계약 상태
    # ─────────────────────────────
    memo: Mapped[str] = mapped_column(Text, default="", nullable=False, doc="비고 / 참고 메모")
    contract_status: Mapped[str] = mapped_column(String(20), default="", nullable=False, doc="계약 상태")
    contract_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True, doc="현재 계약 시작일")
    contract_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True, doc="현재 계약 종료일")

    # ─────────────────────────────
    # 타임스탬프
    # ─────────────────────────────
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, doc="생성 시각(UTC)")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, doc="수정 시각(UTC)"
    )

    # ─────────────────────────────
    # 관계 정의
    # ─────────────────────────────
    # 1:1 사용자 매핑
    user_map: Mapped["UserEmployeeMap"] = relationship(
        "UserEmployeeMap",
        back_populates="employee",
        cascade="all, delete-orphan",
        uselist=False,
    )

    # ✅ 1:N 계약(EmployeeContract)
    contracts: Mapped[List["EmployeeContract"]] = relationship(
        "EmployeeContract",
        back_populates="employee",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # ─────────────────────────────
    # 문자열 표현
    # ─────────────────────────────
    def __repr__(self) -> str:
        return (
            f"<Employee(id={self.id}, property='{self.property_code}', emp_no='{self.emp_no}', "
            f"name='{self.name}', dept='{self.dept}', title='{self.title}', bank='{self.bank_name}')>"
        )


# ============================================================================
# 사용자 ↔ 직원 매핑 테이블
# ============================================================================
class UserEmployeeMap(Base):
    """로그인 사용자(users) ↔ 직원(employees) 연결 테이블"""

    __tablename__ = "user_employee_map"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", name="uq_user_single_map"),)

    employee: Mapped["Employee"] = relationship("Employee", back_populates="user_map")

    def __repr__(self) -> str:
        return f"<UserEmployeeMap user_id={self.user_id}, employee_id={self.employee_id}>"
