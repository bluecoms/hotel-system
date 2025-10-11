# app/datasets/schemas/fnb_items.py
# -*- coding: utf-8 -*-
# version: 2025-10-11 Phase 2 (schemas)

from pydantic import BaseModel, Field


class FnbItemsRow(BaseModel):
    """
    F&B Items (품목별 매출) 데이터 단위 행 스키마
    - 어댑터(fnb_items.py)에서 normalize/parse 후 표준화된 구조
    - item_code, category, qty, amount 포함
    """
    business_date: str = Field(..., description="업무 일자 (YYYY-MM-DD)")
    property_code: str = Field(..., description="호텔 코드 (예: MOP)")
    item_code: str = Field(..., description="품목 코드")
    category: str = Field("", description="카테고리 (선택)")
    qty: str = Field("0", description="수량 (문자열, 기본 0)")
    amount: str = Field(..., description="금액 (문자열, 어댑터에서 정규화됨)")

    class Config:
        from_attributes = True
        orm_mode = True
