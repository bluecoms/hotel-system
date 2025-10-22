# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/datasets/adapters/expenses.py
# Version   : 2025.10-30 · v3.0 (SSOT Stable · Category/Pay Sync)
# Purpose   : Hotel Admin — Expenses Adapter (지출내역 업로드)
# ----------------------------------------------------------------------------
# 목적:
#   • 호텔 지출내역 CSV 파일을 Canon 표준 포맷으로 정규화
#   • property_code + account_code + business_date 기준 병합 (snapshot 모드)
# ----------------------------------------------------------------------------
# 특징:
#   • category_code, pay_method 필드 추가
#   • 금액(amount) → 문자열에서 정수형 문자열로 변환
#   • note·memo 통합 처리
#   • 누락된 필드 자동 생성 (0 / 빈 문자열)
#   • merge_mode = snapshot / missing_policy = soft_delete
# ----------------------------------------------------------------------------
# 연계:
#   • models/canon.py → ExpensesCanon / ExpensesHistory (추가 예정)
#   • merge_engine/engine.py / repository.py → 병합 처리
#   • upload 엔드포인트: /api/upload/expenses
# ============================================================================
import csv
from io import StringIO
from typing import Dict, Any, Iterable, List, Tuple
from pydantic import BaseModel, ValidationError

from app.datasets.adapters.base import DatasetAdapter, CanonRecord


# ============================================================================
# 1️⃣ 내부 검증 스키마
# ----------------------------------------------------------------------------
class ExpensesSchema(BaseModel):
    business_date: str
    property_code: str
    account_code: str
    category_code: str = ""      # 예: OFFICE, SUPPLY, FNB
    pay_method: str = ""         # 예: CASH / CARD / TRANSFER
    amount: str = "0"
    note: str = ""

    class Config:
        from_attributes = True


# ============================================================================
# 2️⃣ 어댑터 본체
# ----------------------------------------------------------------------------
class ExpensesAdapter(DatasetAdapter):
    """
    Expenses (지출 내역) 업로드 어댑터
    - key: (business_date, property_code, account_code)
    - values: category_code, pay_method, amount, note
    - merge mode: snapshot
    - missing policy: soft_delete
    """
    dataset = "expenses"
    schema_model = ExpensesSchema
    key_fields: Tuple[str, ...] = ("business_date", "property_code", "account_code")
    hash_fields: Tuple[str, ...] = ("category_code", "pay_method", "amount", "note")
    default_missing_policy: str = "soft_delete"

    # ─────────────────────────────────────────────
    def normalize(
        self,
        raw_csv_text: str,
        fallback_business_date: str = "",
        property_code: str = "MOP",
    ) -> str:
        """
        원본 CSV를 Canon 표준 헤더로 정규화
        필수 컬럼: business_date, property_code, account_code,
                  category_code, pay_method, amount, note
        """
        required = [
            "business_date", "property_code", "account_code",
            "category_code", "pay_method", "amount", "note",
        ]

        src = StringIO(raw_csv_text.strip().lstrip("\ufeff"))
        reader = csv.DictReader(src)
        rows: List[Dict[str, Any]] = []

        if not reader.fieldnames:
            return self._to_csv(required, [])

        headers = [h.strip() for h in reader.fieldnames]
        lower_map = {h.lower(): h for h in headers}

        def pick(row: Dict[str, Any], key: str, default: Any = "") -> Any:
            lk = key.lower()
            src_key = lower_map.get(lk)
            return (row.get(src_key or key, default) or "").strip()

        for r in reader:
            bd = pick(r, "business_date", fallback_business_date)
            pc = pick(r, "property_code", property_code)
            ac = pick(r, "account_code", "")
            cat = pick(r, "category_code", pick(r, "category", ""))
            pay = pick(r, "pay_method", pick(r, "method", ""))
            amt = pick(r, "amount", "0").replace(",", "").strip()
            note = pick(r, "note", pick(r, "memo", ""))

            if not bd or not pc or not ac:
                continue

            if amt == "":
                amt = "0"

            # 결제 수단 정규화
            pay_upper = pay.upper()
            if pay_upper in ("CARD", "CC", "신용카드", "카드"):
                pay_upper = "CARD"
            elif pay_upper in ("CASH", "현금"):
                pay_upper = "CASH"
            elif pay_upper in ("TRANSFER", "BANK", "계좌이체"):
                pay_upper = "TRANSFER"
            elif pay_upper in ("ETC", "기타"):
                pay_upper = "ETC"
            elif not pay_upper:
                pay_upper = "ETC"

            rows.append({
                "business_date": bd,
                "property_code": pc.upper(),
                "account_code": ac.upper(),
                "category_code": cat.upper(),
                "pay_method": pay_upper,
                "amount": amt,
                "note": note,
            })

        return self._to_csv(required, rows)

    # ─────────────────────────────────────────────
    def parse(self, canon_csv_text: str) -> Iterable[CanonRecord]:
        """정규화된 CSV를 CanonRecord 시퀀스로 변환"""
        reader = csv.DictReader(StringIO(canon_csv_text or ""))
        for r in reader:
            if not any((v or "").strip() for v in r.values()):
                continue
            try:
                data = self.schema_model(**r).dict()
            except ValidationError as e:
                raise ValueError(f"Invalid row: {r} ({e})")

            key_tuple = tuple(data[k] for k in self.key_fields)
            yield CanonRecord.from_parsed(data, key_tuple)

    # ─────────────────────────────────────────────
    def merge_mode(self, form: Dict[str, Any]) -> str:
        """지출내역은 snapshot 병합"""
        return "snapshot"


# ============================================================================
# 3️⃣ Export
# ============================================================================
__all__ = ["ExpensesAdapter", "ExpensesSchema"]
