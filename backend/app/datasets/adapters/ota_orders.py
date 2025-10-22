# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/datasets/adapters/ota_orders.py
# Version   : 2025.10-30 · v1.0 (Initial · SSOT Canon Integration)
# Purpose   : Hotel Admin — OTA Orders Adapter
# ----------------------------------------------------------------------------
# 목적:
#   • OTA(온라인 여행사) 주문/예약 데이터 업로드 어댑터
#   • CSV → CanonRecord 변환 → Merge Engine 병합
# ----------------------------------------------------------------------------
# 주요 기능:
#   ✅ CSV Normalize → Canon CSV 변환
#   ✅ CanonRecord Stream 반환 (엔진에 직접 전달)
#   ✅ dataset="ota_orders" 로 병합엔진과 연동
# ----------------------------------------------------------------------------
# 연계:
#   • models/canon.py → OtaOrdersCanon / OtaOrdersHistory (추가 예정)
#   • core/settings_merge.py → dataset 정책 "ota_orders"
#   • merge_engine/engine.py → run_merge()
#   • upload/{dataset} → /api/upload/ota_orders
# ============================================================================
import csv
from io import StringIO
from typing import Dict, Any, Iterable, List, Tuple
from pydantic import BaseModel, ValidationError

from app.datasets.adapters.base import DatasetAdapter, CanonRecord


# ============================================================================
# 1️⃣ 내부 검증 스키마
# ----------------------------------------------------------------------------
class OtaOrdersSchema(BaseModel):
    business_date: str          # YYYY-MM-DD
    property_code: str          # 예: MOP
    order_code: str             # OTA 주문번호
    channel: str                # OTA 채널 (예: BOOKING, AGODA)
    amount: str                 # 총금액
    commission: str = "0"       # 수수료 금액 (선택)
    note: str = ""              # 비고 (선택)

    class Config:
        from_attributes = True


# ============================================================================
# 2️⃣ 어댑터 본체
# ----------------------------------------------------------------------------
class OtaOrdersAdapter(DatasetAdapter):
    """
    OTA Orders Adapter
    - dataset : ota_orders
    - key_fields : (business_date, property_code, order_code)
    - merge_mode : append
    - missing_policy : ignore
    """
    dataset = "ota_orders"
    schema_model = OtaOrdersSchema
    key_fields: Tuple[str, ...] = ("business_date", "property_code", "order_code")
    hash_fields: Tuple[str, ...] = ("channel", "amount", "commission", "note")
    default_missing_policy: str = "ignore"

    # ─────────────────────────────────────────────
    def normalize(
        self,
        raw_csv_text: str,
        fallback_business_date: str = "",
        property_code: str = "MOP",
    ) -> str:
        """
        원본 CSV를 Canon 표준 CSV로 정규화
        - BOM, 개행, 공백 정리
        - 필수 컬럼 주입: business_date, property_code
        """
        required = ["business_date", "property_code", "order_code", "channel", "amount", "commission", "note"]
        src = StringIO(raw_csv_text.strip().lstrip("\ufeff"))
        reader = csv.DictReader(src)
        rows: List[Dict[str, Any]] = []

        if not reader.fieldnames:
            # 헤더 없는 경우 빈 Canon 스켈레톤 반환
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
            oc = pick(r, "order_code", "")
            ch = pick(r, "channel", "")
            amt = pick(r, "amount", "0").replace(",", "")
            cm = pick(r, "commission", "0").replace(",", "")
            note = pick(r, "note", "")

            if not bd or not oc or not ch:
                continue

            rows.append({
                "business_date": bd,
                "property_code": pc.upper(),
                "order_code": oc,
                "channel": ch.upper(),
                "amount": amt,
                "commission": cm,
                "note": note,
            })

        return self._to_csv(required, rows)

    # ─────────────────────────────────────────────
    def parse(self, canon_csv_text: str) -> Iterable[CanonRecord]:
        """
        Canon CSV를 CanonRecord 스트림으로 변환
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
    def merge_mode(self, form: Dict[str, Any]) -> str:
        """
        병합 모드 결정:
        - OTA Orders 는 append 기반
        """
        return "append"

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


# ============================================================================
# 3️⃣ Export
# ============================================================================
__all__ = ["OtaOrdersAdapter", "OtaOrdersSchema"]
