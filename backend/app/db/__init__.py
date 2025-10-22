# -*- coding: utf-8 -*-
# Python 3.8/3.9 호환
"""
DB 패키지 초기화 (Phase 2 SSOT 안정판)
──────────────────────────────────────────────
- 모델 import 절대 금지 (순환 참조 / 중복등록 방지)
- 필수 요소(SessionLocal, engine, get_db)만 안전하게 export
- Base, metadata, engine_* 등은 존재하지 않아도 안전 처리
- Alembic / SQLAlchemy 환경 모두에서 import-safe 보장
"""

from importlib import import_module

__all__ = []

def _safe_import(module_name: str, symbols: list):
    """특정 모듈에서 지정된 심볼만 안전하게 import"""
    try:
        mod = import_module(f".{module_name}", __name__)
    except Exception:
        return
    for sym in symbols:
        obj = getattr(mod, sym, None)
        if obj is not None:
            globals()[sym] = obj
            if sym not in __all__:
                __all__.append(sym)


# ──────────────────────────────────────────────
# 1️⃣ 세션/엔진 (필수)
_safe_import("session", ["get_db", "engine", "SessionLocal"])

# ──────────────────────────────────────────────
# 2️⃣ Declarative Base
_safe_import("base_class", ["Base"])

# ──────────────────────────────────────────────
# 3️⃣ Base 유틸 (metadata / engine_sync 등)
_safe_import("base", ["metadata", "engine_sync", "init_db"])

# ──────────────────────────────────────────────
# 4️⃣ Phase 2 대응: 비동기 엔진 대응키 추가 (없어도 무시)
try:
    if "engine_async" not in globals():
        from app.db.base import engine_sync as engine_async  # fallback
        globals()["engine_async"] = engine_async
        __all__.append("engine_async")
except Exception:
    pass

__all__.sort()
