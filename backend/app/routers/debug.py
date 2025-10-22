# app/routers/debug.py
# -*- coding: utf-8 -*-
from typing import Optional, Set, Dict, Any
from fastapi import APIRouter, Header
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.core.settings import settings
from app.db import engine as _engine

router = APIRouter(prefix="/api/_debug", tags=["_debug"])

def _table_cols(engine: Engine, name: str) -> Set[str]:
    try:
        with engine.begin() as conn:
            rows = conn.execute(text(f"PRAGMA table_info({name})")).fetchall()
            return {r[1] for r in rows}
    except Exception:
        return set()

@router.get("/dburl")
def dbg_dburl():
    return {"url": str(_engine.url)}

@router.get("/columns")
def dbg_columns():
    with _engine.begin() as conn:
        return {
            "employees": sorted(list(_table_cols(_engine, "employees"))),
            "roles": sorted(list(_table_cols(_engine, "roles"))),
            "user_roles": sorted(list(_table_cols(_engine, "user_roles"))),
            "upload_files": sorted(list(_table_cols(_engine, "upload_files"))),
        }

@router.get("/token")
def dbg_token():
    v = settings.INTERNAL_API_TOKEN or ""
    return {"token_prefix": v[:4], "len": len(v)}

@router.get("/echo")
def dbg_echo(
    x_internal_token: Optional[str] = Header(None),
    x_internal_token_alt: Optional[str] = Header(None, alias="x-internal-token"),
):
    return {"recv_header": x_internal_token or x_internal_token_alt}
