# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/routers/__init__.py
# Version   : 2025.10-30 · v4.0 (SSOT Final Stable · Positions & Titles Sync)
# Purpose   : Hotel Admin — FastAPI Router Auto-Export (Unified Loader)
# ----------------------------------------------------------------------------
# 목적:
#   • routers/*.py 내 router 객체를 자동 탐색 및 전역 등록
#   • ImportError 발생 시 skip 처리로 안전 초기화 지원
#   • FastAPI 앱에서 include_all_routers(app) 호출 시 전체 자동 include
# ----------------------------------------------------------------------------
# 설계 원칙:
#   • 우선순위 로드 순서: auth → system → user/org → domain → reports → hr → master → etc
#   • HR 모듈(hr.py) 및 hr_bridge.py 포함
#   • Master 계열(10종) 라우터 통합 유지:
#       departments, ranks, titles, positions, empno_policy, salary_grade,
#       property, bank, hk_status, ota_channel
#   • ✅ DeptAccess(RoleAccess) + EmployeeContract(직원 계약) 구조 반영
# ----------------------------------------------------------------------------
# 운영 방침:
#   • OTA “수수료(commission)”는 운영 데이터로 분리됨 (/api/ota/commissions)
#     → Master 계열(MasterOtaCommission)에서는 제외 (SSOT 원칙)
#   • Base.metadata 및 router include 순서는 명시적 선언 우선
# ----------------------------------------------------------------------------
# 변경 로그:
#   v3.4 (2025-10-23) ✅ MasterBank 라우터 추가 (7종 완성)
#   v3.5 (2025-10-25) ✅ MasterHkStatus 추가 (8종 완성)
#   v3.6 (2025-10-25) ✅ MasterOtaChannel 추가 (9종 완성)
#   v3.9 (2025-10-28) ✅ MasterPosition 추가 (10종 완성)
#   v4.0 (2025-10-30) ✅ MasterTitle/Position 정식 확정 + SSOT 최종 통합판
# ============================================================================

import logging
import pkgutil
from importlib import import_module
from typing import Dict, Optional, List

__all__: List[str] = []
log = logging.getLogger("app.routers")

# ──────────────────────────────────────────────
# 1️⃣ 우선순위 라우터 정의 (명시 순서 보장)
# ──────────────────────────────────────────────
_PREFERRED_MODULES: Dict[str, str] = {
    # 인증 / 시스템
    "auth": "auth",
    "health": "health",
    "menu": "menu",
    "me": "me",

    # 사용자 / 조직 / 권한
    "users": "users",
    "employees": "employees",
    "user_roles": "user_roles",
    "roles": "roles",                  # ✅ DeptAccess + Role 관리 라우터
    "keywords": "keywords",

    # 인사 / HR / 계약
    "contracts": "contracts",          # ✅ 직원 계약 관리
    "employee_files": "employee_files",
    "hr_bridge": "hr_bridge",

    # 업로드 / 마감 / OTA
    "upload": "upload",
    "closing": "closing",
    "ota": "ota",

    # 리포트 계열
    "reports": "reports",
    "reports_sales": "reports_sales",
    "reports_bank": "reports_bank",

    # ✅ 마스터 계열 (기준정보 10종 완성)
    "master": "master",                         # 허브 라우터 (통합 include)
    "master_departments": "master_departments", # 부서
    "master_ranks": "master_ranks",             # 직급
    "master_titles": "master_titles",           # 직책
    "master_positions": "master_positions",     # 직위
    "master_empno_policy": "master_empno_policy",
    "master_salary_grade": "master_salary_grade",
    "master_property": "master_property",       # 지점(호텔)
    "master_bank": "master_bank",               # 은행코드
    "master_hk_status": "master_hk_status",     # 하우스키핑 상태 코드
    "master_ota_channel": "master_ota_channel", # OTA 채널 기준정보
    # NOTE: master_ota_commission 제거 — 운영 라우트(/api/ota/commissions)로 분리됨

    # 감사 / 회계 / 병합엔진 / 기타
    "audit": "audit",
    "bank": "bank",
    "merge": "merge",
    "debug": "debug",
}

# ──────────────────────────────────────────────
# 2️⃣ router 객체 안전 로드 함수
# ──────────────────────────────────────────────
def _load_router(modname: str) -> Optional[object]:
    """routers.<modname> 에서 router 객체를 안전하게 로드"""
    try:
        mod = import_module(f".{modname}", __name__)
    except Exception as e:
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
for _, name, _ in pkgutil.iter_modules(__path__):  # type: ignore[name-defined]
    if name.startswith("_") or name in _PREFERRED_MODULES:
        continue
    _r = _load_router(name)
    if _r is not None:
        globals()[name] = _r
        __all__.append(name)
        log.info(f"[routers:auto] loaded: {name:<24} prefix={getattr(_r, 'prefix', '')}")

# ──────────────────────────────────────────────
# 5️⃣ FastAPI 앱에 라우터 일괄 등록
# ──────────────────────────────────────────────
def include_all_routers(app):
    """
    FastAPI 앱에 모든 라우터를 순서대로 include
    (SSOT 기준 순서 보장: 인증 → 도메인 → 마스터 → 운영)
    """
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
#   • Master 계열 10종 라우터가 통합되어 /api/master/* 경로로 제공됩니다.
#   • Alembic 및 FastAPI 구동 시 [routers:init] 로그는 정상 초기화 메시지입니다.
# ============================================================================
