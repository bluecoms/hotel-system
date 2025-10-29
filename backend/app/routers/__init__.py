# -*- coding: utf-8 -*-
# =============================================================================
# File      : app/routers/__init__.py
# Version   : 2025.11-11 · v4.7 (Add HousekeepingAssignment · SSOT Final)
# Purpose   : Hotel Admin — FastAPI Router Auto-Export (Unified Loader)
# -----------------------------------------------------------------------------
# 주요 변경사항 (v4.7)
#   ✅ housekeeping_assignment 라우터 추가 (/api/housekeeping/assignments)
#   ✅ 하우스키핑 도메인 완결 (업무/정비 배정)
#   ✅ 기존 구조/로깅 형식 유지
# =============================================================================

import logging
import pkgutil
from importlib import import_module
from typing import Dict, Optional, List

__all__: List[str] = []
log = logging.getLogger("app.routers")

# -----------------------------------------------------------------------------
# 1️⃣ 우선순위 라우터 정의
# -----------------------------------------------------------------------------
_PREFERRED_MODULES: Dict[str, str] = {
    # 인증 / 시스템
    "auth": "auth",
    "health": "health",

    # 사용자 / 조직 / 권한
    "users": "users",
    "employees": "employees",
    "roles": "roles",
    "roles_access": "roles_access",
    "keywords": "keywords",

    # 인사 / HR / 계약
    "contracts": "contracts",
    "employee_files": "employee_files",
    "hr_bridge": "hr_bridge",

    # 업로드 / 마감 / OTA / 하우스키핑
    "upload": "upload",
    "closing": "closing",
    "ota": "ota",
    "housekeeping_task": "housekeeping",                 # ✅ 하우스키핑 업무
    "housekeeping_assignment": "housekeeping_assignment", # ✅ 정비 배정 추가

    # 리포트
    "reports": "reports",
    "reports_sales": "reports_sales",
    "reports_bank": "reports_bank",

    # ✅ 마스터 기준정보
    "master_departments": "master_departments",
    "master_ranks": "master_ranks",
    "master_empno_policy": "master_empno_policy",
    "master_salary_grade": "master_salary_grade",
    "master_property": "master_property",
    "master_bank": "master_bank",
    "master_hk_status": "master_hk_status",
    "master_room_type": "master_room_type",
    "master_hk_unit_rule": "master_hk_unit_rule",

    # 감사 / 회계 / 병합엔진 / 기타
    "audit": "audit",
    "bank": "bank",
    "merge": "merge",
    "debug": "debug",
}

# -----------------------------------------------------------------------------
# 2️⃣ router 안전 로드 함수
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# 3️⃣ 명시 등록된 라우터 우선 로드
# -----------------------------------------------------------------------------
for _mod, _export_name in _PREFERRED_MODULES.items():
    _r = _load_router(_mod)
    if _r is not None:
        globals()[_export_name] = _r
        __all__.append(_export_name)
        log.info(f"[routers:init] loaded: {_export_name:<28} prefix={getattr(_r, 'prefix', '')}")

# -----------------------------------------------------------------------------
# 4️⃣ 나머지 자동 탐색 (Base, 내부 제외)
# -----------------------------------------------------------------------------
_SKIP = {"me", "master_ota_channels", "user_roles"}

for _, name, _ in pkgutil.iter_modules(__path__):  # type: ignore[name-defined]
    if name.startswith("_") or name in _PREFERRED_MODULES or name in _SKIP:
        continue
    _r = _load_router(name)
    if _r is not None:
        globals()[name] = _r
        __all__.append(name)
        log.info(f"[routers:auto] loaded: {name:<28} prefix={getattr(_r, 'prefix', '')}")

# -----------------------------------------------------------------------------
# 5️⃣ FastAPI 앱에 일괄 include
# -----------------------------------------------------------------------------
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
            log.info(f"[routers] include OK: {name:<28} {prefix}")
        except Exception as e:
            fail += 1
            log.warning(f"[routers] include FAIL: {name:<28} → {e}")
    log.info(f"[routers] Routers Loaded — OK={ok}, FAIL={fail}, TOTAL={ok + fail}")

# -----------------------------------------------------------------------------
# 6️⃣ export 정리
# -----------------------------------------------------------------------------
__all__ = list(dict.fromkeys(__all__))

# ============================================================================
# 참고:
#   • housekeeping_assignment 추가 → /api/housekeeping/assignments 라우터 등록
#   • 하우스키핑 도메인: Task + Assignment 두 가지로 분리 관리
#   • master_room_type, master_hk_unit_rule 포함 (운영기준 완성)
# ============================================================================
