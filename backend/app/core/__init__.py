# ============================================================================
# File      : app/core/__init__.py
# Version   : 2025.10-31 · v3.2 (Clean Core · me_router 제거)
# Purpose   : Hotel Admin — Core Package Safe Export (Settings/Auth/I18N 등)
# ----------------------------------------------------------------------------
# 목적:
#   • app/core 하위 핵심 모듈(settings, auth, i18n 등)을 안전하게 통합 export
#   • ImportError 발생 시 조용히 무시하여 유연한 로드 보장
#   • 외부에서 app.core.* 사용 시 단일 진입점 역할 수행
# ----------------------------------------------------------------------------
# 운영 방침:
#   ✅ Python 3.8/3.9 호환 유지 (| None 금지, Optional 사용)
#   ✅ 존재하지 않는 모듈은 무시(테스트/개발단계 유연성 확보)
#   ✅ me_router 완전 폐기 (Phase 3 이후 불필요)
#   ✅ core 패키지 내 모든 모듈은 _MODULES 목록에서만 관리
# ----------------------------------------------------------------------------
# 변경 이력:
#   v3.0 · 2025-10-20  : Core Safe Export 구조 확립
#   v3.1 · 2025-10-27  : hashing / normalize_bank / payments 추가
#   v3.2 · 2025-10-31  : me_router 항목 완전 제거 (No module 에러 근본 해결)
# ============================================================================

from importlib import import_module

__all__ = []

# ─────────────────────────────────────────────
# 1️⃣ 핵심 모듈 목록 정의
# ─────────────────────────────────────────────
_MODULES = [
    "settings",
    "settings_merge",     # 정책 상수 / 병합 설정
    "auth",
    "locale",
    "i18n",
    "keywords",
    "audit",
    "snapshot",
    "employees_import",
    # "me_router",        # ❌ Phase 3 이후 제거됨 (불필요 라우터)
    "dev_bootstrap",
    "normalize",
    "normalize_bank",     # ✅ 은행데이터 정규화
    "payments",           # ✅ 결제 관련 유틸
    "hashing",            # ✅ 해싱 유틸
]

# ─────────────────────────────────────────────
# 2️⃣ 안전 import 함수
# ─────────────────────────────────────────────
def _safe_import(name: str):
    """core 내부 모듈을 안전하게 import/export"""
    try:
        mod = import_module(f".{name}", __name__)
        globals()[name] = mod
        __all__.append(name)
    except Exception:
        # 존재하지 않거나 import 실패해도 무시
        pass

# ─────────────────────────────────────────────
# 3️⃣ 루프 로드 및 export 정리
# ─────────────────────────────────────────────
for m in _MODULES:
    _safe_import(m)

__all__.sort()
