# app/routers/health.py
# -*- coding: utf-8 -*-
"""
헬스체크 라우터
- /healthz           : 표준 헬스 체크 (토큰 불필요)
- /api/healthz       : /healthz와 동일 응답(호환용)
"""

from fastapi import APIRouter
from datetime import datetime, timezone
import os

router = APIRouter()

def _utcnow_iso() -> str:
    # RFC3339/ISO8601 UTC 타임스탬프
    return datetime.now(timezone.utc).isoformat()

def _env() -> str:
    # 실행 환경 (기본 dev)
    return os.getenv("APP_ENV", "dev")

def _commit() -> str:
    # 배포 커밋 해시(없으면 unknown)
    return os.getenv("GIT_COMMIT", "unknown")

@router.get("/healthz")
def healthz():
    return {
        "ok": True,
        "service": "pm-hub-be",
        "env": _env(),
        "commit": _commit(),
        "ts": _utcnow_iso(),
    }

# 호환 경로
@router.get("/api/healthz")
def api_healthz():
    return healthz()
