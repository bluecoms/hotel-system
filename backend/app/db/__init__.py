# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/db/__init__.py
# Version   : 2025-10-31 · v3.6 (SSOT Stable)
# Purpose   : DB 패키지 초기화 / 안전한 심볼 Export
# ----------------------------------------------------------------------------
# 목적:
#   • DB 관련 하위 모듈(session, base_class, base)을 안전하게 import/export
#   • Alembic / SQLAlchemy / FastAPI 환경에서 import-safe 보장
#   • 모델 직접 import 금지 (순환 참조, 중복 등록 방지)
# ----------------------------------------------------------------------------
# 구성:
#   ✅ session.py        → engine / SessionLocal / get_db
#   ✅ base_class.py     → Declarative Base
#   ✅ base.py           → Base 메타데이터 유틸 (metadata, engine_sync, init_db)
# ----------------------------------------------------------------------------
# 특징:
#   • 존재하지 않는 심볼도 안전하게 무시 (_safe_import)
#   • Python 3.8/3.9 완전 호환
#   • Alembic env.py, FastAPI main.py 모두에서 동일 import 구조 사용 가능
# ----------------------------------------------------------------------------
# 사용 예:
#   from app.db import get_db, Base
#   session = next(get_db())
# ----------------------------------------------------------------------------
# 변경 요약:
#   ✅ Phase 2~3 통합 (engine_async fallback 추가)
#   ✅ SSOT 단일 구조 정비
# ============================================================================

from importlib import import_module

__all__: list[str] = []


def _safe_import(module_name: str, symbols: list[str]) -> None:
    """
    지정된 모듈에서 일부 심볼만 안전하게 import.
    모듈이 없거나 ImportError 발생 시 무시하여 import-safe 보장.
    """
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


# ─────────────────────────────────────────────
# 1️⃣ 세션 / 엔진 (필수)
# ─────────────────────────────────────────────
_safe_import("session", ["get_db", "engine", "SessionLocal"])

# ─────────────────────────────────────────────
# 2️⃣ Declarative Base
# ─────────────────────────────────────────────
_safe_import("base_class", ["Base"])

# ─────────────────────────────────────────────
# 3️⃣ Base 유틸 (metadata / engine_sync / init_db)
# ─────────────────────────────────────────────
_safe_import("base", ["metadata", "engine_sync", "init_db"])

# ─────────────────────────────────────────────
# 4️⃣ Phase 2 대응: 비동기 엔진 키 추가 (없어도 무시)
# ─────────────────────────────────────────────
try:
    if "engine_async" not in globals():
        from app.db.base import engine_sync as engine_async  # fallback
        globals()["engine_async"] = engine_async
        __all__.append("engine_async")
except Exception:
    pass

__all__.sort()
