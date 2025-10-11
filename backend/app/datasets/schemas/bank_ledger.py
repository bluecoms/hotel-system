# app/datasets/schemas/bank_ledger.py
# -*- coding: utf-8 -*-
# version: 2025-10-11 Phase 2 (schemas)

from pydantic import BaseModel, Field


class BankLedgerRow(BaseModel):
    """
    Bank Ledger (입출금 장부) 데이터 단위 행 스키마
    - 어댑터(bank_ledger.py)에서 normalize/parse 후 표준화된 구조
    - direction은 in/out 중 하나
    - amount는 문자열로 유지 (정규화는 어댑터에서 수행)
    """
    business_date: str = Field(..., description="업무 일자 (YYYY-MM-DD)")
    property_code: str = Field(..., description="호텔 코드 (예: MOP)")
    txn_id: str = Field(..., description="거래 ID (없을 경우 라인 번호 기반 자동 생성)")
    account_no: str = Field("", description="계좌 번호 (선택)")
    direction: str = Field("in", description="입출 방향 (in/out)")
    amount: str = Field(..., description="금액 (문자열, 어댑터에서 정규화됨)")
    memo: str = Field("", description="비고 / 메모 (선택)")

    class Config:
        from_attributes = True
        orm_mode = True
