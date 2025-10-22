# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/main.py
# Version   : 2025.10-27 · v3.1 (Log Controls · Routers Debug Dump · SSOT)
# Purpose   : Hotel Admin — FastAPI Application Entry Point (Main App)
# ----------------------------------------------------------------------------
# 목적:
#   • FastAPI 진입점 — 라우터 자동로딩 / 중앙 로깅 / CORS / 부트스트랩 / 헬스체크
#   • 로그/가시성 제어(환경변수) + 라우터 디버그 덤프(옵션)
# ----------------------------------------------------------------------------
# 주요 기능:
#   ✅ 중앙 로깅(uvicorn.log + app_debug.log)
#   ✅ 라우터 자동 등록(include_all_routers)
#   ✅ CORS 정책(개발/운영 분리)
#   ✅ 병합엔진 로거/정책 출력
#   ✅ Validation 전역 처리
#   ✅ (신규) LOG_LEVEL / ROUTERS_DEBUG / ROUTERS_DUMP 환경변수 지원
# ----------------------------------------------------------------------------
# 운영 전환 시 변경 포인트 (⚙️):
#   ⚙️ allow_origins  → 실제 서비스 도메인만 남김
#   ⚙️ allow_headers  → ["Content-Type","X-Internal-Token","X-Debug-Role","Accept-Language","Authorization"]
#   ⚙️ allow_methods  → ["GET","POST","PUT","DELETE","OPTIONS"]
#   ⚙️ docs_url       → 운영에서는 None (API 문서 비공개)
#   ⚙️ LOG_LEVEL      → WARNING 이상 권장
# ----------------------------------------------------------------------------
# 연계:
#   • app/routers/__init__.py → include_all_routers(app)
#   • app/core/settings_merge.py → 정책 로그/머지 관리
#   • app/db/session.py → DB 세션 관리
#   • app/core/dev_bootstrap.py → Startup Hook 등록
# ============================================================================

import logging
import warnings
import os
from typing import List

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# ─────────────────────────────────────────────
# Core Imports
# ─────────────────────────────────────────────
from app.core.settings import settings
from app.core.i18n import t
from app.core.auth import router as auth_router
from app.core.dev_bootstrap import register_startup_hooks
from app.db.base import Base
from app.db.session import engine, is_sqlite
from app.routers import include_all_routers

# DEV 전용 라우터
try:
    from app.routers.debug import router as debug_router
except Exception:
    debug_router = None


# ─────────────────────────────────────────────
# 환경 변수 파서
# ─────────────────────────────────────────────
def _split_env(v: str) -> List[str]:
    """쉼표(,) 기준 문자열 분리"""
    return [s.strip() for s in v.split(",") if s.strip()]


# ─────────────────────────────────────────────
# CORS / 환경 설정
# ─────────────────────────────────────────────
ALLOWED_ORIGINS = _split_env(os.getenv("ALLOWED_ORIGINS", "")) or [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.0.6:5173",
    "http://192.168.0.6:8001",
    "https://hotel.mokpooceanhotel.co.kr",
]

IS_DEV = bool(getattr(settings, "DEBUG", False)) or str(
    getattr(settings, "APP_ENV", "")
).lower() in {"dev", "development", "local"}

# (신규) 로그/라우터 가시성 제어 환경변수
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()     # DEBUG/INFO/WARNING/ERROR/CRITICAL
ROUTERS_DEBUG = os.getenv("ROUTERS_DEBUG", "1") == "1" # 1이면 routers 스킵로그를 WARNING/DEBUG로 승격
ROUTERS_DUMP  = os.getenv("ROUTERS_DUMP", "1") == "1"  # 1이면 include 후 prefix/경로 요약 출력


# ─────────────────────────────────────────────
# 로깅 설정 (Centralized)
# ─────────────────────────────────────────────
log_dir = "/volume1/web/hotel-system/logs"
os.makedirs(log_dir, exist_ok=True)

# 포맷에 모듈/라인 포함(트러블슈팅 편의)
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(levelname)s - %(name)s:%(lineno)d - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"{log_dir}/uvicorn.log", encoding="utf-8"),
        logging.FileHandler("/volume1/web/hotel-system/backend/app_debug.log"),
    ],
)
log = logging.getLogger("app.main")

# 서브모듈 기본 레벨
logging.getLogger("merge_settings").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

# 라우터 로더 로거 — 디버그 토글로 제어
routers_logger = logging.getLogger("app.routers")
routers_logger.setLevel(logging.DEBUG if ROUTERS_DEBUG else logging.WARNING)


# ─────────────────────────────────────────────
# 경고 억제 (Pydantic / Deprecation)
# ─────────────────────────────────────────────
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message="Valid config keys have changed in V2")


# ─────────────────────────────────────────────
# FastAPI 앱 생성
# ─────────────────────────────────────────────
app = FastAPI(
    title="Hotel Admin API",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs" if IS_DEV else None,  # ⚙️ 운영 시 None
)


# ─────────────────────────────────────────────
# 병합엔진 설정 로거 초기화
# ─────────────────────────────────────────────
from app.core import settings_merge

settings_merge.setup_merge_logger()
settings_merge.show_policies()


# ─────────────────────────────────────────────
# CORS 설정 (개발용: 풀 오픈)
# ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # ⚙️ 운영 시 ["GET","POST","PUT","DELETE","OPTIONS"]
    allow_headers=["*"],  # ⚙️ 운영 시 명시 리스트로 축소
    expose_headers=["Content-Disposition"],
    max_age=600,
)


# ─────────────────────────────────────────────
# 라우터 등록
# ─────────────────────────────────────────────
app.include_router(auth_router)
include_all_routers(app)

if IS_DEV and debug_router is not None:
    app.include_router(debug_router)

# (신규) 라우트 요약 덤프 — 디버그 시에만 노출
if ROUTERS_DUMP:
    try:
        prefixes = []
        paths = []
        for r in app.routes:
            p = getattr(r, "path", "")
            if p:
                paths.append(p)
        # prefix 추정(대략적인 요약)
        for name in set(p.split("/", 3)[2] for p in paths if p.startswith("/api/")):
            prefixes.append(f"/api/{name}")
        log.warning("[routers] loaded prefixes → " + ", ".join(sorted(set(prefixes))))
        # 선택: ota 관련 경로 요약
        ota_paths = sorted({p for p in paths if "/ota" in p})
        if ota_paths:
            log.warning("[routers] ota paths → " + ", ".join(ota_paths))
    except Exception as _e:
        log.warning(f"[routers] dump failed: {_e}")


# ─────────────────────────────────────────────
# Startup Hook 등록
# ─────────────────────────────────────────────
register_startup_hooks(app, engine, Base, is_dev=IS_DEV)


# ─────────────────────────────────────────────
# Validation Error 핸들러
# ─────────────────────────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """전역 ValidationError 핸들러"""
    lang = getattr(request.state, "lang", "en")
    msg = t("error.validation", lang)
    try:
        errs = exc.errors() or []
        loc_str = " ".join(str(e.get("loc", "")) for e in errs).lower()
        if "rate" in loc_str:
            msg = t("error.rate_range", lang)
        elif "date" in loc_str and "range" in str(errs).lower():
            msg = t("error.date_invert", lang)
    except Exception:
        pass

    log.error(f"Validation error: {msg} - Details: {exc.errors()}")
    return JSONResponse(status_code=422, content={"detail": msg})


# ─────────────────────────────────────────────
# 헬스체크 엔드포인트
# ─────────────────────────────────────────────
@app.get("/api/health-check", tags=["system"])
def health_check():
    """기본 헬스체크"""
    return {
        "ok": True,
        "status": "running",
        "env": settings.APP_ENV,
        "version": "Phase 3 Stable Final",
        "log_level": LOG_LEVEL,
        "routers_debug": ROUTERS_DEBUG,
        "routers_dump": ROUTERS_DUMP,
    }
