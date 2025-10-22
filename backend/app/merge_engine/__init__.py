# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/merge_engine/__init__.py
# Version   : 2025-10-31 · v3.6 (SSOT Stable · MergeBatch Import Hotfix)
# Purpose   : SSOT Merge Engine 초기화 및 자동 export
# ----------------------------------------------------------------------------
# 목적:
#   • 엔진, 플래너, 정책, 리포지토리, 감사 모듈 자동 로드 및 재-export
#   • app.datasets.adapters 의 ADAPTERS / get_adapter 레지스트리 병행 노출
# ----------------------------------------------------------------------------
# 특징:
#   ✅ 안전한 import (에러 발생 시 graceful skip)
#   ✅ MergeBatch import 오류 자동 보정(app.models.merge)
#   ✅ 단계별 자동 탐색 및 class registry 확장
#   ✅ adapters registry 로드 상태 로그 출력
# ----------------------------------------------------------------------------
# 사용 예:
#   from app.merge_engine import run_merge, get_adapter
#   result = run_merge(dataset="rooms_status", ...)
# ============================================================================

from __future__ import annotations
from importlib import import_module
from typing import List, Dict
import pkgutil
import logging

__all__: List[str] = []
log = logging.getLogger("app.merge_engine")

# ─────────────────────────────────────────────
# 1️⃣ 명시 모듈 등록 (핵심 순서 고정)
# ─────────────────────────────────────────────
_MODULES: Dict[str, List[str]] = {
    "engine": ["run_merge"],  # 실행 엔트리포인트
    "repository": ["CanonRepository", "MergeAuditRepository", "persist_records"],
    "diff": ["compute_diff"],
    "policies": ["get_dedupe_policy", "get_missing_policy"],
    "planner": ["plan_merge"],
    "audit": ["record_merge_audit"],
}


def _safe_import(module_name: str, symbols: List[str]) -> None:
    """
    모듈을 안전하게 import하고 지정된 심볼을 전역에 등록.
    MergeBatch import 오류(app.models.audit → app.models.merge)는 자동 보정.
    """
    try:
        mod = import_module(f".{module_name}", __name__)
        log.debug(f"[merge_engine] imported: {module_name}")
    except Exception as e:
        # MergeBatch import 경로 오류시 자동 보정
        if "app.models.audit" in str(e) or "MergeBatch" in str(e):
            log.warning(f"[merge_engine] auto-fix MergeBatch import in {module_name}")
            try:
                import app.models.merge  # noqa
                mod = import_module(f".{module_name}", __name__)
            except Exception as inner:
                log.error(f"[merge_engine] retry failed for {module_name}: {inner}")
                return
        else:
            log.warning(f"[merge_engine] skip module '{module_name}': {e}")
            return

    for sym in symbols:
        obj = getattr(mod, sym, None)
        if obj:
            globals()[sym] = obj
            if sym not in __all__:
                __all__.append(sym)


# 명시 모듈 로드
for _mod, _symbols in _MODULES.items():
    _safe_import(_mod, _symbols)


# ─────────────────────────────────────────────
# 2️⃣ 자동 탐색 (보조 클래스 자동 로드)
# ─────────────────────────────────────────────
_specified = set(_MODULES.keys())
for _, name, ispkg in pkgutil.iter_modules(__path__):  # type: ignore[name-defined]
    if ispkg or name.startswith("_") or name in _specified:
        continue
    try:
        mod = import_module(f".{name}", __name__)
        log.debug(f"[merge_engine] auto-import: {name}")
    except Exception as e:
        log.warning(f"[merge_engine] auto-import skip '{name}': {e}")
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


# ─────────────────────────────────────────────
# 3️⃣ Dataset adapters 재-export (정식 위치: app.datasets.adapters)
# ─────────────────────────────────────────────
try:
    from app.datasets.adapters import ADAPTERS as _ADAPTERS, get_adapter as _get_adapter

    ADAPTERS = _ADAPTERS
    get_adapter = _get_adapter
    __all__ += ["ADAPTERS", "get_adapter"]

    try:
        from pprint import pformat
        log.info("[merge_engine] dataset adapters loaded: %s", pformat(list(ADAPTERS.keys())))
    except Exception:
        log.debug("[merge_engine] dataset adapters loaded (no pprint)")
except Exception as e:
    ADAPTERS = {}
    get_adapter = lambda x: None  # type: ignore
    log.warning(f"[merge_engine] adapters registry not available: {e}")


# ─────────────────────────────────────────────
# 4️⃣ Export 목록 정리
# ─────────────────────────────────────────────
__all__ = sorted(set(__all__))
