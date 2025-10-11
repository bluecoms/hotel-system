# app/datasets/schemas/fnb_tenders.py
# -*- coding: utf-8 -*-
# version: 2025-10-11 Phase 2 (schemas)

from pydantic import BaseModel, Field


class FnbTendersRow(BaseModel):
    """
    F&B Tenders (결제수단별 매출) 데이터 단위 행 스키마
    - 어댑터(fnb_tenders.py)에서 normalize/parse 후 표준화된 구조
    - tender_code: 현금, 카드, 룸차지 등
    """
    business_date: str = Field(..., description="업무 일자 (YYYY-MM-DD)")
    property_code: str = Field(..., description="호텔 코드 (예: MOP)")
    tender_code: str = Field(..., description="결제수단 코드 (예: CASH, CARD, ROOM)")
    amount: str = Field(..., description="금액 (문자열, 어댑터에서 정규화됨)")
    count: str = Field("0", description="건수 (문자열, 기본 0)")

    class Config:
        from_attributes = True
        orm_mode = True
