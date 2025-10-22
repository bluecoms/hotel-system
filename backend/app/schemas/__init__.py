# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/schemas/__init__.py
# Version   : 2025.10-30 · v4.0 (SSOT Final Stable · Positions & Titles Sync)
# Purpose   : Hotel Admin — Pydantic Schemas Auto Import (Unified SSOT Loader)
# ----------------------------------------------------------------------------
# 목적:
#   • schemas/*.py 내 BaseModel 상속 클래스를 자동 탐색 및 전역 등록
#   • 주요 도메인(auth, users, employees, contracts, ota, reports 등) 우선 로드
#   • Master 기준정보 10개 도메인 통합:
#       departments / ranks / titles / positions / empno_policy /
#       salary_grade / property / bank / hk_status / ota_channel
# ----------------------------------------------------------------------------
# 운영 방침:
#   • OTA 수수료(commission)는 운영 데이터로 분리 (/api/ota/commissions)
#     → Master 계열(MasterOtaCommission)에서는 제외 (SSOT 원칙)
#   • 모든 BaseModel 스키마는 자동 탐색되어 FastAPI에서 전역 import 가능
# ----------------------------------------------------------------------------
# 변경 로그:
#   v3.4 (2025-10-23) ✅ MasterBank 추가 (7종 완성)
#   v3.5 (2025-10-25) ✅ MasterHkStatus 추가 (8종 완성)
#   v3.6 (2025-10-25) ✅ MasterOtaChannel 추가 (9종 완성)
#   v3.9 (2025-10-27) ✅ MasterOtaCommission 제거 (운영 라우트로 분리)
#   v4.0 (2025-10-30) ✅ MasterPosition + MasterTitle 확정 / Bank 확장 반영
# ============================================================================

import pkgutil
import sys
from importlib import import_module
from typing import Dict, List

# ──────────────────────────────────────────────
# 1️⃣ BaseModel 확보 (pydantic v1/v2 호환)
# ──────────────────────────────────────────────
try:
    from pydantic import BaseModel  # type: ignore
except Exception:  # fallback
    class BaseModel(object):
        pass

__all__: List[str] = []

# ──────────────────────────────────────────────
# 2️⃣ 명시 모듈 등록 (도메인별 우선순위)
# ──────────────────────────────────────────────
_MODULES: Dict[str, List[str]] = {
    # 인증 / 사용자
    "auth": ["ApproveBody", "UserCreate", "CreateFromEmpIn", "TokenPayload"],
    "users": ["UserOut", "UserIn", "UserListOut"],

    # 역할 / 권한 (DeptAccess 포함)
    "role": [
        "RoleIn",
        "RoleOut",
        "DeptAccessIn",
        "DeptAccessOut",
        "RoleWithAccessOut",
        "EffectiveAccessOut",
    ],

    # 인사 / 조직
    "employees": [
        "EmployeeIn",
        "EmployeeListOut",
        "EmployeeDetailOut",
        "EmployeeUpdate",
    ],

    # ✅ 기준정보 (Master Domains)
    "master_departments": [
        "MasterDepartmentIn",
        "MasterDepartmentOut",
        "MasterDepartmentOption",
        "MasterDepartmentReorderBody",
    ],
    "master_ranks": [
        "MasterRankIn",
        "MasterRankOut",
        "MasterRankReorderBody",
    ],
    "master_title": [
        "MasterTitleIn",
        "MasterTitleOut",
        "MasterTitleReorderBody",
    ],
    "master_position": [
        "MasterPositionIn",
        "MasterPositionOut",
        "MasterPositionReorderBody",
    ],
    "master_empno_policy": [
        "MasterEmpNoPolicyIn",
        "MasterEmpNoPolicyOut",
    ],
    "master_salary_grade": [
        "MasterSalaryGradeIn",
        "MasterSalaryGradeOut",
        "MasterSalaryGradeReorderBody",
    ],
    "master_property": [
        "MasterPropertyIn",
        "MasterPropertyOut",
    ],
    "master_bank": [
        "MasterBankIn",
        "MasterBankOut",
    ],
    "master_hk_status": [
        "MasterHkStatusIn",
        "MasterHkStatusOut",
    ],
    "master_ota_channel": [
        "MasterOtaChannelIn",
        "MasterOtaChannelOut",
    ],
    # NOTE: master_ota_commission 제거 — 운영 라우트(/api/ota/commissions)로 분리

    # ✅ HR / 계약
    "contract": [
        "ContractIn",
        "ContractOut",
        "ContractListOut",
        "ContractHistoryOut",
    ],

    # 영업마감 / 클로징
    "closing": [
        "DayStatusBody",
        "RestoreBody",
        "ClosingDay",
        "ClosingCalendarResp",
    ],

    # 키워드 / OTA (운영용)
    "keywords": ["KeywordIn", "KeywordOut"],
    "ota": [
        "OTAChannelCreate",
        "OTAChannelOut",
        "OTACommissionCreate",
        "OTACommissionUpdate",
        "OTACommissionOut",
        "OTAOrderOut",
        "OTASummaryItem",
        "OTASummaryOut",
    ],

    # 리포트
    "reports": ["PosItemRow", "SalesTagsOut", "DashboardKPIOut"],

    # 은행 / 회계 / 감사
    "bank": ["BankLedgerOut", "BankLedgerIn"],
    "audit": ["AuditLogOut", "AuditLogIn"],

    # 게시판 / 문서
    "board": ["BoardPostIn", "BoardPostOut", "BoardFileOut"],

    # 병합엔진
    "merge": [
        "MergeBatchBase",
        "MergeChangeLogBase",
        "MergeBatchWithChanges",
        "MergeDryRunResp",
        "MergeExecResp",
    ],

    # ✅ 업로드 (Upload / UploadedFile)
    "upload": [
        "UploadedFileOut",
        "UploadVersionList",
    ],
}

# ──────────────────────────────────────────────
# 3️⃣ 명시 모듈 우선 import
# ──────────────────────────────────────────────
def _import_symbols(module_name: str, symbols: List[str]) -> None:
    """명시된 모듈 내 스키마를 안전하게 import"""
    try:
        mod = import_module(f".{module_name}", __name__)
    except Exception as e:
        print(f"[schemas:init] skip {module_name}: {e}", file=sys.stderr)
        return

    for sym in symbols:
        obj = getattr(mod, sym, None)
        if obj is not None:
            globals()[sym] = obj
            if sym not in __all__:
                __all__.append(sym)
                print(f"[schemas:init] loaded: {module_name}.{sym}")


for _mod, _symbols in _MODULES.items():
    _import_symbols(_mod, _symbols)

# ──────────────────────────────────────────────
# 4️⃣ 나머지 자동 탐색 (BaseModel 상속 클래스)
# ──────────────────────────────────────────────
_specified = set(_MODULES.keys())

for _, name, ispkg in pkgutil.iter_modules(__path__):  # type: ignore[name-defined]
    if ispkg or name.startswith("_") or name in _specified:
        continue

    try:
        mod = import_module(f".{name}", __name__)
    except Exception as e:
        print(f"[schemas:auto] skip {name}: {e}", file=sys.stderr)
        continue

    for k, v in mod.__dict__.items():
        if k.startswith("_"):
            continue
        try:
            if isinstance(v, type) and issubclass(v, BaseModel) and v is not BaseModel:
                if k not in globals():
                    globals()[k] = v
                    __all__.append(k)
                    print(f"[schemas:auto] loaded: {name}.{k}")
        except Exception:
            continue

# ──────────────────────────────────────────────
# 5️⃣ 중복 제거 및 정렬
# ──────────────────────────────────────────────
__all__ = sorted(set(__all__))

# ============================================================================
# 참고:
#   • MasterPosition / MasterTitle / MasterBank / MasterOtaChannel 등
#     모든 기준정보 스키마가 본 모듈에 자동 등록됩니다.
#   • Alembic 및 FastAPI 실행 시 schemas 자동 탐색 로그 출력은 정상입니다.
# ============================================================================
