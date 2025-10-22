# -*- coding: utf-8 -*-
# version: 2025-10-18 v1.2 (Master Salary Grades Schema — Final / Annual-Only + Alias)
"""
Hotel Admin — Master Salary Grades Schema
──────────────────────────────────────────────────────────────────────────────
PATH     : /api/master/salary-grades
PURPOSE  : 급여 등급(MasterSalaryGrade) 데이터의 입출력 검증 및 직렬화
STYLE    : Pydantic v2 (ConfigDict.from_attributes=True)

설계 배경
  • 계약 입력(UI)에서 '직급'을 선택하면, 해당 직급의 '연봉(세전)'을 기준으로
    월 급여가 자동 계산되도록 단순화한다.
  • 기준정보는 '연봉(annual_salary)' 단일 기준만 관리한다.
    (월급은 계약 생성 시 annual_salary/12 로 환산, 통화는 내부 KRW로 가정)

필드 명세 (표준)
  • code           : 등급 코드 (unique)
  • name           : 등급명 (예: 대표이사, 부장)
  • annual_salary  : 연봉(세전, KRW, 정수)
  • is_active      : 사용 여부
  • order_no       : 정렬 순서(드래그 정렬용)
  • created_at     : 생성 일시 (DB CURRENT_TIMESTAMP와 일치)

호환성(중요)
  • 과거 프런트가 'base_salary'라는 키로 연봉을 전송하던 호환을 위해
    입력 스키마(MasterSalaryGradeIn)에서는
    annual_salary 필드에 alias="base_salary"를 부여했다.
    즉, base_salary 또는 annual_salary 중 아무 키로 전송해도 수용된다.
──────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ─────────────────────────────────────────────────────────────
# 공통(표준) 필드 — '연봉' 단일 기준
#   ※ 출력/표준 용도로 사용. 입력은 별도의 In 스키마를 사용(아래 참조).
# ─────────────────────────────────────────────────────────────
class MasterSalaryGradeBase(BaseModel):
    """급여 등급 공통(표준) 필드 — annual_salary 단일 기준"""
    code: str = Field(..., description="등급 코드 (unique)")
    name: str = Field(..., description="등급명 (예: 대표이사, 부장, 과장 등)")
    annual_salary: Optional[int] = Field(0, description="연봉(세전, KRW)")
    is_active: Optional[bool] = Field(True, description="사용 여부 (True=사용)")
    order_no: Optional[int] = Field(0, description="정렬 순서(드래그 정렬용)")


# ─────────────────────────────────────────────────────────────
# 입력 스키마 (Create / Update)
#   • 과거 호환: base_salary → annual_salary 로 alias 처리
#   • populate_by_name=True 로 annual_salary 키도 직접 허용
# ─────────────────────────────────────────────────────────────
class MasterSalaryGradeIn(BaseModel):
    """신규 생성 및 수정 입력 스키마 (base_salary ↔ annual_salary 호환)"""
    code: str = Field(..., description="등급 코드 (unique)")
    name: str = Field(..., description="등급명 (예: 대표이사, 부장, 과장 등)")
    # 호환: base_salary(legacy) 로 들어와도 annual_salary로 수용
    annual_salary: Optional[int] = Field(
        0,
        alias="base_salary",
        description="연봉(세전, KRW) — legacy 'base_salary' 키도 허용"
    )
    is_active: Optional[bool] = Field(True, description="사용 여부 (True=사용)")
    order_no: Optional[int] = Field(0, description="정렬 순서(드래그 정렬용)")

    # Pydantic v2: alias/이름 모두 허용
    model_config = ConfigDict(populate_by_name=True)


# ─────────────────────────────────────────────────────────────
# 출력 스키마 (Response)
#   • ORM 객체 → Pydantic 직렬화 허용(from_attributes=True)
# ─────────────────────────────────────────────────────────────
class MasterSalaryGradeOut(MasterSalaryGradeBase):
    """조회/응답 스키마"""
    id: int = Field(..., description="PK")
    created_at: Optional[datetime] = Field(None, description="생성 일시")
    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────
# 정렬 재배치(Drag & Drop) 입력 스키마
# ─────────────────────────────────────────────────────────────
class MasterSalaryGradeReorderIn(BaseModel):
    """정렬 순서 변경 항목"""
    id: int = Field(..., description="급여 등급 ID")
    order_no: int = Field(..., description="정렬 순서(1..N)")


class MasterSalaryGradeReorderBody(BaseModel):
    """정렬 순서 변경 요청 바디"""
    items: List[MasterSalaryGradeReorderIn] = Field(
        default_factory=list,
        description="정렬 변경 항목 리스트"
    )
