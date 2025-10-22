# app/service/__init__.py
# -*- coding: utf-8 -*-
# Python 3.8/3.9 호환
"""
서비스 계층 자동 export (SSOT Phase 2 안정판)
──────────────────────────────────────────────
- routers에서 직접 import 가능한 서비스만 노출
- ImportError 발생 시 무시 (안전)
- Phase 2: merge_service 중심 구조
"""

from importlib import import_module
from typing import Dict, List
import pkgutil
import logging

__all__: List[str] = []
log = logging.getLogger("app.services")

# ────────────────────────────────
# 1️⃣ 명시 등록 (우선순위)
# ────────────────────────────────
_MODULES: Dict[str, List[str]] = {
    "merge_service": ["MergeService"],
    "upload_service": ["UploadService"],
    "upload_apply": ["UploadApplyService"],
}

def _safe_import(module_name: str, symbols: List[str]) -> None:
    """모듈에서 지정 심볼만 안전하게 import"""
    try:
        mod = import_module(f".{module_name}", __name__)
    except Exception as e:
        log.debug(f"[services] skip {module_name}: {e}")
        return
    for sym in symbols:
        obj = getattr(mod, sym, None)
        if obj:
            globals()[sym] = obj
            __all__.append(sym)

for _mod, _symbols in _MODULES.items():
    _safe_import(_mod, _symbols)

# ────────────────────────────────
# 2️⃣ 자동 탐색 (BaseService 상속 검색)
# ────────────────────────────────
_specified = set(_MODULES.keys())

for _, name, ispkg in pkgutil.iter_modules(__path__):  # type: ignore[name-defined]
    if ispkg or name.startswith("_") or name in _specified:
        continue
    try:
        mod = import_module(f".{name}", __name__)
    except Exception:
        continue

    for k, v in mod.__dict__.items():
        if k.startswith("_"):
            continue
        try:
            if isinstance(v, type) and "Service" in k:
                globals()[k] = v
                if k not in __all__:
                    __all__.append(k)
        except Exception:
            continue

__all__.sort()
