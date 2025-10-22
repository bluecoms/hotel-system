# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/datasets/adapters/__init__.py
# Version   : 2025.10-30 · v3.5 (SSOT Final Stable · Banking/OTA Sync)
# Purpose   : Hotel Admin — Dataset Adapter Registry (어댑터 통합 레지스트리)
# ----------------------------------------------------------------------------
# 목적:
#   • 모든 DatasetAdapter 하위 클래스를 자동 탐색/등록
#   • dataset 이름으로 Adapter 인스턴스를 안전하게 반환(get_adapter)
#   • SSOT Merge Engine / Upload 엔진에서 표준 어댑터 진입점 제공
# ----------------------------------------------------------------------------
# 구조:
#   1️⃣ BaseAdapter + CanonRecord 재노출
#   2️⃣ _core_modules (핵심 어댑터 명시 로드)
#   3️⃣ pkgutil 통한 신규 자동 탐색
#   4️⃣ Synonym 해석(pay_settlement→bank_ledger 등)
#   5️⃣ Adapter 인스턴스 팩토리(get_adapter)
# ----------------------------------------------------------------------------
# 변경 로그:
#   v3.5 (2025-10-30)
#     ✅ OTAOrdersAdapter 추가 등록 (/api/ota/orders 대응)
#     ✅ Synonym 확장: ota_commission → ota_orders
#     ✅ 로깅 포맷 개선 (INFO 레벨 명시)
#     ✅ Phase 3 SSOT 표준 주석 양식 적용
# ============================================================================
import pkgutil
import logging
from importlib import import_module
from typing import Dict, List, Optional, Type

from .base import DatasetAdapter, CanonRecord  # Core exports

__all__: List[str] = ["DatasetAdapter", "CanonRecord", "ADAPTERS", "get_adapter"]
log = logging.getLogger("app.datasets.adapters")

# ============================================================================
# 1️⃣ 내부 레지스트리
# ----------------------------------------------------------------------------
_ADAPTER_CLASSES: Dict[str, Type[DatasetAdapter]] = {}
ADAPTERS: Dict[str, Type[DatasetAdapter]] = {}

# ============================================================================
# 2️⃣ 구 명칭/별칭 (레거시 호환)
# ----------------------------------------------------------------------------
_SYNONYMS = {
    "pay_settlement": "bank_ledger",   # 과거 명칭
    "rooms": "rooms_status",           # 단축명
    "ota_commission": "ota_orders",    # OTA 커미션 → 주문데이터로 통합
}

# ============================================================================
# 3️⃣ 내부 유틸 — 안전 import / 등록
# ----------------------------------------------------------------------------
def _safe_import(module_name: str) -> Optional[object]:
    """어댑터 모듈을 안전하게 import (에러 무시)"""
    try:
        mod = import_module(f".{module_name}", __name__)
        return mod
    except Exception as e:
        log.debug(f"[adapters] skip {module_name}: {e}")
        return None


def _register_from_module(mod: object) -> None:
    """모듈 내 DatasetAdapter subclass 자동 탐색/등록"""
    for name, obj in mod.__dict__.items():
        if not isinstance(obj, type):
            continue
        try:
            if issubclass(obj, DatasetAdapter) and obj is not DatasetAdapter:
                dataset = getattr(obj, "dataset", None)
                if isinstance(dataset, str) and dataset.strip():
                    key = dataset.strip().lower()
                    _ADAPTER_CLASSES[key] = obj
                    log.info(f"[adapters] registered adapter: {key} -> {obj.__name__}")
        except Exception:
            continue

# ============================================================================
# 4️⃣ 핵심 어댑터 명시 로드
# ----------------------------------------------------------------------------
_core_modules = (
    "base",          # 기본 구조
    "rooms_status",  # 객실상태
    "sales_front",   # 전면매출
    "fnb_tenders",   # F&B 결제수단
    "fnb_items",     # F&B 품목
    "expenses",      # 지출
    "bank_ledger",   # 입출금장부
    "ota_orders",    # ✅ OTA 주문 (신규)
)

for name in _core_modules:
    mod = _safe_import(name)
    if mod:
        _register_from_module(mod)

# ============================================================================
# 5️⃣ 나머지 자동 탐색 (추가 어댑터 자동 포함)
# ----------------------------------------------------------------------------
for _, name, ispkg in pkgutil.iter_modules(__path__):  # type: ignore[name-defined]
    if (
        ispkg
        or name.startswith("_")
        or name in _core_modules
        or name in {"mixins", "__init__"}
    ):
        continue
    mod = _safe_import(name)
    if mod:
        _register_from_module(mod)

# ============================================================================
# 6️⃣ ADAPTERS 구성
# ----------------------------------------------------------------------------
for ds, cls in sorted(_ADAPTER_CLASSES.items()):
    ADAPTERS[ds] = cls

# ============================================================================
# 7️⃣ Adapter 이름 해석 + 인스턴스 반환
# ----------------------------------------------------------------------------
def _resolve_dataset_name(name: str) -> str:
    """dataset 이름 표준화 (synonym 매핑 포함)"""
    n = (name or "").strip().lower()
    return _SYNONYMS.get(n, n)


def get_adapter(dataset: str) -> Optional[DatasetAdapter]:
    """
    dataset 이름으로 Adapter 인스턴스 반환
    - 존재하지 않으면 None
    - 구 명칭(pay_settlement 등) 자동 매핑
    """
    ds = _resolve_dataset_name(dataset)
    cls = ADAPTERS.get(ds)
    if not cls:
        log.debug(f"[adapters] adapter not found for dataset={dataset}")
        return None
    try:
        return cls()
    except Exception as e:
        log.exception(f"[adapters] adapter init failed for {dataset}: {e}")
        return None

# ============================================================================
# 8️⃣ 로드 완료 로그
# ----------------------------------------------------------------------------
try:
    from pprint import pformat
    log.info("[adapters] loaded datasets: %s", pformat(sorted(ADAPTERS.keys())))
except Exception:
    pass
