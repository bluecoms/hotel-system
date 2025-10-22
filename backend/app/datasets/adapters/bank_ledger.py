# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/datasets/adapters/bank_ledger.py
# Version   : 2025.10-30 · v3.0 (SSOT Stable · Bank/Property Sync)
# Purpose   : Hotel Admin — Bank Ledger Adapter
# ----------------------------------------------------------------------------
# 목적:
#   • 은행 입출금 내역 CSV 업로드를 Canon 표준 포맷으로 정규화
#   • property_code + bank_code + txn_id 기준 병합 (append 모드)
#   • MasterBank / BankAccount 와 연동 가능한 구조 유지
# ----------------------------------------------------------------------------
# 특징:
#   • direction → "IN"/"OUT" 으로 정규화 (국문/영문 혼합 지원)
#   • 금액(amount)은 문자열 → 정수형 변환 전 CSV 저장
#   • 누락 txn_id 자동 생성 ("{date}-{property}-{seq}")
#   • merge_mode = append / missing_policy = ignore
# ----------------------------------------------------------------------------
# 연계:
#   • models/canon.py → BankLedgerCanon / BankLedgerHistory (추가 예정)
#   • merge_engine/engine.py / repository.py → 병합 처리
#   • upload 엔드포인트: /api/upload/bank_ledger
# ============================================================================
import csv
from io import StringIO
from typing import Dict, Any, Iterable, List, Tuple
from pydantic import BaseModel, ValidationError

from app.datasets.adapters.base import DatasetAdapter, CanonRecord


# ============================================================================
# 1️⃣ 내부 검증 스키마
# ----------------------------------------------------------------------------
class BankLedgerSchema(BaseModel):
    business_date: str
    property_code: str
    txn_id: str
    bank_code: str = ""          # ex) KB, NH, WR
    account_no: str = ""
    direction: str = ""          # IN / OUT
    amount: str = "0"
    memo: str = ""
    txn_ref: str = ""            # 거래참조번호 (optional)

    class Config:
        from_attributes = True


# ============================================================================
# 2️⃣ 어댑터 본체
# ----------------------------------------------------------------------------
class BankLedgerAdapter(DatasetAdapter):
    """
    Bank Ledger Adapter
    - dataset : bank_ledger
    - key_fields : (business_date, property_code, txn_id)
    - hash_fields : (bank_code, account_no, direction, amount, memo)
    - merge_mode : append
    - missing_policy : ignore
    """
    dataset = "bank_ledger"
    schema_model = BankLedgerSchema
    key_fields: Tuple[str, ...] = ("business_date", "property_code", "txn_id")
    hash_fields: Tuple[str, ...] = ("bank_code", "account_no", "direction", "amount", "memo")
    default_missing_policy: str = "ignore"

    # ─────────────────────────────────────────────
    def normalize(
        self,
        raw_csv_text: str,
        fallback_business_date: str = "",
        property_code: str = "MOP",
    ) -> str:
        """
        원본 CSV를 Canon 표준 헤더로 정규화.
        필수 컬럼: business_date, property_code, txn_id, bank_code, account_no,
                   direction, amount, memo, txn_ref
        """
        required = [
            "business_date", "property_code", "txn_id",
            "bank_code", "account_no", "direction",
            "amount", "memo", "txn_ref",
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

        line_no = 1
        for r in reader:
            bd = pick(r, "business_date", fallback_business_date)
            pc = pick(r, "property_code", property_code)
            txn_id = pick(r, "txn_id", "")
            bank_code = pick(r, "bank_code", "")
            account_no = pick(r, "account_no", "")
            direction = pick(r, "direction", "").lower()
            amount = pick(r, "amount", "0").replace(",", "").strip()
            memo = pick(r, "memo", "")
            txn_ref = pick(r, "txn_ref", "")

            if not bd or not pc:
                continue

            # txn_id 자동 생성
            if not txn_id:
                txn_id = f"{bd}-{pc}-TX{line_no:04d}"
            line_no += 1

            # 방향 정규화
            if direction in ("in", "deposit", "credit", "cr", "+", "입금", "유입"):
                direction = "IN"
            elif direction in ("out", "withdraw", "debit", "dr", "-", "출금", "지출"):
                direction = "OUT"
            else:
                direction = "OUT" if amount.startswith("-") else "IN"

            rows.append({
                "business_date": bd,
                "property_code": pc.upper(),
                "txn_id": txn_id,
                "bank_code": bank_code.upper(),
                "account_no": account_no,
                "direction": direction,
                "amount": amount or "0",
                "memo": memo,
                "txn_ref": txn_ref,
            })

        return self._to_csv(required, rows)

    # ─────────────────────────────────────────────
    def parse(self, canon_csv_text: str) -> Iterable[CanonRecord]:
        """Canon CSV → CanonRecord 시퀀스 변환"""
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
        """Bank Ledger 는 append 모드 고정"""
        return "append"


# ============================================================================
# 3️⃣ Export
# ============================================================================
__all__ = ["BankLedgerAdapter", "BankLedgerSchema"]
