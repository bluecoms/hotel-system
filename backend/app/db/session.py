# app/db/session.py
# -*- coding: utf-8 -*-
"""
DB Session / Engine 설정 (Phase 3 안정화판)
──────────────────────────────────────────────
- SQLite timeout 보강 (database is locked 대응)
- SQLAlchemy future 모드 유지
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.settings import settings

# ──────────────────────────────────────────────
# 데이터베이스 엔진 및 세션 설정
# ──────────────────────────────────────────────
if settings.APP_DB_URL.startswith("sqlite:"):
    # SQLite 특화: 쓰기 충돌 방지(timeout=30)
    engine = create_engine(
        settings.APP_DB_URL,
        connect_args={"check_same_thread": False, "timeout": 30},
        future=True,
    )
else:
    # 일반 DB (PostgreSQL 등)
    engine = create_engine(settings.APP_DB_URL, future=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


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


# ──────────────────────────────────────────────
# 유틸: SQLite 여부 판별
# ──────────────────────────────────────────────
def is_sqlite() -> bool:
    """
    현재 연결된 데이터베이스가 SQLite인지 여부를 반환.
    main.py 등에서 환경 분기 시 사용.
    """
    return settings.APP_DB_URL.startswith("sqlite:")
