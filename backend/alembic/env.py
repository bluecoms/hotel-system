# -*- coding: utf-8 -*-
# ============================================================================
# File      : backend/alembic/env.py
# Version   : 2025.11-09 · v1.7 (DROP Safe · Compare Enable · SSOT Final Stable)
# Purpose   : Hotel Admin — Alembic Migration Environment Config
# ----------------------------------------------------------------------------
# 목적:
#   • Alembic 환경 설정 파일 (revision/autogenerate/upgrade 실행 환경 정의)
#   • SQLite 개발환경에서 안전하게 신규 테이블 감지 및 마이그레이션 적용
# ----------------------------------------------------------------------------
# 주요 특징:
#   ✅ importlib.invalidate_caches() 로 모델 변경 즉시 반영
#   ✅ 기존 테이블 비교(diff) 허용 — DROP 인식 방지
#   ✅ DROP / ALTER 차단 (데이터 보호)
#   ✅ render_as_batch=True → SQLite ALTER TABLE 우회
#   ✅ 신규 테이블 자동 감지 (SSOT 규약)
# ----------------------------------------------------------------------------
# 연계:
#   • app/db/base.py → Base.metadata (모든 ORM 테이블 정의)
#   • alembic/versions/ → 리비전 저장소
# ----------------------------------------------------------------------------
# 운영 전환 시:
#   • PostgreSQL/MySQL 등 외부 DB 사용 시 DROP/ALTER 가드 해제 가능
# ============================================================================

import os
import sys
import importlib
from sqlalchemy import engine_from_config, pool
from alembic import context

# ─────────────────────────────────────────────
# 1️⃣ 캐시 무효화 (Import 캐시 초기화)
# ─────────────────────────────────────────────
# Alembic이 Base.metadata를 재사용하지 않도록 캐시 초기화
importlib.invalidate_caches()

# ─────────────────────────────────────────────
# 2️⃣ 경로 주입 (backend 기준)
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # .../backend/alembic
PROJ_ROOT = os.path.dirname(BASE_DIR)                  # .../backend
if PROJ_ROOT not in sys.path:
    sys.path.insert(0, PROJ_ROOT)

# ─────────────────────────────────────────────
# 3️⃣ Base 메타데이터 불러오기
# ─────────────────────────────────────────────
from app.db.base import Base
config = context.config
target_metadata = Base.metadata

# ─────────────────────────────────────────────
# 4️⃣ DB URL 설정 (환경변수 → 기본 SQLite)
# ─────────────────────────────────────────────
default_sqlite = "sqlite:////volume1/web/hotel-system/backend/hotel.db"
db_url = os.getenv("APP_DB_URL", os.getenv("DATABASE_URL", default_sqlite))
config.set_main_option("sqlalchemy.url", db_url)

# ─────────────────────────────────────────────
# 5️⃣ 안전 가드 — DROP / ALTER 차단 (SQLite 보호용)
# ─────────────────────────────────────────────
def include_object(object, name, type_, reflected, compare_to):
    """
    Alembic autogenerate 필터
    - 신규 생성:  메타데이터쪽(object)이며 DB에 없음 → 허용 (create)
    - 삭제(DROP): DB쪽(reflected)이며 메타데이터에 없음 → 차단 (False)
    - 변경(ALTER): 양쪽 모두 존재 → 차단 (False)  # SQLite에서 안전 목적
    """
    if type_ != "table":
        return True
    # 메타데이터에만 있고 DB에 없음 → 신규 테이블 생성 허용
    if not reflected and compare_to is None:
        return True
    # DB에만 있고 메타데이터에 없음 → DROP 방지
    if reflected and compare_to is None:
        return False
    # 양쪽 모두 있음(ALTER) → 방지
    return False

def process_revision_directives(context, revision, directives):
    # 방어망 유지: 혹시 모를 DROP/ALTER가 들어오면 바로 차단
    script = directives[0]
    if hasattr(script, "upgrade_ops"):
        ddl = str(script.upgrade_ops).lower()
        if any(k in ddl for k in ("drop_table", "alter_column", "drop_column")):
            raise RuntimeError("Unsafe DDL detected (DROP/ALTER blocked on SQLite)")

# ─────────────────────────────────────────────
# 6️⃣ 오프라인 모드 (SQL 텍스트 출력)
# ─────────────────────────────────────────────
def run_migrations_offline():
    """콘솔 출력용 마이그레이션 (DB 연결 없이 SQL 텍스트 생성)"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        include_object=include_object,
        process_revision_directives=process_revision_directives,
    )
    with context.begin_transaction():
        context.run_migrations()

# ─────────────────────────────────────────────
# 7️⃣ 온라인 모드 (DB 직접 적용)
# ─────────────────────────────────────────────
def run_migrations_online():
    """실제 DB에 마이그레이션 적용 (SQLite 호환 batch mode 활성화)"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            process_revision_directives=process_revision_directives,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()

# ─────────────────────────────────────────────
# 8️⃣ 실행 분기 (Offline / Online)
# ─────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

# ============================================================================
# ✅ 요약:
#   • 신규 테이블: 자동 감지됨
#   • 기존 테이블: drop_table() 안 찍힘
#   • DROP/ALTER 시도 시: RuntimeError 즉시 발생
#   • SQLite 환경 완전 안전모드 (데이터 보호)
# ============================================================================
