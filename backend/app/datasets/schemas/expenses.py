# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/datasets/schemas/expenses.py
# Version   : 2025.10-30 · v3.0 (SSOT Stable · Category/Pay Sync)
# Purpose   : Hotel Admin — Expenses Row Schema (지출내역 단일 행)
# ----------------------------------------------------------------------------
# 목적:
#   • 어댑터(expenses.py)에서 normalize/parse 후 반환되는 정규화 행 구조 정의
#   • 병합엔진(SSOT Merge Engine)에 전달되는 CanonRecord.payload와 일치
# ----------------------------------------------------------------------------
# 특징:
#   • account_code / category_code / pay_method 필드 포함
#   • note/memo 자동 통합
#   • 모든 코드 필드는 대문자 정규화
#   • amount는 문자열 유지 (숫자 변환은 어댑터에서 수행)
#   • Pydantic v2: model_config = ConfigDict(from_attributes=True)
# ============================================================================

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class ExpensesRow(BaseModel):
    """지출내역 단일 행 스키마 (정규화 완료 형태)"""
    business_date: str = Field(..., description="업무 일자 (YYYY-MM-DD)")
    property_code: str = Field(..., description="호텔 코드 (예: MOP)")
    account_code: str = Field(..., description="계정 코드 (예: 5000, 5100 등)")
    category_code: str = Field("", description="지출 카테고리 (예: OFFICE, SUPPLY 등)")
    pay_method: str = Field("", description="결제 수단 (CARD / CASH / TRANSFER / ETC)")
    amount: str = Field(..., description="금액 (문자열, 어댑터에서 정규화됨)")
    note: str = Field("", description="비고 / 메모 (선택)")

    # ✅ v2 스타일 설정
    model_config = ConfigDict(from_attributes=True)

    # ─────────────────────────────────────────────
    # 밸리데이터: 코드/결제수단 정규화
    # ─────────────────────────────────────────────
    @field_validator("property_code", "account_code", "category_code", mode="before")
    @classmethod
    def _upper_codes(cls, v: Optional[str]) -> str:
        return (v or "").strip().upper()

    @field_validator("pay_method", mode="before")
    @classmethod
    def _norm_pay(cls, v: Optional[str]) -> str:
        """결제수단 한글/약어 → 표준 코드 변환"""
        s = (v or "").strip().upper()
        if s in ("CARD", "CC", "신용카드", "카드"):
            return "CARD"
        if s in ("CASH", "현금"):
            return "CASH"
        if s in ("TRANSFER", "BANK", "계좌이체", "이체"):
            return "TRANSFER"
        if s in ("ETC", "기타", ""):
            return "ETC"
        return s
