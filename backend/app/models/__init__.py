# -*- coding: utf-8 -*-
# =============================================================================
# File      : app/models/__init__.py
# Version   : 2025.11-09 · v4.3 (SSOT Phase 4 Final · HK/RoomType Unified)
# Purpose   : Hotel Admin — SQLAlchemy Models Export (Unified ORM Loader)
# -----------------------------------------------------------------------------
# 목적:
#   • app/models/* 내 모든 ORM 클래스를 안전하게 통합 export
#   • Base → ORM import 순서 보장, Alembic 호환
#   • 중복 import / 중복 Table 등록 원천 차단
# -----------------------------------------------------------------------------
# 핵심 개선 (v4.3):
#   ✅ RoleAccess 완전 제거 → DeptAccess(roles_access.py) 로 통합
#   ✅ properties 테이블 extend_existing=True 자동 처리
#   ✅ 하우스키핑(HousekeepingTask) 모델 포함
#   ✅ 객실 타입/유닛 마스터 추가 (master_room_type, master_hk_unit_rule)
# -----------------------------------------------------------------------------
# 주의:
#   • Master 계열 12종 통합 유지 (Departments / Ranks / Titles / Positions 등)
#   • Base.metadata 는 app/db/base_class.py 단일 소스만 사용.
#   • Role/Access 는 Role + DeptAccess 조합만 유지.
#   • HousekeepingTask(하우스키핑 업무) 및 HK 유닛마스터 추가됨.
# =============================================================================

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
# -----------------------------------------------------------------------------
# - app/models/ 내 주요 ORM을 명시적으로 먼저 로드
# - Alembic과 FastAPI 부팅 시 import 순서 보장
# - Master 계열, Role/Access, Housekeeping 등 주요 도메인 지정
# ──────────────────────────────────────────────
_MODULES: Dict[str, List[str]] = {
    # 사용자 / 권한
    "role": ["Role"],                   # 사용자 역할
    "roles_access": ["DeptAccess"],     # 부서별 접근 권한 (RoleAccess 대체)

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
    "property": ["Property"],                    # ✅ 운영용 Property 모델
    "master_bank": ["MasterBank"],
    "master_hk_status": ["MasterHkStatus"],
    "master_ota_channel": ["MasterOtaChannel"],
    "master_room_type": ["MasterRoomType"],      # ✅ 객실 타입 마스터 추가
    "master_hk_unit_rule": ["MasterHkUnitRule"], # ✅ 하우스키핑 유닛 규칙 마스터 추가

    # OTA / Keyword
    "keyword": ["Keyword"],
    "ota": ["OTAChannel", "OTACommission", "OTAOrder"],

    # 영업마감 / 업로드
    "closing": ["ClosingDay", "UploadSession", "UploadedFile"],

    # 병합엔진 (SSOT Merge Engine)
    "merge": ["MergeBatch", "MergeChangeLog"],

    # 회계 / 은행
    "bank": ["BankAccount", "BankTxn", "BankDailyBalance"],

    # 감사 / 게시판 등
    "audit": ["AuditLog"],
    "board": ["BoardPost", "BoardFile", "BoardComment"],

    # ✅ 하우스키핑 (업무 도메인)
    "housekeeping_task": ["HousekeepingTask"],
}

# ──────────────────────────────────────────────
# 2️⃣ 안전 import 유틸
# -----------------------------------------------------------------------------
# - 지정된 모듈과 클래스(ORM)를 안전하게 import
# - 중복 테이블 등록을 방지하며 extend_existing 적용
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
# -----------------------------------------------------------------------------
# - 위에서 정의한 _MODULES 목록 순서대로 import 수행
# - 로드 성공 시 "[models:init] loaded: ..." 로그 출력
# ──────────────────────────────────────────────
for _mod, _symbols in _MODULES.items():
    _import_symbols(_mod, _symbols)

# ──────────────────────────────────────────────
# 4️⃣ 나머지 자동 탐색 (Base, mixins 제외)
# -----------------------------------------------------------------------------
# - app/models/ 내의 나머지 파일 자동 검색
# - _MODULES 에 명시되지 않은 파일만 추가 로드
# - 중복 테이블 방지
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
# 5️⃣ 정리 및 export 목록 구성
# -----------------------------------------------------------------------------
# - __all__ 정렬 및 중복 제거
# - Base.metadata 와 Alembic 호환 유지
# -----------------------------------------------------------------------------
__all__ = sorted(set(__all__))

# -----------------------------------------------------------------------------
# 참고:
#   • RoleAccess 는 DeptAccess 로 완전히 통합됨.
#   • HousekeepingTask, MasterRoomType, MasterHkUnitRule 가 추가되어
#     호텔 기준정보(객실 타입/유닛 계산 규칙)까지 완결.
#   • Base.metadata 는 app/db/base_class.py 단일 소스를 사용.
#   • extend_existing=True 로 중복 테이블 경고 없이 안정 로드.
#   • SSOT Phase 4 Final 버전 (2025-11-09)
# =============================================================================
