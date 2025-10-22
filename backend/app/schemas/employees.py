# ============================================================================
# File      : app/schemas/employees.py
# Version   : 2025.10-22 v3.6 (Final Stable / HR Employees Schema · Property Sync)
# Purpose   : Hotel Admin — HR Employees Schemas (Pydantic v2)
# ----------------------------------------------------------------------------
# 목적:
#   • 직원(사원) 도메인의 요청/응답 스키마 정의
#   • DB 모델(app/models/employee.py v3.4)과 1:1 대응 (property_code 포함)
#   • API 입출력 시 불필요/민감 정보 최소화(마스킹 필드만 노출)
# ----------------------------------------------------------------------------
# 설계 원칙:
#   • Pydantic v2 ConfigDict(from_attributes=True) 사용 (ORM → 스키마 자동 매핑)
#   • API 전용 스키마(ORM Base와 분리), extra="ignore" 로 안전한 확장
#   • 주민번호·계좌번호 ‘원문’ 절대 금지 → rrn_mask/account_mask/account_last4 만 허용
#   • UI 단에서는 계약 상태 및 기간(시작/종료)을 직접 노출(읽기 전용)
# ----------------------------------------------------------------------------
# 보안 정책:
#   ⚠ 주민등록번호, 계좌번호 원문 저장/노출 금지
#   ⚙ rrn_mask / account_mask / account_last4 / bank_name 만 허용
#   ⚙ birth_date 및 property_code 는 선택 입력 가능 (계약서/인사기록용)
# ============================================================================

from __future__ import annotations
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# IN: 생성용 (POST body)
# ============================================================================
class EmployeeIn(BaseModel):
    """신규 직원 등록 입력 스키마"""
    model_config = ConfigDict(extra="ignore")

    # 기본 인적사항
    emp_no: str = Field(..., description="사번 (자동생성 또는 수동입력)")
    name: str = Field(..., description="성명")

    # ✅ 프로퍼티 코드
    property_code: str = Field(..., description="지점 코드 (예: MOP)")

    # 조직정보
    dept: Optional[str] = Field("", description="부서 코드/명")
    title: Optional[str] = Field("", description="직책 코드/명")
    position: Optional[str] = Field("", description="직위(선택)")
    rank: Optional[str] = Field("", description="직급(선택)")

    # 연락정보
    phone: Optional[str] = Field("", description="연락처")
    email: Optional[str] = Field("", description="이메일")
    address: Optional[str] = Field("", description="주소")

    # 고용정보
    hire_date: Optional[date] = Field(None, description="입사일")
    leave_date: Optional[date] = Field(None, description="퇴사일(재직중이면 None)")
    birth_date: Optional[date] = Field(None, description="생년월일 (선택)")

    # 민감정보 (마스킹 전용)
    rrn_mask: Optional[str] = Field("", description="주민등록번호 마스킹 (예: 900101-1******)")
    bank_name: Optional[str] = Field("", description="급여계좌 은행명")
    account_mask: Optional[str] = Field("", description="급여계좌 전체번호 (예: 110-***-****1234)")
    account_last4: Optional[str] = Field("", description="급여계좌 끝 4자리")
    memo: Optional[str] = Field("", description="비고 / 참고 메모")


# ============================================================================
# OUT: 목록용 (간략 정보)
# ============================================================================
class EmployeeListOut(BaseModel):
    """직원 목록 조회 스키마"""
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: int
    emp_no: str
    name: str
    property_code: str
    dept: str = ""
    title: str = ""
    title_name: Optional[str] = None
    dept_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    hire_date: Optional[date] = None
    leave_date: Optional[date] = None

    # 계약 필드(읽기 전용)
    contract_status: Optional[str] = None
    contract_start: Optional[date] = None
    contract_end: Optional[date] = None


# ============================================================================
# OUT: 상세용 (프로필/계약서 표시용)
# ============================================================================
class EmployeeDetailOut(BaseModel):
    """직원 상세 정보 스키마"""
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: int
    emp_no: str
    name: str
    property_code: str
    dept: str
    title: str
    position: str = ""
    rank: str = ""
    title_name: Optional[str] = None
    dept_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    birth_date: Optional[date] = None
    hire_date: Optional[date] = None
    leave_date: Optional[date] = None

    rrn_mask: Optional[str] = None
    bank_name: Optional[str] = None
    account_mask: Optional[str] = None
    account_last4: Optional[str] = None

    # 계약(읽기 전용)
    contract_status: Optional[str] = None
    contract_start: Optional[date] = None
    contract_end: Optional[date] = None

    memo: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


# ============================================================================
# IN: 수정용 (PUT / PATCH body)
# ============================================================================
class EmployeeUpdate(BaseModel):
    """직원 정보 수정 입력 스키마 (부분 갱신)"""
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    property_code: Optional[str] = None
    dept: Optional[str] = None
    title: Optional[str] = None
    position: Optional[str] = None
    rank: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    hire_date: Optional[date] = None
    leave_date: Optional[date] = None
    birth_date: Optional[date] = None
    rrn_mask: Optional[str] = None
    bank_name: Optional[str] = None
    account_mask: Optional[str] = None
    account_last4: Optional[str] = None
    memo: Optional[str] = None
