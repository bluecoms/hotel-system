# app/datasets/adapters/sales_front.py
# -*- coding: utf-8 -*-
# version: 2025-10-12 Phase 2 Final (sales_front adapter)

import csv
from io import StringIO
from typing import Dict, Any, Iterable, List, Tuple
from pydantic import BaseModel, ValidationError

from app.datasets.adapters.base import DatasetAdapter, CanonRecord


# ─────────────────────────────────────────────
# Pydantic 스키마
# ─────────────────────────────────────────────
class SalesFrontSchema(BaseModel):
    business_date: str
    property_code: str
    tag: str
    amount: str = "0"

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# Adapter 본체
# ─────────────────────────────────────────────
class SalesFrontAdapter(DatasetAdapter):
    """
    Front Sales (전면 매출) 업로드 어댑터
    - key: (business_date, property_code, tag)
    - values: amount
    - merge mode: snapshot (기본)
    """
    dataset = "sales_front"
    schema_model = SalesFrontSchema
    key_fields: Tuple[str, ...] = ("business_date", "property_code", "tag")
    hash_fields: Tuple[str, ...] = ("amount",)
    default_missing_policy: str = "soft_delete"

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
        입력 CSV를 표준 헤더/값으로 맞춘 Canon CSV를 리턴.
        필수 컬럼 미존재 시 생성/보강:
          business_date, property_code, tag, amount
        """
        required = ["business_date", "property_code", "tag", "amount"]

        src = StringIO(raw_csv_text or "")
        reader = csv.DictReader(src)
        rows: List[Dict[str, Any]] = []

        if not reader.fieldnames:
            # 헤더 없는 경우: 빈 Canon 스켈레톤
            return self._to_csv(required, [])

        # 필드명 소문자화
        headers = [h.strip() for h in reader.fieldnames]
        lower_map = {h.lower(): h for h in headers}

        def pick(row: Dict[str, Any], key: str, default: Any = "") -> Any:
            lk = key.lower()
            src_key = lower_map.get(lk)
            return (row.get(src_key or key, default) or "").strip()

        for r in reader:
            bd = pick(r, "business_date", fallback_business_date)
            pc = pick(r, "property_code", property_code)
            tag = pick(r, "tag", "")
            amt = pick(r, "amount", "0").replace(",", "")

            if not bd or not pc or not tag:
                continue

            if amt == "":
                amt = "0"

            rows.append({
                "business_date": bd,
                "property_code": pc.upper(),
                "tag": tag,
                "amount": amt,
            })

        return self._to_csv(required, rows)

    # ─────────────────────────────────────────────
    # Canon CSV → CanonRecord generator
    # ─────────────────────────────────────────────
    def parse(self, canon_csv_text: str) -> Iterable[CanonRecord]:
        """
        정규화된 Canon CSV를 CanonRecord 시퀀스로 변환
        """
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
    # 병합 모드 (snapshot / append ... )
    # ─────────────────────────────────────────────
    def merge_mode(self, form: Dict[str, Any]) -> str:
        """Front Sales는 기본 snapshot"""
        return "snapshot"

    # ─────────────────────────────────────────────
    # 내부 유틸
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
