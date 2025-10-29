# -*- coding: utf-8 -*-
# =============================================================================
# File      : app/routers/__init__.py
# Version   : 2025.11-09 · v4.6 (SSOT Phase 4 Final · +RoomType/UnitRule Added)
# Purpose   : Hotel Admin — FastAPI Router Auto-Export (Unified Loader)
# -----------------------------------------------------------------------------
# 목적:
#   • routers/*.py 내 router 객체를 자동 탐색 및 전역 등록
#   • ImportError 발생 시 skip 처리로 안전 초기화 지원
#   • FastAPI 앱에서 include_all_routers(app) 호출 시 전체 자동 include
# -----------------------------------------------------------------------------
# 주요 개선 (v4.6):
#   ✅ 하우스키핑( /api/housekeeping ) 정식 통합 (housekeeping_task → housekeeping)
#   ✅ 객실타입 / 하우스키핑 유닛규칙 라우터 추가
#   ✅ DeptAccess 구조 유지 (RoleAccess 완전 제거)
#   ✅ master_ota_channels 중복 로드 방지 유지
#   ✅ 순환참조 및 로드 순서 안정화
# -----------------------------------------------------------------------------
# 참고:
#   • RoleAccess(User↔Role)는 완전히 폐기됨 → DeptAccess(roles_access.py) 사용.
#   • include_all_routers() 호출 시 모든 라우터가 단일 경로(/api/...)로 등록됨.
#   • Phase 4: RoomType + HK UnitRule 기준정보 라우터 추가됨.
# =============================================================================

import logging
import pkgutil
from importlib import import_module
from typing import Dict, Optional, List

__all__: List[str] = []
log = logging.getLogger("app.routers")

# ──────────────────────────────────────────────
# 1️⃣ 우선순위 라우터 정의 (핵심 경로 우선 로드)
# -----------------------------------------------------------------------------
# - 시스템 및 인증 관련 라우터를 먼저 로드
# - 이후 사용자/조직, 업로드/마감, OTA, 하우스키핑, 마스터 순서대로 구성
# ──────────────────────────────────────────────
_PREFERRED_MODULES: Dict[str, str] = {
    # 인증 / 시스템
    "auth": "auth",
    "health": "health",
    # "me": "me",   # ❌ 제거됨 (Phase 3 이후 폐기)

    # 사용자 / 조직 / 권한
    "users": "users",
    "employees": "employees",
    "roles": "roles",
    "roles_access": "roles_access",  # ✅ DeptAccess 기반 신규 권한 라우터
    "keywords": "keywords",

    # 인사 / HR / 계약
    "contracts": "contracts",
    "employee_files": "employee_files",
    "hr_bridge": "hr_bridge",

    # 업로드 / 마감 / OTA / 하우스키핑
    "upload": "upload",
    "closing": "closing",
    "ota": "ota",
    "housekeeping_task": "housekeeping",  # ✅ 모듈명=housekeeping_task, export명=housekeeping

    # 리포트 계열
    "reports": "reports",
    "reports_sales": "reports_sales",
    "reports_bank": "reports_bank",

    # ✅ 마스터 기준정보 (Phase 4 추가 완료)
    "master_departments": "master_departments",
    "master_ranks": "master_ranks",
    "master_empno_policy": "master_empno_policy",
    "master_salary_grade": "master_salary_grade",
    "master_property": "master_property",
    "master_bank": "master_bank",
    "master_hk_status": "master_hk_status",
    "master_room_type": "master_room_type",          # ✅ 객실타입 마스터 추가
    "master_hk_unit_rule": "master_hk_unit_rule",    # ✅ HK 유닛규칙 마스터 추가

    # 감사 / 회계 / 병합엔진 / 기타
    "audit": "audit",
    "bank": "bank",
    "merge": "merge",
    "debug": "debug",
}

# ──────────────────────────────────────────────
# 2️⃣ router 안전 로드 함수
# -----------------------------------------------------------------------------
# - 모듈 import 중 예외 발생 시 skip 처리
# - router 객체만 반환
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
# -----------------------------------------------------------------------------
# - _PREFERRED_MODULES 에 지정된 모듈을 순서대로 로드
# - 로드 성공 시 "[routers:init] loaded" 로그 출력
# ──────────────────────────────────────────────
for _mod, _export_name in _PREFERRED_MODULES.items():
    _r = _load_router(_mod)
    if _r is not None:
        globals()[_export_name] = _r
        __all__.append(_export_name)
        log.info(f"[routers:init] loaded: {_export_name:<24} prefix={getattr(_r, 'prefix', '')}")

# ──────────────────────────────────────────────
# 4️⃣ 나머지 자동 탐색 (Base, 내부 제외)
# -----------------------------------------------------------------------------
# - _PREFERRED_MODULES 에 없는 나머지 라우터 자동 등록
# - 중복/내부/폐기 라우터 제외
# ──────────────────────────────────────────────
_SKIP = {"me", "master_ota_channels", "user_roles"}  # ✅ 폐기 라우터 스킵

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
# -----------------------------------------------------------------------------
# - include_all_routers(app) 호출 시 전체 라우터 자동 include
# - 로드 순서 및 오류를 로그로 확인 가능
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
# -----------------------------------------------------------------------------
# - __all__ 중복 제거 및 순서 정리
# - import 순서 안정성 보장
# ──────────────────────────────────────────────
__all__ = list(dict.fromkeys(__all__))

# ============================================================================
# 참고:
#   • me, user_roles 라우터는 완전 제거됨.
#   • housekeeping 라우터(DeptAccess=HK)는 /api/housekeeping 으로 등록됨.
#   • master_room_type, master_hk_unit_rule 라우터가 추가되어
#     객실타입 및 유닛 계산 기준정보가 통합됨.
#   • roles_access 라우터(DeptAccess)는 SSOT 기준 권한 엔드포인트로 통합됨.
# ============================================================================
