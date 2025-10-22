# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/datasets/schemas/__init__.py
# Version   : 2025.10-30 · v3.3 (SSOT Stable Final · Dataset Schemas Unified)
# Purpose   : Hotel Admin — Dataset Schemas (Rooms/Sales/Expenses/Bank)
# ----------------------------------------------------------------------------
# 목적:
#   • 각 데이터셋의 정규화·파싱 후 구조를 SSOT 기준으로 통합 정의
#   • 어댑터(adapters/*)와 병합엔진(engine.py) 간 일관된 payload 구조 유지
# ----------------------------------------------------------------------------
# 구성:
#   • BaseDatasetSchema   : 공통 필드 (business_date / property_code)
#   • RoomsStatusSchema   : 객실상태
#   • SalesFrontSchema    : 전면매출
#   • ExpensesSchema      : 지출내역
#   • BankLedgerSchema    : 입출금장부
# ----------------------------------------------------------------------------
# 특징:
#   • Pydantic v2 기반 (ConfigDict from_attributes=True)
#   • 대문자 정규화 및 문자열 기반 금액 유지
#   • 모든 스키마는 CanonRecord.payload와 동일한 필드셋
# ============================================================================
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

# ============================================================================
# 1️⃣ 공통 베이스 스키마
# ----------------------------------------------------------------------------
class BaseDatasetSchema(BaseModel):
    """모든 데이터셋의 공통 기본 필드"""
    business_date: str = Field(..., description="업무 일자 (YYYY-MM-DD)")
    property_code: str = Field(..., description="호텔 코드 (예: MOP)")

    model_config = ConfigDict(from_attributes=True)

    @field_validator("property_code", mode="before")
    @classmethod
    def _upper_pc(cls, v: Optional[str]) -> str:
        return (v or "").strip().upper()

# ============================================================================
# 2️⃣ RoomsStatus 스키마
# ----------------------------------------------------------------------------
class RoomsStatusSchema(BaseDatasetSchema):
    """객실 상태 데이터"""
    room_no: str = Field(..., description="객실 번호")
    status: str = Field(..., description="상태 (CLEAN / DIRTY / OOO 등)")
    note: str = Field("", description="비고")

# ============================================================================
# 3️⃣ SalesFront 스키마
# ----------------------------------------------------------------------------
class SalesFrontSchema(BaseDatasetSchema):
    """전면 매출 데이터"""
    tag: str = Field(..., description="매출 구분 태그 (예: ROOM_ONLY, BREAKFAST 등)")
    amount: str = Field(..., description="금액 (문자열, 어댑터에서 정규화됨)")

# ============================================================================
# 4️⃣ Expenses 스키마
# ----------------------------------------------------------------------------
class ExpensesSchema(BaseDatasetSchema):
    """지출 내역 데이터"""
    account_code: str = Field(..., description="계정 코드 (예: 5000, 5100 등)")
    category_code: str = Field("", description="지출 카테고리 (예: OFFICE, SUPPLY 등)")
    pay_method: str = Field("", description="결제 수단 (CARD / CASH / TRANSFER / ETC)")
    amount: str = Field(..., description="금액 (문자열, 어댑터에서 정규화됨)")
    note: str = Field("", description="비고 / 메모")

    @field_validator("account_code", "category_code", mode="before")
    @classmethod
    def _upper_codes(cls, v: Optional[str]) -> str:
        return (v or "").strip().upper()

# ============================================================================
# 5️⃣ BankLedger 스키마
# ----------------------------------------------------------------------------
class BankLedgerSchema(BaseDatasetSchema):
    """입출금 장부 데이터"""
    txn_id: str = Field(..., description="거래 ID (없을 경우 어댑터에서 자동 생성)")
    bank_code: str = Field("", description="은행 코드 (예: KB, NH, WR 등)")
    account_no: str = Field("", description="계좌 번호 (선택)")
    direction: str = Field("IN", description="입출 방향 (IN/OUT)")
    amount: str = Field(..., description="금액 (문자열, 어댑터에서 정규화됨)")
    memo: str = Field("", description="비고 / 메모 (선택)")
    txn_ref: str = Field("", description="거래 참조번호 (선택)")

    @field_validator("bank_code", mode="before")
    @classmethod
    def _upper_bank(cls, v: Optional[str]) -> str:
        return (v or "").strip().upper()

    @field_validator("direction", mode="before")
    @classmethod
    def _norm_dir(cls, v: Optional[str]) -> str:
        s = (v or "").strip().lower()
        if s in ("in", "deposit", "credit", "cr", "+", "입금", "유입"):
            return "IN"
        if s in ("out", "withdraw", "debit", "dr", "-", "출금", "지출"):
            return "OUT"
        return "IN"

# ============================================================================
# 6️⃣ export 목록
# ----------------------------------------------------------------------------
__all__ = [
    "BaseDatasetSchema",
    "RoomsStatusSchema",
    "SalesFrontSchema",
    "ExpensesSchema",
    "BankLedgerSchema",
]
