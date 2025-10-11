# app/datasets/adapters/fnb_tenders.py
# -*- coding: utf-8 -*-
# version: 2025-10-11 Phase 2 (fnb_tenders adapter)

import csv
import io
from typing import Iterable, Dict, Any, Tuple, List

from app.datasets.adapters.base import DatasetAdapter, CanonRecord


class FnbTendersAdapter(DatasetAdapter):
    """
    F&B Tenders (결제수단별 매출) 업로드 어댑터
    - key: (business_date, property_code, tender_code)
    - values: amount, count
    - merge mode: snapshot
    """
    dataset = "fnb_tenders"
    key_fields: Tuple[str, ...] = ("business_date", "property_code", "tender_code")
    hash_fields: Tuple[str, ...] = ("amount", "count")
    default_missing_policy: str = "soft_delete"

    def normalize(self, raw_csv_text: str, fallback_business_date: str = "", property_code: str = "MOP") -> str:
        required = ["business_date", "property_code", "tender_code", "amount", "count"]
        src = io.StringIO(raw_csv_text or "")
        reader = csv.DictReader(src)
        rows: List[Dict[str, Any]] = []

        if not reader.fieldnames:
            return self._to_csv(required, [])

        headers = [h.strip() for h in reader.fieldnames]
        lower_map = {h.lower(): h for h in headers}

        def pick(row, key, default=""):
            lk = key.lower()
            src_key = lower_map.get(lk)
            return (row.get(src_key or key, default) or "").strip()

        for r in reader:
            bd = pick(r, "business_date", fallback_business_date)
            pc = pick(r, "property_code", property_code)
            tc = pick(r, "tender_code")
            amt = pick(r, "amount", "0").replace(",", "")
            cnt = pick(r, "count", "0")

            if not bd or not pc or not tc:
                continue

            rows.append({
                "business_date": bd,
                "property_code": pc,
                "tender_code": tc,
                "amount": amt,
                "count": cnt,
            })

        return self._to_csv(required, rows)

    def parse(self, canon_csv_text: str) -> Iterable[CanonRecord]:
        reader = csv.DictReader(io.StringIO(canon_csv_text or ""))
        for r in reader:
            payload = {
                "business_date": r.get("business_date", "").strip(),
                "property_code": r.get("property_code", "").strip(),
                "tender_code": r.get("tender_code", "").strip(),
                "amount": r.get("amount", "0").replace(",", "").strip(),
                "count": r.get("count", "0").strip(),
            }
            key_tuple = (
                payload["business_date"],
                payload["property_code"],
                payload["tender_code"],
            )
            yield CanonRecord(key_tuple=key_tuple, payload=payload)

    def merge_mode(self, form: Dict[str, Any]) -> str:
        return "snapshot"

    @staticmethod
    def _to_csv(headers, rows):
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            writer.writerow({h: r.get(h, "") for h in headers})
        return buf.getvalue()
