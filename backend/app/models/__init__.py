# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/models/__init__.py
# Version   : 2025.10-30 · v4.0 (SSOT Final Stable · Titles & Positions Integrated)
# Purpose   : Hotel Admin — SQLAlchemy Models Export (Unified ORM Loader)
# ----------------------------------------------------------------------------
# 목적:
#   • app/models/* 내 모든 ORM 클래스를 안전하게 통합 export
#   • 순환참조 없이 Base → ORM import 순서 보장 (Alembic 호환)
#   • Master 기준정보 10개 도메인 통합 유지:
#       departments / ranks / titles / positions / empno_policy /
#       salary_grade / property / bank / hk_status / ota_channel
# ----------------------------------------------------------------------------
# 운영 방침:
#   • OTA “수수료(commission)”는 운영 데이터로 분리 (/api/ota/commissions)
#     → Master 계열(MasterOtaCommission)에서 제외 (SSOT 원칙)
#   • Base.metadata 는 app/db/base_class.py 단일 소스만 사용.
#   • 각 모델은 Base 상속 후 이 init 모듈에서 일괄 로드하여 export.
# ----------------------------------------------------------------------------
# 변경 로그:
#   v3.4 (2025-10-23) ✅ MasterBank 모델 추가
#   v3.5 (2025-10-25) ✅ MasterHkStatus 모델 추가
#   v3.6 (2025-10-25) ✅ MasterOtaChannel 모델 추가
#   v3.8 (2025-10-27) ✅ MasterOtaCommission 제거 (운영 라우트로 분리)
#   v3.9 (2025-10-28) ✅ MasterPosition 신규 추가 / MasterBank 업그레이드
#   v4.0 (2025-10-30) ✅ MasterTitle 구조 확정 / 전체 SSOT Final 정비
# ----------------------------------------------------------------------------
# 참고:
#   • MasterTitle : 직책(Titles) 기준정보 (직원/계약 화면)
#   • MasterPosition : 직위(Position) 기준정보 (EmployeeForm v-select)
#   • MasterBank : 은행 코드 + 국가코드/메타 확장 (v3.9 반영)
#   • Base.metadata 에 이미 존재하는 테이블 extend_existing=True 는 정상 경고임.
# ============================================================================

from importlib import import_module
from typing import Dict, List
import pkgutil
import warnings

# ──────────────────────────────────────────────
# 경고 억제 (이미 정의된 테이블 관련 경고)
# ──────────────────────────────────────────────
warnings.filterwarnings("ignore", message="Table 'properties' is already defined")

__all__: List[str] = []

# ──────────────────────────────────────────────
# 1️⃣ 명시 등록 (우선 로드 대상)
# ──────────────────────────────────────────────
_MODULES: Dict[str, List[str]] = {
    # 사용자 / 권한
    "user": ["User"],
    "role": ["Role", "UserRole", "RoleAccess"],  # ✅ DeptAccess 구조 반영

    # 인사 / 조직 / 계약
    "employee": ["Employee", "UserEmployeeMap"],
    "employee_file": ["EmployeeFile"],
    "contract": ["EmployeeContract"],  # ✅ 직원 계약 (버저닝)

    # ✅ 기준정보 (Master Domains)
    "master_departments": ["MasterDepartment"],      # 부서
    "master_ranks": ["MasterRank"],                  # 직급
    "master_titles": ["MasterTitle"],                # 직책 (v4.0 확정)
    "master_positions": ["MasterPosition"],          # 직위
    "master_empno_policy": ["MasterEmpNoPolicy"],    # 사번 정책
    "master_salary_grade": ["MasterSalaryGrade"],    # 급여 등급
    "master_property": ["MasterProperty"],           # 지점(호텔)
    "master_bank": ["MasterBank"],                   # 은행 코드
    "master_hk_status": ["MasterHkStatus"],          # 하우스키핑 상태코드
    "master_ota_channel": ["MasterOtaChannel"],      # OTA 채널 기준정보
    # NOTE: MasterOtaCommission 제거 — 운영 라우트(/api/ota/commissions)로 분리

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
}

# ──────────────────────────────────────────────
# 2️⃣ 안전 import 유틸
# ──────────────────────────────────────────────
def _import_symbols(module_name: str, symbols: List[str]) -> None:
    """모듈 내 지정된 ORM 클래스를 안전하게 import"""
    try:
        mod = import_module(f".{module_name}", __name__)
    except Exception as e:
        print(f"[models:init] skip {module_name}: {e}")
        return

    for sym in symbols:
        obj = getattr(mod, sym, None)
        if obj is not None and sym not in globals():
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
        try:
            # SQLAlchemy Declarative 모델만 export 대상으로 등록
            if isinstance(v, type) and hasattr(v, "__tablename__"):
                if k not in globals():
                    globals()[k] = v
                    __all__.append(k)
                    print(f"[models:auto] loaded: {name}.{k}")
        except Exception:
            continue


# ──────────────────────────────────────────────
# 5️⃣ 중복 제거 및 정렬
# ──────────────────────────────────────────────
__all__ = sorted(set(__all__))

# ──────────────────────────────────────────────
# 참고:
#   • Alembic 실행 시 "Table 'properties' is already defined" 경고는 정상입니다.
#   • Master 계열이 자동 import되며 Base.metadata에 이미 등록된 테이블을
#     extend_existing=True 로 재등록할 때 발생합니다.
#   • 이는 DB 구조나 데이터에 영향을 주지 않습니다.
# ============================================================================
