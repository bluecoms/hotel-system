# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/routers/master.py
# Version   : 2025.10-31 · v2.2 (Circular Safe · SSOT Stable)
# Purpose   : Hotel Admin — Master Router Hub (/api/master/*)
# ----------------------------------------------------------------------------
# 목적:
#   • Master 계열 10종 라우터 통합 include
#   • 개별 라우터 파일 분리(master_*.py) 구조 유지
#   • Circular Import 방지를 위해 importlib 기반 지연 로드 사용
# ----------------------------------------------------------------------------
# 통합 포함 대상:
#   departments, ranks, titles, positions, empno_policy, salary_grade,
#   property, bank, hk_status, ota_channel
# ============================================================================
from __future__ import annotations
from fastapi import APIRouter
from importlib import import_module
import logging

log = logging.getLogger("app.routers.master")

router = APIRouter(
    prefix="/api/master",
    tags=["master"],
)

# ─────────────────────────────────────────────
# 안전한 서브라우터 include 함수
# ─────────────────────────────────────────────
def _safe_include(subpath: str, prefix_note: str = ""):
    try:
        mod = import_module(f"app.routers.{subpath}")
        sub_router = getattr(mod, "router", None)
        if sub_router:
            router.include_router(sub_router)
            log.info(f"[master] include OK: {subpath:<30} → {getattr(sub_router, 'prefix', '')}")
        else:
            log.warning(f"[master] skip {subpath}: router not found")
    except Exception as e:
        log.warning(f"[master] skip {subpath}: {e}")

# ─────────────────────────────────────────────
# Master 계열 통합 include (10종)
# ─────────────────────────────────────────────
for _mod in [
    "master_departments",
    "master_ranks",
    "master_titles",
    "master_position",
    "master_empno_policy",
    "master_salary_grade",
    "master_property",
    "master_bank",
    "master_hk_status",
    "master_ota_channels",
]:
    _safe_include(_mod)
