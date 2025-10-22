# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/datasets/schemas/bank_ledger.py
# Version   : 2025.10-30 · v3.0 (SSOT Stable · Banking Ready)
# Purpose   : Hotel Admin — Bank Ledger Row Schema (정규화 후 단일 행)
# ----------------------------------------------------------------------------
# 목적:
#   • 어댑터(bank_ledger.py)에서 normalize/parse 후 반환되는 표준 행 스키마
#   • 병합 엔진(SSOT Merge Engine)에 전달되는 CanonRecord.payload 구조와 일치
# ----------------------------------------------------------------------------
# 특징:
#   • direction → "IN"/"OUT" 사용 (소문자·한글·부호 입력도 허용, 자동 상향)
#   • bank_code / account_no / txn_ref 포함 (MasterBank/계좌 연동 대비)
#   • amount 는 문자열 유지 (숫자 변환/부호 처리/콤마 제거는 어댑터 단계에서 수행)
#   • Pydantic v2: model_config = ConfigDict(from_attributes=True)
# ============================================================================

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class BankLedgerRow(BaseModel):
    """
    Bank Ledger (입출금 장부) — SSOT 정규화 행
    - 어댑터(bank_ledger.py)가 정규화한 결과와 동일 스키마
    - direction: IN / OUT (대소문자·한글·부호 입력도 허용하되, 최종 저장은 대문자)
    - amount: 문자열(정규화는 어댑터에서 수행), 콤마 제거/괄호부호/±부호 처리됨
    """
    business_date: str = Field(..., description="업무 일자 (YYYY-MM-DD)")
    property_code: str = Field(..., description="호텔 코드 (예: MOP)")
    txn_id: str = Field(..., description="거래 ID (미입력 시 어댑터가 자동 생성)")
    bank_code: str = Field("", description="은행 코드 (예: KB, NH, WR, SH ...)")
    account_no: str = Field("", description="계좌 번호 (선택)")
    direction: str = Field("IN", description="입출 방향 (IN/OUT)")
    amount: str = Field(..., description="금액 (문자열, 어댑터에서 정규화됨)")
    memo: str = Field("", description="비고 / 메모 (선택)")
    txn_ref: str = Field("", description="거래 참조번호 (선택)")

    # ✅ Pydantic v2 호환 설정
    model_config = ConfigDict(from_attributes=True)

    # ─────────────────────────────────────────────
    # 정규화 보조 (입력 관대 수용 → 저장 일관성)
    # ─────────────────────────────────────────────
    @field_validator("property_code", mode="before")
    @classmethod
    def _upper_pc(cls, v: str) -> str:
        return (v or "").strip().upper()

    @field_validator("bank_code", mode="before")
    @classmethod
    def _upper_bank(cls, v: str) -> str:
        return (v or "").strip().upper()

    @field_validator("direction", mode="before")
    @classmethod
    def _norm_direction(cls, v: Optional[str]) -> str:
        """
        허용 입력: in/out, deposit/withdraw, credit/debit, cr/dr, +/-, 한글(입금/출금)
        최종 표준: 'IN' 또는 'OUT'
        ※ 어댑터 단계에서 이미 정규화되지만, 방어차원에서 재확인
        """
        s = (v or "").strip().lower()
        if s in ("in", "deposit", "credit", "cr", "+", "입금", "유입"):
            return "IN"
        if s in ("out", "withdraw", "debit", "dr", "-", "출금", "지출"):
            return "OUT"
        # 모호하면 금액 부호로 판단은 어댑터에서 처리하므로 기본값 유지
        return "IN"
