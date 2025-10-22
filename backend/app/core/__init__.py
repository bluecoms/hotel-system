# -*- coding: utf-8 -*-
# Python 3.8/3.9 호환
"""
핵심 모듈(core) 안전 export
- 설정, 인증, 로케일 등 공용 유틸을 통합 import.
- ImportError 발생 시 조용히 무시.
- 외부에서 app.core.* 사용 시 안전하게 접근 가능.
"""

from importlib import import_module

__all__ = []

# 명시적으로 관리할 핵심 모듈 목록
_MODULES = [
    "settings",
    "settings_merge",     # ✅ Phase 2 정책 상수 예정
    "auth",
    "locale",
    "i18n",
    "keywords",
    "audit",
    "snapshot",
    "employees_import",
    "me_router",
    "dev_bootstrap",
    "normalize",
    "normalize_bank",     # ✅ 은행데이터 정규화 추가
    "payments",           # ✅ 결제 관련 유틸 추가
    "hashing",            # ✅ core.hashing (hash utils)
]

def _safe_import(name: str):
    """core 내부 모듈을 안전하게 import/export"""
    try:
        mod = import_module(f".{name}", __name__)
        globals()[name] = mod
        __all__.append(name)
    except Exception:
        # 존재하지 않거나 import 실패해도 무시
        pass

for m in _MODULES:
    _safe_import(m)

__all__.sort()
