# app/datasets/adapters/sales_front.py
# -*- coding: utf-8 -*-
# version: 2025-10-11 Phase 2 (sales_front adapter)

from io import StringIO
import csv
from typing import Dict, Any, Iterable, List

from .base import DatasetAdapter, CanonRecord


class SalesFrontAdapter(DatasetAdapter):
    """
    Front Sales (전면 매출) 업로드 어댑터
    - key: (business_date, property_code, tag)
    - values: amount
    - merge mode: snapshot (기본)
    """
    dataset = "sales_front"
    key_fields = ["business_date", "property_code", "tag"]
    hash_fields = ["amount"]
    default_missing_policy = "soft_delete"  # snapshot 기본

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
            tag = str(pick(r, "tag", "")).strip()
            amt = str(pick(r, "amount", "0")).strip()

            if not bd or not pc or not tag:
                continue

            amt = amt.replace(",", "").strip()
            if amt == "":
                amt = "0"

            rows.append({
                "business_date": bd,
                "property_code": pc,
                "tag": tag,
                "amount": amt,
            })

        return self._to_csv(required, rows)

    # ─────────────────────────────────────────────
    # Canon CSV → CanonRecord generator
    # ─────────────────────────────────────────────
    def parse(self, canon_csv_text: str) -> Iterable[CanonRecord]:
        reader = csv.DictReader(StringIO(canon_csv_text or ""))
        for r in reader:
            bd = (r.get("business_date") or "").strip()
            pc = (r.get("property_code") or "").strip()
            tag = (r.get("tag") or "").strip()
            amt = (r.get("amount") or "0").replace(",", "").strip()
            payload = {
                "business_date": bd,
                "property_code": pc,
                "tag": tag,
                "amount": amt,
            }
            key_tuple = (bd, pc, tag)
            yield CanonRecord(key_tuple=key_tuple, payload=payload)

    # ─────────────────────────────────────────────
    # 병합 모드 (snapshot / append ... )
    # ─────────────────────────────────────────────
    def merge_mode(self, form: Dict[str, Any]) -> str:
        return "snapshot"

    # ─────────────────────────────────────────────
    # 내부 유틸
    # ─────────────────────────────────────────────
    @staticmethod
    def _to_csv(headers: List[str], rows: List[Dict[str, Any]]) -> str:
        buf = StringIO()
        writer = csv.DictWriter(buf, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            writer.writerow({h: r.get(h, "") for h in headers})
        return buf.getvalue()
