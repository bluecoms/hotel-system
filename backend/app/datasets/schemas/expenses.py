# app/datasets/schemas/expenses.py
# -*- coding: utf-8 -*-
# version: 2025-10-11 Phase 2 (schemas)

from pydantic import BaseModel, Field


class ExpensesRow(BaseModel):
    """
    Expenses (지출 내역) 데이터 단위 행 스키마
    - 어댑터(expenses.py)에서 normalize/parse 후 표준화된 구조
    - amount는 문자열로 유지 (정규화는 어댑터에서 수행)
    """
    business_date: str = Field(..., description="업무 일자 (YYYY-MM-DD)")
    property_code: str = Field(..., description="호텔 코드 (예: MOP)")
    account_code: str = Field(..., description="계정 코드 (예: 5000, 5100 등)")
    amount: str = Field(..., description="금액 (문자열, 어댑터에서 정규화됨)")
    note: str = Field("", description="비고 (선택)")

    class Config:
        from_attributes = True
        orm_mode = True
