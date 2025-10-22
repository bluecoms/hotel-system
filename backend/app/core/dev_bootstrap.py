# app/core/dev_bootstrap.py
# -*- coding: utf-8 -*-
from fastapi import FastAPI
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session

def register_startup_hooks(app: FastAPI, engine, Base, is_dev: bool):
    """DEV 환경에서만 스타트업 보강 로직 등록"""
    if not is_dev:
        return

    @app.on_event("startup")
    def _dev_startup():
        insp = inspect(engine)

        # 1) (DEV) 스키마 1차 생성 (중복 안전)
        try:
            Base.metadata.create_all(bind=engine, checkfirst=True)
        except Exception as e:
            print("[startup] Base.create_all failed:", e)

        # 2) (DEV + SQLite) uploaded_files 보강
        try:
            from app.db.session import is_sqlite
            if is_sqlite():
                with engine.begin() as conn:
                    # uploaded_files 우선 확인
                    existing_tables = {r[0] for r in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))}
                    target_table = "uploaded_files" if "uploaded_files" in existing_tables else "upload_files"
                    cols = {r[1] for r in conn.execute(text(f"PRAGMA table_info({target_table})"))}

                    if "part_key" not in cols:
                        conn.execute(text(f"ALTER TABLE {target_table} ADD COLUMN part_key VARCHAR(120) DEFAULT ''"))
                        print(f"[startup:migrate] {target_table} add part_key")
                    if "created_at" not in cols:
                        conn.execute(text(f"ALTER TABLE {target_table} ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                        print(f"[startup:migrate] {target_table} add created_at")
                    if "updated_at" not in cols and "uploaded_files" in existing_tables:
                        # 안전하게만 추가 (nullable 허용)
                        conn.execute(text(f"ALTER TABLE {target_table} ADD COLUMN updated_at TIMESTAMP"))
                        print(f"[startup:migrate] {target_table} add updated_at")
        except Exception as e:
            if "already exists" in str(e) or "no such table" in str(e):
                print(f"[startup:migrate] skip uploaded_files patch ({e})")
            else:
                print("[startup:migrate] uploaded_files alter failed:", e)

        # 3) (DEV + SQLite) employees 보강
        try:
            from app.db.session import is_sqlite
            if is_sqlite():
                with engine.begin() as conn:
                    try:
                        from app.startup.helpers import _ensure_employees_schema
                        added = _ensure_employees_schema(conn)
                        if added:
                            print("[startup:migrate] employees added:", ", ".join(added))
                    except Exception:
                        pass
        except Exception as e:
            print("[startup:migrate] employees alter failed:", e)

        # 4) (DEV + SQLite) roles/user_roles 테이블 점검
        try:
            from app.db.session import is_sqlite
            if is_sqlite():
                with engine.begin() as conn:
                    cols_roles = {r[1] for r in conn.execute(text("PRAGMA table_info(roles)"))}
                    if cols_roles and "id" not in cols_roles:
                        conn.execute(text("ALTER TABLE roles RENAME TO roles_bad_20250928"))
                        print("[startup:migrate] renamed broken table 'roles' -> roles_bad_20250928")

                    cols_user_roles = {r[1] for r in conn.execute(text("PRAGMA table_info(user_roles)"))}
                    if cols_user_roles and not {"user_id", "role_id"} <= cols_user_roles:
                        conn.execute(text("ALTER TABLE user_roles RENAME TO user_roles_bad_20250928"))
                        print("[startup:migrate] renamed broken table 'user_roles' -> user_roles_bad_20250928")
        except Exception as e:
            print("[startup:migrate] roles/user_roles check failed:", e)

        # 5) (DEV) Role 시드
        try:
            from app.models.role import Role
            with Session(bind=engine) as db:
                def ensure(code: str, name: str):
                    if not db.query(Role).filter(Role.code == code).first():
                        db.add(Role(code=code, name=name, is_active=True))
                        db.commit()
                ensure("ADMIN", "Admin")
                ensure("SUPERADMIN", "Super Admin")
        except Exception as e:
            print("[startup:migrate] roles seed failed:", e)
