# app/schemas/common.py
from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from datetime import datetime, date
from typing import Optional, Union, Literal, List, Dict

# -----------------------------
# Users / Auth
# -----------------------------
class ApproveBody(BaseModel):
    is_active: bool


class UserCreate(BaseModel):
    email: str
    name: str
    is_active: bool = True


class CreateFromEmpIn(BaseModel):
    """사원명부를 기준으로 앱 계정 생성할 때 사용"""
    emp_no: str
    email: str
    name: Optional[str] = None
    is_active: bool = True


# -----------------------------
# Employees (사원명부)
# -----------------------------
class EmployeeIn(BaseModel):
    """
    사원 생성/임포트 기본 입력 스키마 (간단 버전)
    - 주민번호/계좌는 '마스킹' 값만 저장 (원문 금지)
    """
    emp_no: str
    name: str

    dept: Optional[str] = ""
    title: Optional[str] = ""      # 직책
    position: Optional[str] = ""   # 직위
    phone: Optional[str] = ""
    email: Optional[str] = ""
    address: Optional[str] = ""

    hire_date: Optional[date] = None
    leave_date: Optional[date] = None

    # 민감정보(마스킹만 저장)
    rrn_mask: Optional[str] = ""       # 예: "801125-1**" 등 (원문 금지)
    bank_name: Optional[str] = ""      # 예: "농협", "국민"
    account_mask: Optional[str] = ""   # 예: "***-***-1234" (원문 금지)
    account_last4: Optional[str] = ""  # 검색/대조용

    memo: Optional[str] = ""


# 목록 응답(가벼움)
class EmployeeListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    emp_no: str
    name: str
    dept: str
    title: str


# 상세 응답/HR 카드(무거움)
class EmployeeDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    emp_no: str
    name: str

    dept: str
    title: str        # 직책
    position: str     # 직위
    rank: str = ""  # 추후 확장 대비(모델에 존재하면 그대로 매핑)

    phone: str
    email: str
    address: str

    hire_date: Optional[date] = None
    leave_date: Optional[date] = None

    rrn_mask: str
    bank_name: str
    account_mask: str
    account_last4: str

    memo: str


# 부분 수정(패치) — HR 카드 저장 시 사용
class EmployeeUpdate(BaseModel):
    name: Optional[str] = None

    dept: Optional[str] = None
    title: Optional[str] = None
    position: Optional[str] = None
    rank: Optional[str] = None

    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

    hire_date: Optional[date] = None
    leave_date: Optional[date] = None

    rrn_mask: Optional[str] = None           # 원문 금지(마스킹만)
    bank_name: Optional[str] = None
    account_mask: Optional[str] = None       # 원문 금지(마스킹만)
    account_last4: Optional[str] = None

    memo: Optional[str] = None


# -----------------------------
# Closing / Upload / Keywords
# -----------------------------
class DayStatusBody(BaseModel):
    date: str
    property_code: str = "MOP"
    status: Literal["OPEN", "CLOSED"]


class RestoreBody(BaseModel):
    dataset: str
    business_date: str
    property_code: str = "MOP"
    version_no: int


class KeywordIn(BaseModel):
    group_name: str
    k: str
    v: str = ""
    weight: int = 0
    is_active: bool = True


class KeywordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    group_name: str
    k: str
    v: str
    weight: int
    is_active: bool
    created_at: datetime
