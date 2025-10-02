# -*- coding: utf-8 -*-
import os, sys
from sqlalchemy import engine_from_config, pool
from alembic import context

# 프로젝트 루트(backend) 경로 주입
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # .../backend/alembic
PROJ_ROOT = os.path.dirname(BASE_DIR)                  # .../backend
if PROJ_ROOT not in sys.path:
    sys.path.insert(0, PROJ_ROOT)

# 앱 Base 메타데이터
from app.db.base import Base  # Base.metadata 사용

config = context.config

# DB URL: ENV 우선, 없으면 절대경로 sqlite
default_sqlite = "sqlite:////volume1/web/hotel-system/backend/hotel.db"
db_url = os.getenv("APP_DB_URL", os.getenv("DATABASE_URL", default_sqlite))
config.set_main_option("sqlalchemy.url", db_url)

target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
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
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
