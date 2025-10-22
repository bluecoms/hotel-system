# ============================================================================
# File      : app/routers/__init__.py
# Version   : 2025.10-31 · v4.3 (OTA Dup Fix · SSOT Final Stable)
# Purpose   : Hotel Admin — FastAPI Router Auto-Export (Unified Loader)
# ----------------------------------------------------------------------------
# 목적:
#   • routers/*.py 내 router 객체를 자동 탐색 및 전역 등록
#   • ImportError 발생 시 skip 처리로 안전 초기화 지원
#   • FastAPI 앱에서 include_all_routers(app) 호출 시 전체 자동 include
# ----------------------------------------------------------------------------
# 개선 사항 (v4.3)
#   ✅ me 라우터 완전 제거 (Phase 3 이후 불필요 기능)
#   ✅ master_ota_channels 중복 로드 방지 (prefix 중복 근본 해결)
#   ✅ 순환참조 및 로드 순서 안정화
# ============================================================================
import logging
import pkgutil
from importlib import import_module
from typing import Dict, Optional, List

__all__: List[str] = []
log = logging.getLogger("app.routers")

# ──────────────────────────────────────────────
# 1️⃣ 우선순위 라우터 정의 (필수 항목만 명시)
# ──────────────────────────────────────────────
_PREFERRED_MODULES: Dict[str, str] = {
    # 인증 / 시스템
    "auth": "auth",
    "health": "health",
    "menu": "menu",
    # "me": "me",   # ❌ 제거됨 (Phase 3 이후 폐기)

    # 사용자 / 조직 / 권한
    "users": "users",
    "employees": "employees",
    "user_roles": "user_roles",
    "roles": "roles",
    "keywords": "keywords",

    # 인사 / HR / 계약
    "contracts": "contracts",
    "employee_files": "employee_files",
    "hr_bridge": "hr_bridge",

    # 업로드 / 마감 / OTA
    "upload": "upload",
    "closing": "closing",
    "ota": "ota",
    # ⚠️ master_ota_channels 는 자동탐색 전용 (여기 명시 금지)

    # 리포트 계열
    "reports": "reports",
    "reports_sales": "reports_sales",
    "reports_bank": "reports_bank",

    # ✅ 마스터 핵심만 명시 (나머지는 자동탐색)
    "master_departments": "master_departments",
    "master_ranks": "master_ranks",
    "master_empno_policy": "master_empno_policy",
    "master_salary_grade": "master_salary_grade",
    "master_property": "master_property",
    "master_bank": "master_bank",
    "master_hk_status": "master_hk_status",

    # 감사 / 회계 / 병합엔진 / 기타
    "audit": "audit",
    "bank": "bank",
    "merge": "merge",
    "debug": "debug",
}

# ──────────────────────────────────────────────
# 2️⃣ router 안전 로드 함수
# ──────────────────────────────────────────────
def _load_router(modname: str) -> Optional[object]:
    """routers.<modname> 에서 router 객체를 안전하게 로드"""
    try:
        mod = import_module(f".{modname}", __name__)
    except Exception as e:
        if modname == "me":
            log.debug(f"[routers:init] skip {modname}: intentionally removed")
        else:
            log.warning(f"[routers:init] skip {modname}: {e}")
        return None
    return getattr(mod, "router", None)

# ──────────────────────────────────────────────
# 3️⃣ 명시 등록된 라우터 우선 로드
# ──────────────────────────────────────────────
for _mod, _export_name in _PREFERRED_MODULES.items():
    _r = _load_router(_mod)
    if _r is not None:
        globals()[_export_name] = _r
        __all__.append(_export_name)
        log.info(f"[routers:init] loaded: {_export_name:<24} prefix={getattr(_r, 'prefix', '')}")

# ──────────────────────────────────────────────
# 4️⃣ 나머지 자동 탐색 (Base, 내부 제외)
# ──────────────────────────────────────────────
_SKIP = {"me", "master_ota_channels"}  # ✅ 중복 로드 방지 대상 추가

for _, name, _ in pkgutil.iter_modules(__path__):  # type: ignore[name-defined]
    if name.startswith("_") or name in _PREFERRED_MODULES or name in _SKIP:
        continue
    _r = _load_router(name)
    if _r is not None:
        globals()[name] = _r
        __all__.append(name)
        log.info(f"[routers:auto] loaded: {name:<24} prefix={getattr(_r, 'prefix', '')}")

# ──────────────────────────────────────────────
# 5️⃣ FastAPI 앱에 일괄 include
# ──────────────────────────────────────────────
def include_all_routers(app):
    """FastAPI 앱에 모든 라우터를 순서대로 include (SSOT 기준 순서 보장)"""
    ok, fail = 0, 0
    for name in __all__:
        router = globals().get(name)
        if not router:
            continue
        try:
            app.include_router(router)
            ok += 1
            prefix = getattr(router, "prefix", "")
            log.info(f"[routers] include OK: {name:<24} {prefix}")
        except Exception as e:
            fail += 1
            log.warning(f"[routers] include FAIL: {name:<24} → {e}")
    log.info(f"[routers] Routers Loaded — OK={ok}, FAIL={fail}, TOTAL={ok + fail}")

# ──────────────────────────────────────────────
# 6️⃣ export 정리
# ──────────────────────────────────────────────
__all__ = list(dict.fromkeys(__all__))

# ============================================================================
# 참고:
#   • me 라우터는 완전 제거, master_ota_channels 는 중복 방지를 위해 자동탐색 스킵.
#   • include_all_routers() 호출 시 모든 라우터가 단일 경로(/api/...)로만 등록됨.
# ============================================================================
