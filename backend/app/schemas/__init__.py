# -*- coding: utf-8 -*-
# =============================================================================
# File      : app/schemas/__init__.py
# Version   : 2025-11-11 · v4.4 (Add HousekeepingAssignment · SSOT Final)
# Purpose   : Hotel Admin — Pydantic Schemas Auto Import (Unified SSOT Loader)
# -----------------------------------------------------------------------------
# 주요 변경사항 (v4.4)
#   ✅ HousekeepingAssignment 스키마 추가
#   ✅ 하우스키핑 도메인 완결 (Task + Assignment)
#   ✅ 기존 구조 유지 (MasterRoomType/HkUnitRule 포함)
# =============================================================================

import pkgutil
import sys
from importlib import import_module
from typing import Dict, List

try:
    from pydantic import BaseModel  # type: ignore
except Exception:  # fallback
    class BaseModel(object):
        pass

__all__: List[str] = []

# -----------------------------------------------------------------------------
# 1️⃣ 명시 모듈 등록 (도메인별 우선순위)
# -----------------------------------------------------------------------------
_MODULES: Dict[str, List[str]] = {
    # 인증 / 사용자
    "auth": ["ApproveBody", "UserCreate", "CreateFromEmpIn", "TokenPayload"],

    # 역할 / 권한
    "role": [
        "RoleIn",
        "RoleOut",
        "DeptAccessIn",
        "DeptAccessOut",
        "RoleWithAccessOut",
        "EffectiveAccessOut",
    ],
    "roles_access": [
        "DeptAccessBase",
        "DeptAccessIn",
        "DeptAccessOut",
        "EffectiveDeptAccess",
    ],

    # 인사 / 조직
    "employees": [
        "EmployeeIn",
        "EmployeeListOut",
        "EmployeeDetailOut",
        "EmployeeUpdate",
    ],

    # ✅ 기준정보 (Master Domains)
    "master_department": [
        "MasterDepartmentIn",
        "MasterDepartmentOut",
        "MasterDepartmentOption",
        "MasterDepartmentReorderBody",
    ],
    "master_ranks": ["MasterRankIn", "MasterRankOut", "MasterRankReorderBody"],
    "master_title": ["MasterTitleIn", "MasterTitleOut", "MasterTitleReorderBody"],
    "master_position": ["MasterPositionIn", "MasterPositionOut", "MasterPositionReorderBody"],
    "master_empno_policy": ["MasterEmpNoPolicyIn", "MasterEmpNoPolicyOut"],
    "master_salary_grade": ["MasterSalaryGradeIn", "MasterSalaryGradeOut", "MasterSalaryGradeReorderBody"],
    "master_property": ["MasterPropertyIn", "MasterPropertyOut"],
    "master_bank": ["MasterBankIn", "MasterBankOut"],
    "master_hk_status": ["MasterHkStatusIn", "MasterHkStatusOut"],
    "master_ota_channel": ["MasterOtaChannelIn", "MasterOtaChannelOut"],
    "master_room_type": ["RoomTypeBase", "RoomTypeCreate", "RoomTypeUpdate", "RoomTypeOut"],
    "master_hk_unit_rule": ["HkUnitRuleBase", "HkUnitRuleCreate", "HkUnitRuleUpdate", "HkUnitRuleOut"],

    # ✅ HR / 계약
    "contract": ["ContractIn", "ContractOut", "ContractListOut", "ContractHistoryOut"],

    # ✅ 하우스키핑 (Housekeeping)
    "housekeeping_task": [
        "HousekeepingTaskBase",
        "HousekeepingTaskCreate",
        "HousekeepingTaskUpdate",
        "HousekeepingTaskOut",
        "HousekeepingStatsOut",
    ],
    # ✅ 추가: 하우스키핑 정비 배정 (Assignment)
    "housekeeping_assignment": [
        "AssignmentBase",
        "AssignmentCreate",
        "AssignmentUpdate",
        "AssignmentOut",
    ],

    # 클로징 / 리포트
    "closing": ["DayStatusBody", "RestoreBody", "ClosingDay", "ClosingCalendarResp"],
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
    "reports": ["PosItemRow", "SalesTagsOut", "DashboardKPIOut"],
    "bank": ["BankLedgerOut", "BankLedgerIn"],
    "audit": ["AuditLogOut", "AuditLogIn"],
    "board": ["BoardPostIn", "BoardPostOut", "BoardFileOut"],
    "merge": [
        "MergeBatchBase",
        "MergeChangeLogBase",
        "MergeBatchWithChanges",
        "MergeDryRunResp",
        "MergeExecResp",
    ],
    "upload": ["UploadedFileOut", "UploadVersionList"],
}

# -----------------------------------------------------------------------------
# 2️⃣ 명시 모듈 우선 import
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# 3️⃣ 자동 탐색 (BaseModel 상속 클래스)
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# 4️⃣ 중복 제거 및 정렬
# -----------------------------------------------------------------------------
__all__ = sorted(set(__all__))

# ============================================================================
# 참고:
#   • HousekeepingAssignment 추가로 정비 배정 기능까지 완결됨.
#   • HousekeepingTask + Assignment 스키마로 도메인 완성.
#   • RoomType / HkUnitRule 포함으로 기준정보 완결.
# ============================================================================
