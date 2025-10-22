# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/db/session.py
# Version   : 2025-11-01 · v3.7 (SSOT Final Stable · Auto DB Guard)
# Purpose   : Hotel Admin — Database Engine / Session 설정 (SQLite & PostgreSQL 공용)
# ----------------------------------------------------------------------------
# 목적:
#   • DB 엔진/세션을 단일 진입점으로 통합 (SSOT)
#   • SQLite/외부DB(PostgreSQL 등) 모두 자동 감지 및 최적화 설정
# ----------------------------------------------------------------------------
# 주요 개선사항 (v3.7)
#   ✅ SQLite 파일 미존재 시 자동 생성 (settings.db_exists() 연계)
#   ✅ WAL 모드 + foreign_keys ON 활성화
#   ✅ pool_pre_ping + recycle 로 연결 안정성 향상
#   ✅ 세션 커밋 후 expire_on_commit=False 로 ORM 객체 재사용 안전화
#   ✅ PostgreSQL 등 외부 DB 완전 호환 (설정 자동 분기)
# ----------------------------------------------------------------------------
# 사용:
#   from app.db.session import get_db, engine
#   with engine.connect() as conn:
#       conn.execute(...)
# ============================================================================

from __future__ import annotations
from typing import Generator
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.settings import settings

# ============================================================================
# 1️⃣ DB Engine 생성
# ----------------------------------------------------------------------------
#  • SQLite → 경로 자동 생성 + WAL 모드
#  • PostgreSQL 등 → 표준 연결 (pool_pre_ping=True)
# ============================================================================
if settings.APP_DB_URL.startswith("sqlite:"):
    # ✅ SQLite: 경로 보장 (없으면 생성)
    db_path = settings.APP_DB_URL.replace("sqlite:///", "")
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    if not os.path.exists(db_path):
        open(db_path, "a").close()

    # ✅ Engine 생성
    engine = create_engine(
        settings.APP_DB_URL,
        connect_args={"check_same_thread": False, "timeout": 30},
        pool_pre_ping=True,
        pool_recycle=1800,
        future=True,
    )

    # ✅ SQLite 성능/무결성 설정 (WAL + FK)
    with engine.connect() as conn:
        try:
            conn.execute(text("PRAGMA journal_mode=WAL;"))
            conn.execute(text("PRAGMA foreign_keys=ON;"))
            conn.commit()
        except Exception as e:
            print(f"[DB] ⚠️ SQLite PRAGMA 설정 실패: {e}")

else:
    # ✅ 일반 DB (예: PostgreSQL, MySQL)
    engine = create_engine(
        settings.APP_DB_URL,
        pool_pre_ping=True,
        pool_recycle=1800,
        future=True,
    )

# ============================================================================
# 2️⃣ SessionLocal 설정
# ----------------------------------------------------------------------------
#  • expire_on_commit=False → 커밋 후에도 ORM 객체 속성 유지
#  • future=True → SQLAlchemy 2.x 스타일
# ============================================================================
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    future=True,
)

# ============================================================================
# 3️⃣ FastAPI 의존성 주입 세션
# ----------------------------------------------------------------------------
#  • 라우터에서 Depends(get_db) 형태로 사용
#  • 요청 단위로 세션 열고 자동 종료
# ============================================================================
def get_db() -> Generator[Session, None, None]:
    """
    요청 단위 DB 세션 생성기.
    FastAPI 라우터에서 Depends(get_db)로 주입하여 사용.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================================
# 4️⃣ SQLite 여부 헬퍼
# ----------------------------------------------------------------------------
#  • Alembic/DB 작업 시 분기용
# ============================================================================
def is_sqlite() -> bool:
    """현재 DB 엔진이 SQLite인지 여부 반환"""
    return settings.APP_DB_URL.startswith("sqlite:")

# ============================================================================
# 5️⃣ (선택) 단독 실행 테스트
# ----------------------------------------------------------------------------
#  • python app/db/session.py 실행 시 DB 연결 테스트 수행
# ============================================================================
if __name__ == "__main__":
    print(" DB URL:", settings.APP_DB_URL)
    print(" SQLite:", is_sqlite())
    print(" DB Exists:", settings.db_exists())
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            print(" DB 연결 성공:", result)
    except Exception as e:
        print(" DB 연결 실패:", e)
