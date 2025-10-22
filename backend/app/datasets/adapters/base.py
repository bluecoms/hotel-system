# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/datasets/adapters/base.py
# Version   : 2025.10-30 · v3.1 (SSOT Stable · CanonRecord Core)
# Purpose   : Hotel Admin — Dataset Adapter Base (Merge Engine 공통 베이스)
# ----------------------------------------------------------------------------
# 목적:
#   • 모든 CSV 업로드 어댑터(Rooms, Sales, FNB, OTA 등)의 공통 기반 클래스
#   • CSV → CanonRecord 표준 포맷으로 변환
#   • Merge Engine(merge_engine/engine.py)과 직접 호환
# ----------------------------------------------------------------------------
# 구조:
#   ✅ CanonRecord : 정규화/파싱 후 Merge Engine으로 전달되는 표준 단위
#   ✅ DatasetAdapter : 각 어댑터 공통 인터페이스 (normalize / parse / merge_mode)
# ----------------------------------------------------------------------------
# 연계:
#   • app/datasets/adapters/{rooms_status, sales_front, ota_orders}.py
#   • app/merge_engine/engine.py / repository.py
#   • app/core/settings_merge.py
# ----------------------------------------------------------------------------
# 변경 로그:
#   v3.1 (2025-10-30)
#     ✅ 주석·docstring 표준화 (SSOT 규격)
#     ✅ _to_csv / validate_header 등 확장 준비 추가
#     ✅ from_attributes 설정 유지 (Pydantic v2 호환)
# ============================================================================

from typing import Iterable, Dict, Any, Tuple, List
from pydantic import BaseModel, Field


# ============================================================================
# 1️⃣ CanonRecord — 병합 엔진 표준 데이터 단위
# ----------------------------------------------------------------------------
class CanonRecord(BaseModel):
    """
    CanonRecord
    ────────────────────────────────────────────────
    CSV → Dict → Pydantic → Merge Engine 으로 전달되는 표준 단위 레코드

    필드:
      • business_date : 업무 일자 (YYYY-MM-DD)
      • property_code : 호텔 코드 (예: MOP)
      • payload       : 원본 CSV의 파싱 결과(dict)
      • key_tuple     : 고유 키 필드 튜플 (dataset별 고유 식별자)
    """
    business_date: str = Field(..., description="YYYY-MM-DD")
    property_code: str = Field(..., description="호텔 코드")
    payload: Dict[str, Any] = Field(..., description="CSV에서 파싱된 데이터")
    key_tuple: Tuple[Any, ...] = Field(..., description="고유 키 튜플")

    class Config:
        from_attributes = True  # ORM/Pydantic 상호 변환 지원

    # ─────────────────────────────────────────────
    @classmethod
    def from_parsed(cls, data: Dict[str, Any], key_tuple: Tuple[Any, ...]) -> "CanonRecord":
        """
        dict → CanonRecord 안전 변환기
        (CSV → Dict → Pydantic 변환 시 필드 누락 방지)
        """
        return cls(
            business_date=data.get("business_date", ""),
            property_code=data.get("property_code", ""),
            payload=data,
            key_tuple=key_tuple,
        )


# ============================================================================
# 2️⃣ DatasetAdapter — 모든 어댑터의 공통 인터페이스
# ----------------------------------------------------------------------------
class DatasetAdapter:
    """
    DatasetAdapter (추상 베이스 클래스)
    ────────────────────────────────────────────────
    모든 어댑터는 이 클래스를 상속받아 구현해야 함.

    필수 구현 메서드:
      • normalize(raw_csv_text, fallback_business_date, property_code)
      • parse(canon_csv_text)
      • merge_mode(form)
    """

    dataset: str                      # 데이터셋 ID (예: "rooms_status")
    schema_model: BaseModel           # 각 행 검증용 Pydantic 스키마
    key_fields: Tuple[str, ...]       # 고유 키 필드 목록
    default_missing_policy: str = "soft_delete"

    # ─────────────────────────────────────────────
    def normalize(
        self, raw_csv_text: str, fallback_business_date: str, property_code: str
    ) -> str:
        """
        CSV 원본을 Canon 표준 포맷으로 변환.
        (헤더/필드 보정, BOM 제거, 필수 컬럼 주입)
        하위 클래스에서 반드시 구현해야 함.
        """
        raise NotImplementedError("normalize() must be implemented by subclass")

    # ─────────────────────────────────────────────
    def parse(self, canon_csv_text: str) -> Iterable[CanonRecord]:
        """
        Canon 표준 CSV를 CanonRecord 스트림으로 변환.
        (하위 클래스에서 반드시 구현)
        """
        raise NotImplementedError("parse() must be implemented by subclass")

    # ─────────────────────────────────────────────
    def merge_mode(self, form: Dict[str, Any]) -> str:
        """
        병합 모드 결정:
          - source_kind, form.mode 기준으로 snapshot / append 판단
          - 일간(daily) → append
          - 주간/월간(full) → snapshot
        """
        mode = str(form.get("mode", "")).strip().lower()
        if mode in ("append", "snapshot"):
            return mode
        src = str(form.get("source_kind", "daily")).lower()
        if src in ("weekly", "monthly", "full"):
            return "snapshot"
        return "append"

    # ─────────────────────────────────────────────
    @staticmethod
    def _to_csv(headers: List[str], rows: List[Dict[str, Any]]) -> str:
        """
        내부 유틸 — Dict 리스트를 CSV 문자열로 변환.
        모든 어댑터에서 공통 사용 가능.
        """
        import csv
        from io import StringIO
        buf = StringIO()
        writer = csv.DictWriter(buf, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            writer.writerow({h: r.get(h, "") for h in headers})
        return buf.getvalue()

    # ─────────────────────────────────────────────
    @staticmethod
    def validate_header(reader_fieldnames: List[str], required: List[str]) -> None:
        """
        CSV 헤더 유효성 검증 헬퍼 (옵션)
        """
        missing = [h for h in required if h not in (reader_fieldnames or [])]
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")


# ============================================================================
# 3️⃣ Export
# ============================================================================
__all__ = ["CanonRecord", "DatasetAdapter"]
