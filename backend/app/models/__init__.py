# -*- coding: utf-8 -*-
# =============================================================================
# File      : app/models/__init__.py
# Version   : 2025.11-11 · v4.4 (Add HousekeepingAssignment · SSOT Final)
# Purpose   : Hotel Admin — SQLAlchemy Models Export (Unified ORM Loader)
# -----------------------------------------------------------------------------
# 주요 변경사항 (v4.4)
#   ✅ HousekeepingAssignment 추가 (정비 배정 기능)
#   ✅ 하우스키핑 도메인 완결: HousekeepingTask + HousekeepingAssignment
#   ✅ 기타 기존 구조/로직 유지
# =============================================================================

from importlib import import_module
from typing import Dict, List
import pkgutil
import warnings
import sys
from sqlalchemy import Table
from app.db.base_class import Base

warnings.filterwarnings("ignore", message="Table 'properties' is already defined")

__all__: List[str] = []
_registered_tables = set(Base.metadata.tables.keys())

# -----------------------------------------------------------------------------
# 1️⃣ 명시 등록 (우선 로드 대상)
# -----------------------------------------------------------------------------
_MODULES: Dict[str, List[str]] = {
    # 사용자 / 권한
    "role": ["Role"],
    "roles_access": ["DeptAccess"],

    # 인사 / 조직 / 계약
    "employee": ["Employee", "UserEmployeeMap"],
    "employee_file": ["EmployeeFile"],
    "contract": ["EmployeeContract"],

    # 기준정보 (Master Domains)
    "master_department": ["MasterDepartment"],
    "master_ranks": ["MasterRank"],
    "master_titles": ["MasterTitle"],
    "master_position": ["MasterPosition"],
    "master_empno_policy": ["MasterEmpNoPolicy"],
    "master_salary_grade": ["MasterSalaryGrade"],
    "master_property": ["MasterProperty"],
    "property": ["Property"],
    "master_bank": ["MasterBank"],
    "master_hk_status": ["MasterHkStatus"],
    "master_ota_channel": ["MasterOtaChannel"],
    "master_room_type": ["MasterRoomType"],
    "master_hk_unit_rule": ["MasterHkUnitRule"],

    # OTA / Keyword
    "keyword": ["Keyword"],
    "ota": ["OTAChannel", "OTACommission", "OTAOrder"],

    # 영업마감 / 업로드
    "closing": ["ClosingDay", "UploadSession", "UploadedFile"],

    # 병합엔진
    "merge": ["MergeBatch", "MergeChangeLog"],

    # 회계 / 은행
    "bank": ["BankAccount", "BankTxn", "BankDailyBalance"],

    # 감사 / 게시판
    "audit": ["AuditLog"],
    "board": ["BoardPost", "BoardFile", "BoardComment"],

    # ✅ 하우스키핑 도메인
    "housekeeping_task": ["HousekeepingTask"],
    "housekeeping_assignment": ["HousekeepingAssignment"],  # ✅ 추가됨
}

# -----------------------------------------------------------------------------
# 2️⃣ 안전 import 유틸
# -----------------------------------------------------------------------------
def _import_symbols(module_name: str, symbols: List[str]) -> None:
    full_mod = f".{module_name}"
    full_name = f"{__name__}.{module_name}"

    if full_name in sys.modules:
        return

    try:
        mod = import_module(full_mod, __name__)
    except Exception as e:
        print(f"[models:init] skip {module_name}: {e}")
        return

    for sym in symbols:
        obj = getattr(mod, sym, None)
        if obj is None:
            continue

        try:
            tablename = getattr(obj, "__tablename__", None)
            if tablename and tablename in _registered_tables:
                table: Table = Base.metadata.tables.get(tablename)
                if table is not None:
                    table.info["extend_existing"] = True
                    continue
            _registered_tables.add(tablename)
        except Exception:
            pass

        if sym not in globals():
            globals()[sym] = obj
            __all__.append(sym)
            print(f"[models:init] loaded: {module_name}.{sym}")

# -----------------------------------------------------------------------------
# 3️⃣ 명시 등록된 ORM 로드
# -----------------------------------------------------------------------------
for _mod, _symbols in _MODULES.items():
    _import_symbols(_mod, _symbols)

# -----------------------------------------------------------------------------
# 4️⃣ 자동 탐색 (미등록 모듈)
# -----------------------------------------------------------------------------
_specified = set(_MODULES.keys())

for _, name, ispkg in pkgutil.iter_modules(__path__):  # type: ignore[name-defined]
    if ispkg or name.startswith("_") or name in _specified or name in ("base", "mixins", "__init__"):
        continue

    try:
        mod = import_module(f".{name}", __name__)
    except Exception as e:
        print(f"[models:auto] skip {name}: {e}")
        continue

    for k, v in mod.__dict__.items():
        if k.startswith("_"):
            continue
        if isinstance(v, type) and hasattr(v, "__tablename__"):
            tablename = getattr(v, "__tablename__", None)
            if tablename and tablename in _registered_tables:
                continue
            _registered_tables.add(tablename)
            globals()[k] = v
            __all__.append(k)
            print(f"[models:auto] loaded: {name}.{k}")

# -----------------------------------------------------------------------------
# 5️⃣ Export 정리
# -----------------------------------------------------------------------------
__all__ = sorted(set(__all__))
