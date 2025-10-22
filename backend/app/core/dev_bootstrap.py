# -*- coding: utf-8 -*-
# ============================================================================
# File      : app/core/dev_bootstrap.py
# Version   : 2025-10-31 · v3.6 (SSOT Stable)
# Purpose   : DEV 환경 부팅 시 DB 자동 보강 및 시드 데이터 생성
# ----------------------------------------------------------------------------
# 목적:
#   • 개발환경(DEV)에서만 실행되는 DB 초기화·보강 루틴
#   • 누락된 컬럼, 테이블 자동 생성 및 Role 기본값 삽입
#   • 운영환경(PROD)에서는 절대 실행되지 않음
# ----------------------------------------------------------------------------
# 특징:
#   ✅ Alembic 미적용 개발환경에서도 안전한 부팅 보장
#   ✅ SQLite 보강: uploaded_files, employees, roles, user_roles 등 자동 점검
#   ✅ SSOT 정책: version_no, is_active 컬럼 누락 시 자동 추가
# ----------------------------------------------------------------------------
# 사용 예:
#   from app.core.dev_bootstrap import register_startup_hooks
#   register_startup_hooks(app, engine, Base, is_dev=True)
# ============================================================================

import logging
from fastapi import FastAPI
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session

log = logging.getLogger(__name__)


def register_startup_hooks(app: FastAPI, engine, Base, is_dev: bool):
    """DEV 환경에서만 스타트업 보강 로직 등록"""
    if not is_dev:
        return

    @app.on_event("startup")
    def _dev_startup():
        insp = inspect(engine)
        log.info("[startup] DEV bootstrap 시작")

        # ─────────────────────────────────────────────
        # 1️⃣ 스키마 생성 (중복 안전)
        # ─────────────────────────────────────────────
        try:
            Base.metadata.create_all(bind=engine, checkfirst=True)
        except Exception as e:
            log.warning(f"[startup] Base.create_all 실패: {e}")

        # ─────────────────────────────────────────────
        # 2️⃣ uploaded_files 테이블 보강 (DEV + SQLite)
        # ─────────────────────────────────────────────
        try:
            from app.db.session import is_sqlite
            if is_sqlite():
                with engine.begin() as conn:
                    tables = {r[0] for r in conn.execute(text(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ))}
                    target_table = "uploaded_files" if "uploaded_files" in tables else "upload_files"
                    cols = {r[1] for r in conn.execute(text(f"PRAGMA table_info({target_table})"))}

                    def _add(col: str, ddl: str):
                        if col not in cols:
                            conn.execute(text(f"ALTER TABLE {target_table} ADD COLUMN {ddl}"))
                            log.info(f"[startup:migrate] {target_table} add {col}")

                    _add("part_key", "VARCHAR(120) DEFAULT ''")
                    _add("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                    _add("updated_at", "TIMESTAMP")
                    _add("is_active", "BOOLEAN DEFAULT 1")          # ✅ Soft-delete 보강
                    _add("version_no", "INTEGER DEFAULT 1")         # ✅ 버전 관리 보강
        except Exception as e:
            log.warning(f"[startup:migrate] uploaded_files 보강 실패: {e}")

        # ─────────────────────────────────────────────
        # 3️⃣ employees 스키마 보강 (DEV + SQLite)
        # ─────────────────────────────────────────────
        try:
            from app.db.session import is_sqlite
            if is_sqlite():
                with engine.begin() as conn:
                    from app.startup.helpers import _ensure_employees_schema
                    added = _ensure_employees_schema(conn)
                    if added:
                        log.info(f"[startup:migrate] employees 보강: {', '.join(added)}")
        except Exception as e:
            log.warning(f"[startup:migrate] employees 보강 실패: {e}")

        # ─────────────────────────────────────────────
        # 4️⃣ roles / user_roles 테이블 점검 (DEV + SQLite)
        # ─────────────────────────────────────────────
        try:
            from app.db.session import is_sqlite
            if is_sqlite():
                with engine.begin() as conn:
                    cols_roles = {r[1] for r in conn.execute(text("PRAGMA table_info(roles)"))}
                    if cols_roles and "id" not in cols_roles:
                        conn.execute(text("ALTER TABLE roles RENAME TO roles_bad_20251031"))
                        log.warning("[startup:migrate] renamed invalid 'roles' -> roles_bad_20251031")

                    cols_user_roles = {r[1] for r in conn.execute(text("PRAGMA table_info(user_roles)"))}
                    if cols_user_roles and not {"user_id", "role_id"} <= cols_user_roles:
                        conn.execute(text("ALTER TABLE user_roles RENAME TO user_roles_bad_20251031"))
                        log.warning("[startup:migrate] renamed invalid 'user_roles' -> user_roles_bad_20251031")
        except Exception as e:
            log.warning(f"[startup:migrate] roles/user_roles 점검 실패: {e}")

        # ─────────────────────────────────────────────
        # 5️⃣ 기본 Role 시드 데이터
        # ─────────────────────────────────────────────
        try:
            from app.models.role import Role
            with Session(bind=engine) as db:
                def ensure(code: str, name: str):
                    if not db.query(Role).filter(Role.code == code).first():
                        db.add(Role(code=code, name=name, is_active=True))
                        db.commit()
                        log.info(f"[startup:seed] Role '{code}' 추가됨")

                ensure("ADMIN", "Admin")
                ensure("SUPERADMIN", "Super Admin")
                ensure("HRADMIN", "HR Admin")
        except Exception as e:
            log.warning(f"[startup:migrate] roles 시드 실패: {e}")

        log.info("[startup] DEV bootstrap 완료 ✅")
