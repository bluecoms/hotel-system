# app/datasets/adapters/bank_ledger.py
# -*- coding: utf-8 -*-
# version: 2025-10-11 Phase 2 (bank_ledger adapter)

from io import StringIO
import csv
from typing import Dict, Any, Iterable, List

from .base import DatasetAdapter, CanonRecord


class BankLedgerAdapter(DatasetAdapter):
    """
    Bank Ledger (입출금 장부) 업로드 어댑터
    - key: (business_date, property_code, txn_id)
      txn_id 없을 경우 행 번호 기반 surrogate ID 생성
    - values: account_no, direction(in/out), amount, memo
    - merge mode: append (기본)
    """
    dataset = "bank_ledger"
    key_fields = ["business_date", "property_code", "txn_id"]
    hash_fields = ["account_no", "direction", "amount", "memo"]
    default_missing_policy = "ignore"  # append 데이터는 기본 ignore

    # ─────────────────────────────────────────────
    # 업로드 파일 → Canon CSV 문자열
    # ─────────────────────────────────────────────
    def normalize(
        self,
        raw_csv_text: str,
        fallback_business_date: str = "",
        property_code: str = "MOP",
    ) -> str:
        """
        입력 CSV를 표준 컬럼으로 정규화:
          business_date, property_code, txn_id, account_no, direction, amount, memo
        - txn_id가 없으면 행번호 기반 생성
        - direction은 in/out으로 정규화
        """
        required = [
            "business_date",
            "property_code",
            "txn_id",
            "account_no",
            "direction",
            "amount",
            "memo",
        ]

        src = StringIO(raw_csv_text or "")
        reader = csv.DictReader(src)
        rows: List[Dict[str, Any]] = []

        if not reader.fieldnames:
            return self._to_csv(required, [])

        headers = [h.strip() for h in reader.fieldnames]
        lower_map = {h.lower(): h for h in headers}

        def pick(row: Dict[str, Any], key: str, default: Any = "") -> Any:
            """대소문자 무시 안전 추출"""
            if key in row:
                return row[key]
            lk = key.lower()
            src_key = lower_map.get(lk)
            if src_key and src_key in row:
                return row[src_key]
            return default

        line_no = 1
        for r in reader:
            bd = str(pick(r, "business_date", fallback_business_date)).strip()
            pc = str(pick(r, "property_code", property_code)).strip()
            txn_id = str(pick(r, "txn_id", "")).strip()
            account_no = str(pick(r, "account_no", "")).strip()
            direction = str(pick(r, "direction", "")).strip().lower()
            amount = str(pick(r, "amount", "0")).strip()
            memo = str(pick(r, "memo", "")).strip()

            if not bd or not pc:
                continue

            # txn_id 대체 생성
            if not txn_id:
                txn_id = f"{bd}-{pc}-L{line_no}"
            line_no += 1

            # direction 정규화
            if direction in ("in", "deposit", "credit", "cr", "+", "입금", "유입"):
                direction = "in"
            elif direction in ("out", "withdraw", "debit", "dr", "-", "출금", "지출"):
                direction = "out"
            else:
                direction = "out" if amount.startswith("-") else "in"

            # 금액 정규화
            amount = amount.replace(",", "").strip()
            if amount == "":
                amount = "0"

            rows.append({
                "business_date": bd,
                "property_code": pc,
                "txn_id": txn_id,
                "account_no": account_no,
                "direction": direction,
                "amount": amount,
                "memo": memo,
            })

        return self._to_csv(required, rows)

    # ─────────────────────────────────────────────
    # Canon CSV → CanonRecord generator
    # ─────────────────────────────────────────────
    def parse(self, canon_csv_text: str) -> Iterable[CanonRecord]:
        """정규화된 CSV를 CanonRecord 시퀀스로 변환"""
        reader = csv.DictReader(StringIO(canon_csv_text or ""))
        for r in reader:
            bd = (r.get("business_date") or "").strip()
            pc = (r.get("property_code") or "").strip()
            txn_id = (r.get("txn_id") or "").strip()
            account_no = (r.get("account_no") or "").strip()
            direction = (r.get("direction") or "").strip()
            amount = (r.get("amount") or "0").replace(",", "").strip()
            memo = (r.get("memo") or "").strip()

            payload = {
                "business_date": bd,
                "property_code": pc,
                "txn_id": txn_id,
                "account_no": account_no,
                "direction": direction,
                "amount": amount,
                "memo": memo,
            }
            key_tuple = (bd, pc, txn_id)
            yield CanonRecord(key_tuple=key_tuple, payload=payload)

    # ─────────────────────────────────────────────
    # 병합 모드 결정
    # ─────────────────────────────────────────────
    def merge_mode(self, form: Dict[str, Any]) -> str:
        """입출금 장부는 append 기본, 필요시 form에서 snapshot 지정"""
        mode = str(form.get("mode", "append")).strip().lower()
        if mode not in ("append", "snapshot"):
            mode = "append"
        return mode

    # ─────────────────────────────────────────────
    # 내부 유틸: CSV writer
    # ─────────────────────────────────────────────
    @staticmethod
    def _to_csv(headers: List[str], rows: List[Dict[str, Any]]) -> str:
        """Dict 리스트를 CSV 문자열로 변환"""
        buf = StringIO()
        writer = csv.DictWriter(buf, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            writer.writerow({h: r.get(h, "") for h in headers})
        return buf.getvalue()
