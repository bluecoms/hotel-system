# app/datasets/adapters/expenses.py
# -*- coding: utf-8 -*-
# version: 2025-10-11 Phase 2 (expenses adapter)

from io import StringIO
import csv
from typing import Dict, Any, Iterable, List

from .base import DatasetAdapter, CanonRecord


class ExpensesAdapter(DatasetAdapter):
    """
    Expenses (지출 내역) 업로드 어댑터
    - key: (business_date, property_code, account_code)
    - values: amount, note
    - merge mode: snapshot
    """
    dataset = "expenses"
    key_fields = ["business_date", "property_code", "account_code"]
    hash_fields = ["amount", "note"]
    default_missing_policy = "soft_delete"

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
        입력 CSV를 표준화하여 Canon CSV 문자열로 반환
        필수 컬럼: business_date, property_code, account_code, amount, note
        """
        required = ["business_date", "property_code", "account_code", "amount", "note"]

        src = StringIO(raw_csv_text or "")
        reader = csv.DictReader(src)
        rows: List[Dict[str, Any]] = []

        if not reader.fieldnames:
            # 헤더가 없으면 빈 CSV 반환
            return self._to_csv(required, [])

        headers = [h.strip() for h in reader.fieldnames]
        lower_map = {h.lower(): h for h in headers}

        def pick(row: Dict[str, Any], key: str, default: Any = "") -> Any:
            """대소문자 무시하고 안전하게 필드값 선택"""
            if key in row:
                return row[key]
            lk = key.lower()
            src_key = lower_map.get(lk)
            if src_key and src_key in row:
                return row[src_key]
            return default

        for r in reader:
            bd = str(pick(r, "business_date", fallback_business_date)).strip()
            pc = str(pick(r, "property_code", property_code)).strip()
            ac = str(pick(r, "account_code", "")).strip()
            amt = str(pick(r, "amount", "0")).strip()
            note = str(pick(r, "note", "")).strip()

            # 필수 키 없으면 스킵
            if not bd or not pc or not ac:
                continue

            # 금액 정규화
            amt = amt.replace(",", "").strip()
            if amt == "":
                amt = "0"

            rows.append({
                "business_date": bd,
                "property_code": pc,
                "account_code": ac,
                "amount": amt,
                "note": note,
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
            ac = (r.get("account_code") or "").strip()
            amt = (r.get("amount") or "0").replace(",", "").strip()
            note = (r.get("note") or "").strip()

            payload = {
                "business_date": bd,
                "property_code": pc,
                "account_code": ac,
                "amount": amt,
                "note": note,
            }
            key_tuple = (bd, pc, ac)
            yield CanonRecord(key_tuple=key_tuple, payload=payload)

    # ─────────────────────────────────────────────
    # 병합 모드 (snapshot / append ...)
    # ─────────────────────────────────────────────
    def merge_mode(self, form: Dict[str, Any]) -> str:
        """기본 병합 모드 snapshot"""
        return "snapshot"

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
