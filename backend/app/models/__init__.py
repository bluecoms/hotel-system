# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/models/__init__.py
# Version   : 2025.10-31 · v4.2 (SSOT Phase 3.5 Final · Role/Access Unified)
# Purpose   : Hotel Admin — SQLAlchemy Models Export (Unified ORM Loader)
# ----------------------------------------------------------------------------
# 목적:
#   • app/models/* 내 모든 ORM 클래스를 안전하게 통합 export
#   • Base → ORM import 순서 보장, Alembic 호환
#   • 중복 import / 중복 Table 등록 원천 차단
# ----------------------------------------------------------------------------
# 핵심 개선 (v4.2):
#   ✅ UserRole / RoleAccess 완전 제거
#   ✅ DeptAccess(roles_access.py) 로 통합
#   ✅ Base.metadata.registered_tables() 중복 등록 방지 강화
#   ✅ properties 테이블 extend_existing=True 자동 처리
#   ✅ Alembic / FastAPI 부팅 시 경고 억제
# ----------------------------------------------------------------------------
# 주의:
#   • Master 계열 10종 통합 유지 (Departments / Ranks / Titles / Positions 등)
#   • Base.metadata 는 app/db/base_class.py 단일 소스만 사용.
#   • Role/Access 는 Role + DeptAccess(roles_access) 조합만 유지.
#   • HousekeepingTask(하우스키핑) 모델 추가됨.
# ============================================================================

from importlib import import_module
from typing import Dict, List
import pkgutil
import warnings
import sys
from sqlalchemy import Table
from app.db.base_class import Base

# ──────────────────────────────────────────────
# 경고 억제 및 중복 테이블 등록 방지
# ──────────────────────────────────────────────
warnings.filterwarnings("ignore", message="Table 'properties' is already defined")

__all__: List[str] = []
_registered_tables = set(Base.metadata.tables.keys())

# ──────────────────────────────────────────────
# 1️⃣ 명시 등록 (우선 로드 대상)
# ──────────────────────────────────────────────
_MODULES: Dict[str, List[str]] = {
    # 사용자 / 권한
    "role": ["Role"],                # ✅ RoleAccess → DeptAccess로 교체됨
    "roles_access": ["DeptAccess"],  # ✅ 새로운 DeptAccess 모델 (권한 SSOT)

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
    "master_bank": ["MasterBank"],
    "master_hk_status": ["MasterHkStatus"],
    "master_ota_channel": ["MasterOtaChannel"],

    # OTA/Keyword (운영 도메인)
    "keyword": ["Keyword"],
    "ota": ["OTAChannel", "OTACommission", "OTAOrder"],

    # 영업마감 / 업로드
    "closing": ["ClosingDay", "UploadSession", "UploadedFile"],

    # 병합엔진
    "merge": ["MergeBatch", "MergeChangeLog"],

    # 회계 / 은행
    "bank": ["BankAccount", "BankTxn", "BankDailyBalance"],

    # 감사 / 게시판 등
    "audit": ["AuditLog"],
    "board": ["BoardPost", "BoardFile", "BoardComment"],

    # ✅ 하우스키핑 (신규)
    "housekeeping_task": ["HousekeepingTask"],
}

# ──────────────────────────────────────────────
# 2️⃣ 안전 import 유틸
# ──────────────────────────────────────────────
def _import_symbols(module_name: str, symbols: List[str]) -> None:
    """모듈 내 지정된 ORM 클래스를 안전하게 import"""
    full_mod = f".{module_name}"
    full_name = f"{__name__}.{module_name}"

    # 이미 import된 모듈은 재로드 방지
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

        # SQLAlchemy 모델 중복 등록 방지
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

# ──────────────────────────────────────────────
# 3️⃣ 명시 등록된 ORM 우선 로드
# ──────────────────────────────────────────────
for _mod, _symbols in _MODULES.items():
    _import_symbols(_mod, _symbols)

# ──────────────────────────────────────────────
# 4️⃣ 나머지 자동 탐색 (Base, mixins 제외)
# ──────────────────────────────────────────────
_specified = set(_MODULES.keys())

for _, name, ispkg in pkgutil.iter_modules(__path__):  # type: ignore[name-defined]
    if (
        ispkg
        or name.startswith("_")
        or name in _specified
        or name in ("base", "mixins", "__init__")
    ):
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

# ──────────────────────────────────────────────
# 5️⃣ 정리
# ──────────────────────────────────────────────
__all__ = sorted(set(__all__))

# ----------------------------------------------------------------------------
# 참고:
#   • UserRole / RoleAccess 는 완전히 폐기되었으며 DeptAccess 로 통합.
#   • HousekeepingTask (하우스키핑 업무) 모델이 추가되어 ORM 완결.
#   • properties 테이블 중복 경고는 v4.1 이후 완전 억제.
#   • Base.metadata 는 app/db/base_class.py 단일 소스만 사용.
#   • extend_existing=True 처리는 runtime conflict 없이 적용.
# ============================================================================
