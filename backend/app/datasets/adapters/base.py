# app/datasets/adapters/base.py
# -*- coding: utf-8 -*-
from typing import Iterable, Dict, Any, Tuple
from pydantic import BaseModel, Field


# ───────────────────────────────────────────────
# CanonRecord: Merge Engine 공통 데이터 단위
# ───────────────────────────────────────────────
class CanonRecord(BaseModel):
    """
    정규화/파싱 후 엔진으로 전달되는 표준 레코드 단위
    - business_date / property_code / key_tuple / payload
    """
    business_date: str = Field(..., description="YYYY-MM-DD")
    property_code: str = Field(..., description="호텔 코드")
    payload: Dict[str, Any] = Field(..., description="CSV에서 파싱된 데이터")
    key_tuple: Tuple[Any, ...] = Field(..., description="고유 키 튜플")

    class Config:
        from_attributes = True  # ORM 객체에서 변환 지원

    # ✅ 안전한 클래스 생성기
    @classmethod
    def from_parsed(cls, data: Dict[str, Any], key_tuple: Tuple[Any, ...]) -> "CanonRecord":
        """
        dict 데이터로부터 CanonRecord 생성.
        CSV→Dict→Pydantic 변환 시 필드 누락 방지용.
        """
        return cls(
            business_date=data.get("business_date", ""),
            property_code=data.get("property_code", ""),
            payload=data,
            key_tuple=key_tuple,
        )


# ───────────────────────────────────────────────
# DatasetAdapter: 모든 어댑터의 추상 베이스
# ───────────────────────────────────────────────
class DatasetAdapter:
    """
    모든 데이터셋 어댑터의 공통 인터페이스.
    각 Adapter는 반드시 다음 메서드를 구현해야 함:
    - normalize(raw_csv_text, fallback_business_date, property_code)
    - parse(canon_csv_text)
    - merge_mode(form)
    """
    dataset: str
    schema_model: BaseModel
    key_fields: Tuple[str, ...]
    default_missing_policy: str = "soft_delete"

    # ────────────────────────────────
    # Normalize CSV
    # ────────────────────────────────
    def normalize(self, raw_csv_text: str, fallback_business_date: str, property_code: str) -> str:
        """
        CSV를 표준 포맷으로 변환.
        하위 클래스에서 반드시 구현.
        """
        raise NotImplementedError("normalize() must be implemented by subclass")

    # ────────────────────────────────
    # Parse normalized CSV
    # ────────────────────────────────
    def parse(self, canon_csv_text: str) -> Iterable[CanonRecord]:
        """
        정규화된 CSV를 CanonRecord 시퀀스로 변환.
        하위 클래스에서 반드시 구현.
        """
        raise NotImplementedError("parse() must be implemented by subclass")

    # ────────────────────────────────
    # Determine merge mode
    # ────────────────────────────────
    def merge_mode(self, form: Dict[str, Any]) -> str:
        """
        병합 모드 결정:
        - source_kind 기준으로 snapshot/append 판단
        """
        src = str(form.get("source_kind", "daily")).lower()
        if src in ("weekly", "monthly", "full"):
            return "snapshot"
        return "append"
