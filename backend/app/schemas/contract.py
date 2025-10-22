# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/schemas/contract.py
# Version   : 2025.10-24 Final Stable (v3.8 · DeptName Join / ListResp 정합)
# Purpose   : Hotel Admin — 직원 계약 관리 스키마 (EmployeeContract Schemas)
# ----------------------------------------------------------------------------
# 목적:
#   • EmployeeContract 모델(직원 계약) <-> API 요청/응답 구조 정의
#   • append-only 버저닝(version_no) / 최신 플래그(is_latest) 구조 지원
#   • Employee LEFT JOIN + MasterDepartment JOIN 결과(부서명 등) 대응
# ----------------------------------------------------------------------------
# 변경사항 (v3.8)
#   ✅ ContractOut: dept_name / title_name 추가 (JOIN 결과 표시용)
#   ✅ ContractOut: emp_no(표준) + employee_emp_no(과거 호환) 동시 지원
#   ✅ ContractOut: model_config.extra='allow' 로 Router 응답 확장 필드 허용
#   ✅ 목록 응답용 ContractListResp 추가 (ok/page/size/total/items) — 라우터 반환과 정합
# ----------------------------------------------------------------------------
# 연계 모듈:
#   • app/models/contract.py       — EmployeeContract 모델
#   • app/routers/contracts.py     — 계약 관리 라우터 (LEFT JOIN + Dept JOIN)
#   • app/models/master_departments.py — MasterDepartment (dept_name 소스)
#   • app/models/employee.py       — Employee(dept_code/title 등 소스)
# ============================================================================

from __future__ import annotations
from datetime import datetime, date
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# 1️⃣ 입력 스키마 (ContractIn)
# ----------------------------------------------------------------------------
#  • 신규 계약 생성 시 사용
#  • append-only 구조로, 수정 시에는 신규 버전으로 생성됨
# ============================================================================
class ContractIn(BaseModel):
    """신규 계약 생성 입력 스키마 (append-only)"""
    employee_id: int = Field(..., description="직원 ID (employees.id)")
    contract_type: str = Field("MONTHLY", description="계약 유형 (MONTHLY/HOURLY 등)")
    start_date: Optional[date] = Field(None, description="계약 시작일(YYYY-MM-DD)")
    end_date: Optional[date] = Field(None, description="계약 종료일(YYYY-MM-DD)")
    pay_type: Optional[str] = Field("MONTHLY", description="지급 유형 (MONTHLY/HOURLY)")
    salary: Optional[float] = Field(None, description="급여 금액 (원화 기준)")
    currency: Optional[str] = Field("KRW", description="통화 코드 (기본 KRW)")
    memo: Optional[str] = Field("", description="비고/메모")
    file_path: Optional[str] = Field("", description="계약서 파일 경로(선택)")
    contract_no: Optional[str] = Field("", description="계약 번호(선택)")
    meta: Optional[Any] = Field(None, description="계약서 스냅샷/양식 메타(JSON 직렬화 가능)")


# ============================================================================
# 2️⃣ 출력 스키마 (ContractOut)
# ----------------------------------------------------------------------------
#  • 단일 계약 레코드 반환용
#  • Employee/Department JOIN 결과(이름/사번/지점/부서명/직책명) 포함
#  • Router에서 반환하는 추가 필드가 있어도 수용하도록 extra='allow' 설정
# ============================================================================
class ContractOut(BaseModel):
    """계약 단일 응답 스키마 (LEFT JOIN + Dept JOIN 확장 포함)"""
    model_config = ConfigDict(from_attributes=True, extra='allow')

    # 기본 계약 필드
    id: Optional[int] = Field(None, description="계약 PK")
    employee_id: Optional[int] = Field(None, description="직원 ID")
    contract_type: Optional[str] = Field(None, description="계약 유형")
    start_date: Optional[date] = Field(None, description="계약 시작일")
    end_date: Optional[date] = Field(None, description="계약 종료일")
    pay_type: Optional[str] = Field(None, description="급여 유형")
    salary: Optional[float] = Field(None, description="급여 금액")
    currency: Optional[str] = Field("KRW", description="통화 코드")
    status: Optional[str] = Field("draft", description="계약 상태 (draft/active/terminated)")
    version_no: Optional[int] = Field(1, description="버전 번호 (append-only)")
    is_latest: Optional[bool] = Field(True, description="최신 버전 여부")
    file_path: Optional[str] = Field("", description="계약서 파일 경로")
    memo: Optional[str] = Field("", description="비고/메모")
    contract_no: Optional[str] = Field("", description="계약 번호")
    meta: Optional[Any] = Field(None, description="계약서 스냅샷 메타")
    created_at: Optional[datetime] = Field(None, description="생성 시각(UTC)")
    updated_at: Optional[datetime] = Field(None, description="수정 시각(UTC)")

    # ✅ LEFT JOIN 확장 필드 — 직원/지점/부서/직책 (표시용)
    employee_name: Optional[str] = Field(None, description="직원 이름 (JOIN)")
    # 표준 표기: emp_no / 과거 호환: employee_emp_no
    emp_no: Optional[str] = Field(None, description="직원 사번 (JOIN 표준 필드)")
    employee_emp_no: Optional[str] = Field(None, description="직원 사번 (과거 호환 필드)")
    property_code: Optional[str] = Field(None, description="지점 코드 (JOIN)")
    dept_name: Optional[str] = Field(None, description="부서명 (MasterDepartment JOIN)")
    title_name: Optional[str] = Field(None, description="직책명 (MasterTitle JOIN)")

    # 주의:
    #  • Employee 모델 자체에는 dept_name 컬럼이 존재하지 않음(SSOT 원칙).
    #  • 반드시 MasterDepartment JOIN 결과를 dept_name으로 매핑하여 사용.


# ============================================================================
# 3️⃣ 목록 응답 스키마 (ContractListResp)
# ----------------------------------------------------------------------------
#  • /api/contracts (목록조회) 라우터의 실제 반환과 정합
#  • ok/page/size/total + items 로 구성
# ============================================================================
class ContractListResp(BaseModel):
    """계약 목록 응답 스키마 (라우터 반환 구조와 정합)"""
    model_config = ConfigDict(extra='allow')  # 라우터에서 필드 확장해도 수용
    ok: bool = Field(True, description="성공 여부")
    items: List[ContractOut] = Field(default_factory=list, description="계약 목록")
    page: int = Field(1, description="현재 페이지")
    size: int = Field(20, description="페이지 크기")
    total: int = Field(0, description="총 계약 수")


# ============================================================================
# 4️⃣ 이력 스키마 (ContractHistoryOut)
# ----------------------------------------------------------------------------
#  • 특정 직원의 계약 이력 조회 (/history/{employee_id})
# ============================================================================
class ContractHistoryOut(BaseModel):
    """직원별 계약 이력 응답 스키마"""
    employee_id: int = Field(..., description="직원 ID")
    items: List[ContractOut] = Field(default_factory=list, description="계약 이력 목록")
    total: int = Field(0, description="총 이력 개수")
