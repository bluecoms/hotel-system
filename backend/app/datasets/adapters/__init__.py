# app/datasets/adapters/__init__.py
# -*- coding: utf-8 -*-
# version: 2025-10-11 Phase 2 (adapters registry full)
"""
Dataset Adapter 자동 export + Registry (SSOT Phase 2)
──────────────────────────────────────────────
- base.py: DatasetAdapter, CanonRecord
- 개별 어댑터 자동 탐색 → ADAPTERS 등록
- get_adapter(dataset)로 인스턴스 제공
- 구 명칭 호환: pay_settlement -> bank_ledger
"""

from importlib import import_module
from typing import Dict, List, Optional, Type
import pkgutil
import logging

from .base import DatasetAdapter, CanonRecord  # noqa

__all__: List[str] = ["DatasetAdapter", "CanonRecord", "ADAPTERS", "get_adapter"]
log = logging.getLogger("app.datasets.adapters")

# ─────────────────────────────────────────────
# 내부용 레지스트리
# ─────────────────────────────────────────────
_ADAPTER_CLASSES: Dict[str, Type[DatasetAdapter]] = {}   # 모듈 import → class 탐색용
ADAPTERS: Dict[str, Type[DatasetAdapter]] = {}           # 최종 외부 공개용

# ─────────────────────────────────────────────
# 구명칭/별칭 (레거시 호환)
# ─────────────────────────────────────────────
_SYNONYMS = {
    "pay_settlement": "bank_ledger",  # 과거 dataset 이름
    "rooms": "rooms_status",
}


# ─────────────────────────────────────────────
# 내부 헬퍼: 안전 import
# ─────────────────────────────────────────────
def _safe_import(module_name: str) -> Optional[object]:
    try:
        mod = import_module(f".{module_name}", __name__)
        return mod
    except Exception as e:
        log.debug(f"[adapters] skip {module_name}: {e}")
        return None


# ─────────────────────────────────────────────
# 내부 헬퍼: DatasetAdapter subclass 자동 등록
# ─────────────────────────────────────────────
def _register_from_module(mod: object) -> None:
    for k, v in mod.__dict__.items():
        if not isinstance(v, type):
            continue
        try:
            if issubclass(v, DatasetAdapter) and v is not DatasetAdapter:
                dataset = getattr(v, "dataset", None)
                if isinstance(dataset, str) and dataset.strip():
                    key = dataset.strip().lower()
                    _ADAPTER_CLASSES[key] = v
        except Exception:
            continue


# ─────────────────────────────────────────────
# 1) 핵심 어댑터 명시 로드
# ─────────────────────────────────────────────
_core_modules = (
    "base",
    "rooms_status",
    "sales_front",
    "fnb_tenders",
    "fnb_items",
    "expenses",
    "bank_ledger",
)

for name in _core_modules:
    mod = _safe_import(name)
    if mod:
        _register_from_module(mod)

# ─────────────────────────────────────────────
# 2) 나머지 자동 탐색 (추후 신규 모듈 자동 포함)
# ─────────────────────────────────────────────
for _, name, ispkg in pkgutil.iter_modules(__path__):  # type: ignore[name-defined]
    if ispkg or name.startswith("_") or name in _core_modules or name in {"mixins", "__init__"}:
        continue
    mod = _safe_import(name)
    if mod:
        _register_from_module(mod)

# ─────────────────────────────────────────────
# 3) 최종 ADAPTERS 레지스트리 구성
# ─────────────────────────────────────────────
for ds, cls in sorted(_ADAPTER_CLASSES.items()):
    ADAPTERS[ds] = cls

# ─────────────────────────────────────────────
# 4) 유틸: dataset 이름 해석 + Adapter 인스턴스 생성
# ─────────────────────────────────────────────
def _resolve_dataset_name(name: str) -> str:
    n = (name or "").strip().lower()
    return _SYNONYMS.get(n, n)


def get_adapter(dataset: str) -> Optional[DatasetAdapter]:
    """
    dataset 이름으로 어댑터 인스턴스 반환.
    - 존재하지 않으면 None
    - 구 명칭(pay_settlement 등)도 자동 매핑
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


# ─────────────────────────────────────────────
# 5) 로드 완료 로그
# ─────────────────────────────────────────────
try:
    from pprint import pformat
    log.info("[adapters] loaded datasets: %s", pformat(list(ADAPTERS.keys())))
except Exception:
    pass
