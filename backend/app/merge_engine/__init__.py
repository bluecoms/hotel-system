# app/merge_engine/__init__.py
# -*- coding: utf-8 -*-
# Python 3.8/3.9 호환
"""
Merge Engine 패키지 자동 export (SSOT Phase 2)
──────────────────────────────────────────────
- 엔진/리포지토리/정책/플래너/감사 모듈 자동 로드
- datasets.adapters 레지스트리(ADAPTERS, get_adapter) 재-export
"""

from importlib import import_module
from typing import List, Dict
import pkgutil
import logging

__all__: List[str] = []
log = logging.getLogger("app.merge_engine")

# ────────────────────────────────
# 1) 명시 등록 (우선순위 순서)
# ────────────────────────────────
_MODULES: Dict[str, List[str]] = {
    "engine": ["run_merge"],  # 실제 공개 함수
    "repository": ["CanonRepository", "MergeAuditRepository", "persist_records"],
    "diff": ["compute_diff"],
    "policies": ["get_dedupe_policy", "get_missing_policy"],
    "planner": ["plan_merge"],
    "audit": ["record_merge_audit"],
}

def _safe_import(module_name: str, symbols: List[str]) -> None:
    """모듈을 안전하게 import하고 필요한 심볼을 등록"""
    try:
        mod = import_module(f".{module_name}", __name__)
        log.debug(f"[merge_engine] imported: {module_name}")
    except Exception as e:
        log.debug(f"[merge_engine] skip {module_name}: {e}")
        return
    for sym in symbols:
        obj = getattr(mod, sym, None)
        if obj:
            globals()[sym] = obj
            if sym not in __all__:
                __all__.append(sym)

for _mod, _symbols in _MODULES.items():
    _safe_import(_mod, _symbols)

# ────────────────────────────────
# 2) 자동 탐색 (보조 클래스 자동 로드)
# ────────────────────────────────
_specified = set(_MODULES.keys())
for _, name, ispkg in pkgutil.iter_modules(__path__):  # type: ignore[name-defined]
    if ispkg or name.startswith("_") or name in _specified:
        continue
    try:
        mod = import_module(f".{name}", __name__)
        log.debug(f"[merge_engine] auto-import {name}")
    except Exception as e:
        log.debug(f"[merge_engine] skip {name}: {e}")
        continue
    for k, v in mod.__dict__.items():
        if k.startswith("_"):
            continue
        try:
            if isinstance(v, type) and ("Merge" in k or "Repository" in k or "Policy" in k):
                globals()[k] = v
                if k not in __all__:
                    __all__.append(k)
        except Exception:
            continue

# ────────────────────────────────
# 3) Dataset adapters 재-export (정식 위치: app.datasets.adapters)
# ────────────────────────────────
try:
    from app.datasets.adapters import ADAPTERS as _ADAPTERS, get_adapter as _get_adapter
    ADAPTERS = _ADAPTERS
    get_adapter = _get_adapter
    __all__ += ["ADAPTERS", "get_adapter"]

    try:
        from pprint import pformat
        log.info("[merge_engine] dataset adapters loaded: %s", pformat(list(ADAPTERS.keys())))
    except Exception:
        pass
except Exception as e:
    log.warning(f"[merge_engine] adapters registry not available: {e}")

# ────────────────────────────────
# 4) Export 정리
# ────────────────────────────────
__all__ = sorted(set(__all__))
