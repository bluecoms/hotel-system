# app/datasets/adapters/fnb_items.py
# -*- coding: utf-8 -*-
# version: 2025-10-12 Phase 2 Final (fnb_items adapter)

import csv
import io
from typing import Iterable, Dict, Any, Tuple, List
from pydantic import BaseModel, ValidationError

from app.datasets.adapters.base import DatasetAdapter, CanonRecord


# ─────────────────────────────────────────────
# Pydantic Schema
# ─────────────────────────────────────────────
class FnbItemsSchema(BaseModel):
    business_date: str
    property_code: str
    item_code: str
    category: str = ""
    qty: str = "0"
    amount: str = "0"

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# Adapter 본체
# ─────────────────────────────────────────────
class FnbItemsAdapter(DatasetAdapter):
    """
    F&B Items (품목별 매출) 업로드 어댑터
    - key: (business_date, property_code, item_code)
    - values: category, qty, amount
    - merge mode: snapshot
    """
    dataset = "fnb_items"
    schema_model = FnbItemsSchema
    key_fields: Tuple[str, ...] = ("business_date", "property_code", "item_code")
    hash_fields: Tuple[str, ...] = ("category", "qty", "amount")
    default_missing_policy: str = "soft_delete"

    def normalize(self, raw_csv_text: str, fallback_business_date: str = "", property_code: str = "MOP") -> str:
        required = ["business_date", "property_code", "item_code", "category", "qty", "amount"]
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
            ic = pick(r, "item_code")
            cat = pick(r, "category", "")
            qty = pick(r, "qty", "0")
            amt = pick(r, "amount", "0").replace(",", "")

            if not bd or not pc or not ic:
                continue

            rows.append({
                "business_date": bd,
                "property_code": pc.upper(),
                "item_code": ic,
                "category": cat,
                "qty": qty,
                "amount": amt,
            })

        return self._to_csv(required, rows)

    def parse(self, canon_csv_text: str) -> Iterable[CanonRecord]:
        reader = csv.DictReader(io.StringIO(canon_csv_text or ""))
        for r in reader:
            if not any((v or "").strip() for v in r.values()):
                continue
            try:
                data = self.schema_model(**r).dict()
            except ValidationError as e:
                raise ValueError(f"Invalid row: {r} ({e})")

            key_tuple = tuple(data[k] for k in self.key_fields)
            yield CanonRecord.from_parsed(data, key_tuple)

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
