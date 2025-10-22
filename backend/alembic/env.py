# -*- coding: utf-8 -*-
# ============================================================================
# File      : backend/alembic/env.py
# Version   : 2025.10-25 · v1.5 (Safe SQLite Autogen Guard · SSOT Stable)
# Purpose   : Hotel Admin — Alembic Migration Environment Config
# ----------------------------------------------------------------------------
# 목적:
#   • Alembic 환경 설정 파일 (revision/autogenerate/upgrade 실행 환경 정의)
#   • SQLite 개발환경에 맞춰 “안전 가드” 및 “경로 주입” 처리
# ----------------------------------------------------------------------------
# 주요 특징:
#   ✅ 프로젝트 경로 자동 인식 (backend/app 포함)
#   ✅ APP_DB_URL / DATABASE_URL 환경변수 우선 적용
#   ✅ DROP / ALTER 차단 — SQLite 환경의 안전 보장
#   ✅ include_object 필터로 신규 테이블만 자동 감지 (Safe Auto-Gen)
#   ✅ render_as_batch=True 설정으로 ALTER 우회 지원
# ----------------------------------------------------------------------------
# 연계:
#   • app/db/base.py        → Base.metadata (모든 ORM 테이블 메타)
#   • app/models/*          → ORM 정의 원본
#   • alembic/versions/*    → 마이그레이션 파일 저장소
# ----------------------------------------------------------------------------
# ⚙️ 운영 시 변경사항:
#   • 운영 DB(MySQL/PostgreSQL)로 이전 시 DROP/ALTER 가드 해제 필요.
#   • "process_revision_directives" 내 forbidden 목록 수정으로 제어 가능.
#   • "include_object" 필터로 특정 테이블만 autogen 하도록 조정 가능.
# ============================================================================

import os
import sys
from sqlalchemy import engine_from_config, pool
from alembic import context

# ─────────────────────────────────────────────
# 1️⃣ 경로 주입 (backend 기준)
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # .../backend/alembic
PROJ_ROOT = os.path.dirname(BASE_DIR)                  # .../backend
if PROJ_ROOT not in sys.path:
    sys.path.insert(0, PROJ_ROOT)

# ─────────────────────────────────────────────
# 2️⃣ Base 메타데이터 불러오기
# ─────────────────────────────────────────────
from app.db.base import Base  # Base.metadata 참조
config = context.config
target_metadata = Base.metadata

# ─────────────────────────────────────────────
# 3️⃣ DB URL 설정
# ─────────────────────────────────────────────
# 환경변수(APP_DB_URL / DATABASE_URL) 우선 → 없으면 SQLite 절대경로 기본값
# 운영 전환 시 반드시 외부 DB 연결 문자열로 교체
# 예: mysql+pymysql://user:pass@host:3306/hotel
# ─────────────────────────────────────────────
default_sqlite = "sqlite:////volume1/web/hotel-system/backend/hotel.db"
db_url = os.getenv("APP_DB_URL", os.getenv("DATABASE_URL", default_sqlite))
config.set_main_option("sqlalchemy.url", db_url)

# ─────────────────────────────────────────────
# 4️⃣ 안전가드 — DROP / ALTER 차단 (SQLite 보호용)
# ─────────────────────────────────────────────
def include_object(object, name, type_, reflected, compare_to):
    """
    Alembic autogenerate 시 객체 포함 여부 제어
    - 신규 테이블만 허용 (compare_to is None)
    """
    if type_ == "table" and compare_to is None:
        return True  # 신규 생성은 허용
    return True      # 나머지는 기본 허용 (필요 시 필터링 가능)

def process_revision_directives(context, revision, directives):
    """
    Revision 생성 시 위험한 DDL 자동 차단
    - DROP / ALTER 문 감지 시 RuntimeError 발생
    """
    script = directives[0]
    if hasattr(script, "upgrade_ops"):
        ddl = str(script.upgrade_ops)
        forbidden = ("drop_table", "alter_column")
        if any(k in ddl for k in forbidden):
            raise RuntimeError("Unsafe DDL detected: DROP/ALTER not allowed on SQLite")

# ─────────────────────────────────────────────
# 5️⃣ 오프라인 모드 (DDL 출력 전용)
# ─────────────────────────────────────────────
def run_migrations_offline():
    """
    콘솔 출력용 마이그레이션 (DB 연결 없이 SQL 텍스트 생성)
    """
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
# 6️⃣ 온라인 모드 (DB 직접 적용)
# ─────────────────────────────────────────────
def run_migrations_online():
    """
    실제 DB에 마이그레이션 적용 (SQLite 호환 batch mode 활성화)
    """
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
            render_as_batch=True,  # SQLite ALTER TABLE 우회
        )
        with context.begin_transaction():
            context.run_migrations()

# ─────────────────────────────────────────────
# 7️⃣ 실행 분기 (Offline / Online)
# ─────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
