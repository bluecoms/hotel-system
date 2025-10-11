# app/datasets/adapters/rooms_status.py
# -*- coding: utf-8 -*-
# version: 2025-10-12 Final (rooms_status adapter)
"""
RoomsStatusAdapter
──────────────────────────────────────────────
- CSV normalize → parse → CanonRecord
- 필수 필드 자동 주입(business_date, property_code)
- 공백/대소문자/부울 정규화
"""

import csv
import io
from typing import Iterable, Dict, Any, Tuple
from pydantic import BaseModel, ValidationError

from app.datasets.adapters.base import DatasetAdapter, CanonRecord


# ─────────────────────────────────────────────
# Pydantic 스키마 (내부 검증용)
# ─────────────────────────────────────────────
class RoomsStatusSchema(BaseModel):
    business_date: str
    property_code: str
    room_no: str
    status: str = ""
    note: str = ""
    is_dirty: str = "0"

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# Adapter 본체
# ─────────────────────────────────────────────
class RoomsStatusAdapter(DatasetAdapter):
    dataset = "rooms_status"
    schema_model = RoomsStatusSchema
    key_fields: Tuple[str, ...] = ("business_date", "property_code", "room_no")
    hash_fields: Tuple[str, ...] = ("status", "note", "is_dirty")
    default_missing_policy: str = "soft_delete"

    def normalize(self, raw_csv_text: str, fallback_business_date: str = "", property_code: str = "MOP") -> str:
        """
        CSV 정규화:
        - BOM/개행/공백 제거
        - business_date / property_code 주입
        - 필수 컬럼(room_no, status) 보강
        """
        if not raw_csv_text:
            return self._to_csv(["business_date", "property_code", "room_no", "status", "note", "is_dirty"], [])

        text = (
            raw_csv_text.replace("\r\n", "\n")
            .replace("\r", "\n")
            .lstrip("\ufeff")
            .strip()
        )
        src = io.StringIO(text)
        reader = csv.DictReader(src)
        rows = []

        headers = [h.strip() for h in (reader.fieldnames or [])]
        lower_map = {h.lower(): h for h in headers}

        def pick(row: Dict[str, Any], key: str, default: str = "") -> str:
            lk = key.lower()
            src_key = lower_map.get(lk)
            return str(row.get(src_key or key, default)).strip()

        for r in reader:
            bd = pick(r, "business_date", fallback_business_date)
            pc = pick(r, "property_code", property_code)
            rn = pick(r, "room_no", "")
            st = pick(r, "status", pick(r, "status_code", ""))
            nt = pick(r, "note", pick(r, "hk_note", ""))
            dirty = pick(r, "is_dirty", "")

            if not bd or not rn:
                continue

            # is_dirty 정규화
            d = dirty.lower()
            if d in ("1", "true", "t", "y", "yes"):
                d = "1"
            elif d in ("0", "false", "f", "n", "no", ""):
                d = "0"
            else:
                d = "1" if d.isdigit() and d != "0" else "0"

            rows.append({
                "business_date": bd,
                "property_code": pc.upper(),
                "room_no": rn,
                "status": st.upper(),
                "note": nt,
                "is_dirty": d,
            })

        headers_final = ["business_date", "property_code", "room_no", "status", "note", "is_dirty"]
        return self._to_csv(headers_final, rows)

    def parse(self, canon_csv_text: str) -> Iterable[CanonRecord]:
        """
        Canon CSV를 CanonRecord 스트림으로 변환
        """
        reader = csv.DictReader(io.StringIO(canon_csv_text or ""))
        for r in reader:
            if not any((v or "").strip() for v in r.values()):
                continue
            try:
                data = self.schema_model(**r).dict()
            except ValidationError as e:
                raise ValueError(f"Invalid row: {r} ({e})")

            key_tuple = tuple(data[k] for k in self.key_fields)

            # ✅ 수정: from_parsed(data, key_tuple)
            yield CanonRecord.from_parsed(data, key_tuple)

    def merge_mode(self, form: Dict[str, Any]) -> str:
        """
        업로드 모드 결정:
        - form.mode → snapshot 힌트(split_by_date=1) → 기본 snapshot
        """
        m = str(form.get("mode", "")).strip().lower()
        if m in ("append", "snapshot"):
            return m
        if str(form.get("split_by_date", "0")).strip() == "1":
            return "snapshot"
        return "snapshot"

    @staticmethod
    def _to_csv(headers, rows):
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            writer.writerow({h: r.get(h, "") for h in headers})
        return buf.getvalue()
