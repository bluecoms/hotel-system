# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/db/session.py
# Version   : 2025-10-31 · v3.6 (SSOT Stable · Engine Safety)
# Purpose   : Database Engine / Session 설정 (SQLite + PostgreSQL 공용)
# ----------------------------------------------------------------------------
# 변경 요약:
#   ✅ SQLite WAL 모드 적용 (잠금 최소화)
#   ✅ pool_pre_ping=True 로 연결 안정성 강화
#   ✅ Engine / Session 생성부 주석·타입 명시
# ============================================================================

from __future__ import annotations
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.settings import settings

# ─────────────────────────────────────────────
# DB Engine 생성
# ─────────────────────────────────────────────
if settings.APP_DB_URL.startswith("sqlite:"):
    # ✅ SQLite 특화 설정
    engine = create_engine(
        settings.APP_DB_URL,
        connect_args={
            "check_same_thread": False,
            "timeout": 30,  # 잠금 대기시간 보강
        },
        pool_pre_ping=True,
        future=True,
    )

    # WAL 모드 설정 (병행 읽기 성능 개선)
    with engine.connect() as conn:
        try:
            conn.execute(text("PRAGMA journal_mode=WAL;"))
            conn.commit()
        except Exception:
            pass

else:
    # ✅ 일반 DB (PostgreSQL 등)
    engine = create_engine(
        settings.APP_DB_URL,
        pool_pre_ping=True,
        future=True,
    )

# ─────────────────────────────────────────────
# Session 설정
# ─────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True,
)

# ─────────────────────────────────────────────
# 의존성 주입용 세션
# ─────────────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    """
    요청 단위 DB 세션 의존성 주입용.
    FastAPI 라우터에서 Depends(get_db)로 사용.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ─────────────────────────────────────────────
# 유틸: SQLite 여부 판별
# ─────────────────────────────────────────────
def is_sqlite() -> bool:
    """현재 연결된 데이터베이스가 SQLite인지 여부 반환."""
    return settings.APP_DB_URL.startswith("sqlite:")
