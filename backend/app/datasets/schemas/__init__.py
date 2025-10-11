# app/datasets/schemas/__init__.py
# -*- coding: utf-8 -*-
# version: 2025-10-11 Phase 2 (datasets schemas)
"""
Dataset Schema 통합 초기화 (__init__.py)
──────────────────────────────────────────────
- 각 데이터셋의 입력/정규화/머지 스키마를 일관 구조로 통합
- 상위 레벨 import 시 자동 노출 (예: from app.datasets.schemas import SalesFrontSchema)
- 공통 필드는 BaseDatasetSchema에 정의
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# 공통 베이스 스키마
# ─────────────────────────────────────────────
class BaseDatasetSchema(BaseModel):
    business_date: str = Field(..., description="업무 일자 (YYYY-MM-DD)")
    property_code: str = Field(..., description="호텔 코드 (예: MOP)")

    class Config:
        orm_mode = True
        from_attributes = True


# ─────────────────────────────────────────────
# RoomsStatus 스키마
# ─────────────────────────────────────────────
class RoomsStatusSchema(BaseDatasetSchema):
    room_no: str = Field(..., description="객실 번호")
    status: str = Field(..., description="상태 (VACANT / OCCUPIED 등)")
    note: Optional[str] = Field("", description="비고")


# ─────────────────────────────────────────────
# SalesFront 스키마
# ─────────────────────────────────────────────
class SalesFrontSchema(BaseDatasetSchema):
    tag: str = Field(..., description="매출 구분 태그 (예: ROOM_ONLY, BREAKFAST 등)")
    amount: str = Field(..., description="금액 (문자열, 어댑터에서 정규화됨)")


# ─────────────────────────────────────────────
# Expenses 스키마
# ─────────────────────────────────────────────
class ExpensesSchema(BaseDatasetSchema):
    account_code: str = Field(..., description="계정 코드")
    amount: str = Field(..., description="금액 (문자열)")
    note: Optional[str] = Field("", description="비고")


# ─────────────────────────────────────────────
# BankLedger 스키마
# ─────────────────────────────────────────────
class BankLedgerSchema(BaseDatasetSchema):
    txn_id: str = Field(..., description="거래 ID (없을 경우 행 번호로 대체)")
    account_no: str = Field("", description="계좌 번호")
    direction: str = Field("in", description="입출 방향 (in/out)")
    amount: str = Field(..., description="금액 (문자열, 어댑터에서 정규화됨)")
    memo: Optional[str] = Field("", description="메모")


# ─────────────────────────────────────────────
# export 목록
# ─────────────────────────────────────────────
__all__ = [
    "BaseDatasetSchema",
    "RoomsStatusSchema",
    "SalesFrontSchema",
    "ExpensesSchema",
    "BankLedgerSchema",
]
